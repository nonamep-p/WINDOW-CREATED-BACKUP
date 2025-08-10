import discord
from discord.ext import commands
from discord import app_commands

from utils.helpers import create_embed, format_number

# Import interactive sub-views from other cogs
from cogs.dungeon import DungeonView
from cogs.quests import DailyQuestsView as DailyView
from cogs.guild_interactive import GuildInteractiveView

class PlayView(discord.ui.View):
    def __init__(self, bot, user_id: int, timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This panel belongs to someone else.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.primary, emoji="👤")
    async def profile_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        char = await self.bot.character_system.get_character(self.user_id)
        if not char:
            embed = create_embed(title="👤 Profile", description="No character found. Use the Create button below.", color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=self)
            return
        stats = self.bot.character_system.format_character_display(char)
        hp_bar = self._bar(stats["stats"].get("hp", 0), stats["stats"].get("max_hp", 1))
        sp_bar = self._bar(stats["stats"].get("sp", 0), stats["stats"].get("max_sp", 1))
        embed = create_embed(
            title=f"👤 {stats['username']} — L{stats['level']}",
            description=f"Gold: {format_number(stats['gold'])} | XP: {format_number(stats['xp'])}",
            color=discord.Color.blurple(),
            fields=[
                {"name": "HP", "value": f"{hp_bar} ({stats['stats'].get('hp',0)}/{stats['stats'].get('max_hp',0)})", "inline": True},
                {"name": "SP", "value": f"{sp_bar} ({stats['stats'].get('sp',0)}/{stats['stats'].get('max_sp',0)})", "inline": True},
                {"name": "Combat", "value": f"W/L: {char.get('battles_won',0)}/{char.get('battles_lost',0)} | Dungeons: {char.get('dungeons_completed',0)}", "inline": True},
            ],
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Hunt", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def hunt_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = self.user_id
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            await interaction.response.send_message("Create a character first.", ephemeral=True)
            return
        monsters_data = await self.bot.db.load_monsters()
        if not monsters_data:
            await interaction.response.send_message("No monsters available.", ephemeral=True)
            return
        import random
        monster = monsters_data[random.choice(list(monsters_data.keys()))]
        result = await self.bot.combat_system.start_battle(user_id, monster)
        if not result["success"]:
            await interaction.response.send_message(result.get("message", "Cannot start battle."), ephemeral=True)
            return
        battle = result["battle"]
        embed_data = self.bot.combat_system.get_battle_embed(battle)
        embed = create_embed(**embed_data)
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Dungeon", style=discord.ButtonStyle.success, emoji="🏰")
    async def dungeon_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = self.user_id
        char = await self.bot.character_system.get_character(user_id)
        if not char:
            await interaction.response.send_message("Create a character first.", ephemeral=True)
            return
        dungeon_id = "forest"
        dungeon = await self.bot.db.get_dungeon(dungeon_id)
        if not dungeon:
            await interaction.response.send_message("Dungeon not found.", ephemeral=True)
            return
        session = await self.bot.dungeon_system.start_dungeon(user_id, dungeon_id)
        floors_obj = dungeon.get("floors")
        floor_count = len(floors_obj.keys()) if isinstance(floors_obj, dict) else dungeon.get("floors", 0)
        desc = dungeon.get("description") or (floors_obj.get("1", {}).get("env", {}).get("name", "") if isinstance(floors_obj, dict) else "")
        embed = create_embed(
            title=f"🏰 Entering {dungeon['name']}",
            description=desc,
            color=discord.Color.purple(),
            fields=[{"name": "Floors", "value": str(floor_count), "inline": True}],
        )
        await interaction.response.edit_message(embed=embed, view=DungeonView(self.bot, user_id))

    @discord.ui.button(label="Quests", style=discord.ButtonStyle.secondary, emoji="🧭")
    async def quests_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = self.user_id
        await self.bot.daily_quest_system.get_daily(user_id)
        dv = DailyView(self.bot, user_id)
        await interaction.response.edit_message(embed=create_embed(title="🧭 Daily Quests", description="Loading...", color=discord.Color.blurple()), view=dv)
        await dv._refresh(interaction)

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.secondary, emoji="🏪")
    async def shop_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = self.user_id
        character = await self.bot.character_system.get_character(user_id)
        shop_items = await self.bot.economy_system.get_shop_items()
        if not shop_items:
            await interaction.response.send_message("Shop is empty.", ephemeral=True)
            return
        desc = "\n".join([f"• {it['name']} — {it.get('price', it.get('value', 0))}g" for it in shop_items[:10]])
        embed = create_embed(title="🏪 Shop", description=desc, color=discord.Color.gold(), footer=f"Your Gold: {character.get('gold',0)}")
        await interaction.response.edit_message(embed=embed, view=None) # Removed ShopView(self.bot, user_id, shop_items)

    @discord.ui.button(label="Faction", style=discord.ButtonStyle.secondary, emoji="🏳️")
    async def faction_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = self.user_id
        embed = create_embed(title="🏳️ Factions", description="Use /guild to open the interactive faction panel.", color=discord.Color.blue())
        # Provide a small inline view with a button to trigger /guild
        v = discord.ui.View(timeout=60)
        open_btn = discord.ui.Button(label="Open Guild Panel", style=discord.ButtonStyle.primary, emoji="🏰")
        async def open_cb(i: discord.Interaction):
            if i.user.id != self.user_id:
                return await i.response.send_message("Not for you", ephemeral=True)
            try:
                await i.response.defer()
            except Exception:
                pass
            # Build guild embed directly
            character = await self.bot.character_system.get_character(self.user_id)
            cog = self.bot.get_cog("GuildInteractiveCog")
            embed = cog._create_guild_embed(character) if cog else create_embed(title="Guild", description="Unavailable", color=discord.Color.red())
            v2 = GuildInteractiveView(self.bot, self.user_id, in_faction=bool(character.get("faction"))) if cog else None
            await i.followup.send(embed=embed, view=v2, ephemeral=False)
        open_btn.callback = open_cb
        v.add_item(open_btn)
        await interaction.response.edit_message(embed=embed, view=v)

    def _bar(self, current: int, maximum: int) -> str:
        if maximum <= 0:
            return "██████████"
        filled = int((current / maximum) * 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

class PlayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="Access the main game control panel")
    async def play(self, interaction: discord.Interaction):
        """Main game control panel"""
        user_id = interaction.user.id
        character = await self.bot.character_system.get_character(user_id)
        
        if not character:
            embed = create_embed(
                title="👋 Welcome, Adventurer!",
                description="It looks like you haven't created a character yet. Let's get you set up!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Start Your Journey", value="Use `/character create` to begin!", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        level = character.get("level", 1)
        gold = character.get("gold", 0)
        xp = character.get("xp", 0)
        hp = character.get("hp", 100)
        max_hp = character.get("max_hp", 100)

        embed = create_embed(
            title=f"🎮 {character['username']}'s Adventure Hub",
            description=f"**Level {level}** {character.get('class', 'Adventurer')}\n**Gold:** {format_number(gold)} | **XP:** {format_number(xp)}\n**HP:** {hp}/{max_hp}",
            color=discord.Color.blue()
        )

        embed.add_field(name="⚔️ Combat & Adventure", value="Hunt monsters, explore dungeons, and battle other players", inline=True)
        embed.add_field(name="💰 Economy & Trading", value="Shop for items, manage inventory, and craft equipment", inline=True)
        embed.add_field(name="🏰 Social & Guilds", value="Join guilds, form parties, and compete with others", inline=True)
        embed.add_field(name="🎯 Character & Skills", value="Manage your character, skills, and achievements", inline=True)
        embed.add_field(name="📚 Learning & Help", value="Tutorials, guides, and comprehensive help system", inline=True)
        embed.add_field(name="⚙️ Settings & Tools", value="Admin tools and bot settings", inline=True)

        embed.set_footer(text="Select a category below to access features!")

        view = PlayMainView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

class NewPlayerView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🎯 Create Character", style=discord.ButtonStyle.success, emoji="🎯")
    async def create_character(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Redirect to character creation
        character_cog = self.bot.get_cog("CharacterCog")
        if character_cog:
            await character_cog.character_create(interaction)
        else:
            embed = create_embed(
                title="❌ Character System Unavailable",
                description="The character system is currently unavailable. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📚 Tutorial", style=discord.ButtonStyle.primary, emoji="📚")
    async def start_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Redirect to tutorial
        tutorial_cog = self.bot.get_cog("TutorialCog")
        if tutorial_cog:
            await tutorial_cog._tutorial_start(interaction)
        else:
            embed = create_embed(
                title="❌ Tutorial Unavailable",
                description="The tutorial system is currently unavailable. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, emoji="❓")
    async def get_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Redirect to help
        help_cog = self.bot.get_cog("HelpCog")
        if help_cog:
            await help_cog.help_command(interaction)
        else:
            embed = create_embed(
                title="❓ Need Help?",
                description="Use `/help` to access the comprehensive help system!",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class PlayMainView(discord.ui.View):
    def __init__(self, bot, user_id: int, character: dict):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.character = character

    @discord.ui.button(label="⚔️ Combat", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def combat_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="⚔️ Combat & Adventure",
            description="Choose your adventure type:",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🎯 Hunt Monsters",
            value="`/hunt` - Fight wild monsters for XP and loot",
            inline=False
        )
        
        embed.add_field(
            name="�� Explore Dungeons",
            value="`/dungeon` - Venture into dangerous dungeons",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Arena",
            value="`/pvp @user` - Challenge other players\n`/arena` - Enter ranked battles",
            inline=False
        )
        
        embed.add_field(
            name="📜 Quests",
            value="`/quests` - Take on epic adventures",
            inline=False
        )
        
        # Direct command suggestions instead of broken view
        embed.add_field(
            name="🎮 Quick Actions",
            value="`/hunt` - Start hunting\n`/dungeon` - Enter dungeon\n`/arena` - PvP battles",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="💰 Economy", style=discord.ButtonStyle.success, emoji="💰")
    async def economy_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="💰 Economy & Trading",
            description="Manage your wealth and items:",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🛒 Shopping",
            value="`/shop` - Browse and buy items\n`/daily` - Claim daily rewards",
            inline=False
        )
        
        embed.add_field(
            name="📦 Inventory",
            value="`/inventory` - Manage your items\n`/equipment` - View equipped gear",
            inline=False
        )
        
        embed.add_field(
            name="🔨 Crafting",
            value="`/craft` - Create powerful items",
            inline=False
        )
        
        # Direct command suggestions instead of broken view
        embed.add_field(
            name="🎮 Quick Actions", 
            value="`/shop` - Browse shop\n`/inventory` - View items\n`/craft` - Start crafting",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🏰 Social", style=discord.ButtonStyle.primary, emoji="🏰")
    async def social_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🏰 Social & Guilds",
            description="Connect with other players:",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🏰 Guild System",
            value="`/guild` - Join or manage your guild",
            inline=False
        )
        
        embed.add_field(
            name="👥 Party System",
            value="`/party` - Form temporary groups",
            inline=False
        )
        
        embed.add_field(
            name="📊 Leaderboards",
            value="`/leaderboard` - See top players\n`/profile @user` - View player profiles",
            inline=False
        )
        
        view = GuildInteractiveView(self.bot, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PlayCog(bot))
