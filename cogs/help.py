import discord
from discord.ext import commands
from discord import app_commands
from utils.helpers import create_embed
import logging

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Get help with bot commands and features")
    async def help_command(self, interaction: discord.Interaction):
        """Interactive help system"""
        embed = create_embed(
            title="🎮 RPG Bot Help Center",
            description="Welcome to the comprehensive help system! Select a category to explore:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📚 Quick Start",
            value="New to the bot? Start here for the basics!",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Combat & Skills",
            value="Learn about battles, skills, and equipment",
            inline=True
        )
        
        embed.add_field(
            name="🏰 Guilds & Social",
            value="Guild management, parties, and PvP",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economy & Trading",
            value="Gold, shop, crafting, and marketplace",
            inline=True
        )
        
        embed.add_field(
            name="🗺️ Exploration",
            value="Dungeons, quests, and adventures",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Character & Progression",
            value="Levels, skills, achievements, and profiles",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Settings & Admin",
            value="Bot settings and admin commands",
            inline=True
        )
        
        view = HelpMainView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)

class HelpMainView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300.0)
        self.bot = bot

    @discord.ui.button(label="📚 Quick Start", style=discord.ButtonStyle.primary, emoji="📚")
    async def quick_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="📚 Quick Start Guide",
            description="Welcome to the RPG Bot! Here's how to get started:",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="1️⃣ Create Your Character",
            value="`/character create` - Choose your race and class\n`/character` - View your character stats",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ Start Playing",
            value="`/play` - Access the main game menu\n`/hunt` - Start your first battle\n`/daily` - Claim daily rewards",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ Explore Features",
            value="`/shop` - Buy items and equipment\n`/inventory` - Manage your items\n`/dungeon` - Explore dungeons",
            inline=False
        )
        
        embed.add_field(
            name="4️⃣ Social Features",
            value="`/guild` - Join or create a guild\n`/party` - Form parties with friends\n`/pvp` - Challenge other players",
            inline=False
        )
        
        embed.add_field(
            name="💡 Pro Tips",
            value="• Use `/tutorial start` for an interactive guide\n• Check `/profile` to track your progress\n• Visit `/craft` to create powerful items",
            inline=False
        )
        
        view = HelpNavigationView(self.bot, "main")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="⚔️ Combat", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def combat_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="⚔️ Combat & Skills Guide",
            description="Master the art of battle!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🎯 Combat Commands",
            value="`/hunt` - Start a PvE battle\n`/pvp @user` - Challenge another player\n`/arena` - Enter the PvP arena",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Combat Actions",
            value="**⚔️ Attack** - Basic attack\n**🛡️ Defend** - Reduce damage, gain SP\n**🎯 Skills** - Use special abilities\n**🧪 Items** - Consume potions/scrolls\n**🔥 Ultimate** - Powerful special move",
            inline=False
        )
        
        embed.add_field(
            name="🎪 Skills System",
            value="• Learn skills by leveling up\n• Skills cost SP (Skill Points)\n• Skills have cooldowns\n• Combo attacks for bonus damage",
            inline=False
        )
        
        embed.add_field(
            name="🎒 Equipment",
            value="`/equipment` - View/change gear\n`/equip <item>` - Equip an item\n**Weapon** - Increases attack\n**Armor** - Increases defense\n**Accessory** - Various bonuses",
            inline=False
        )
        
        view = HelpNavigationView(self.bot, "main")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🏰 Social", style=discord.ButtonStyle.secondary, emoji="🏰")
    async def social_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="🏰 Guilds & Social Features",
            description="Team up with other players!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🏰 Guild System",
            value="`/guild` - Interactive guild management\n• Create or join guilds\n• Guild ranks: Owner > Officer > Member\n• Guild bonuses and shared resources",
            inline=False
        )
        
        embed.add_field(
            name="👥 Party System",
            value="`/party` - Form temporary groups\n• Team up for dungeons\n• Share rewards\n• Cooperative combat",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ PvP Features",
            value="`/pvp @user` - Challenge players\n`/arena` - Ranked battles\n• Climb the leaderboards\n• Earn PvP rewards",
            inline=False
        )
        
        embed.add_field(
            name="📊 Social Commands",
            value="`/profile @user` - View player profiles\n`/leaderboard` - See top players\n`/achievements` - Track accomplishments",
            inline=False
        )
        
        view = HelpNavigationView(self.bot, "main")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="💰 Economy", style=discord.ButtonStyle.success, emoji="💰")
    async def economy_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="💰 Economy & Trading Guide",
            description="Master the art of wealth!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💰 Currency System",
            value="**Gold** - Main currency for purchases\n**XP** - Experience points for leveling\n**Reputation** - Social standing",
            inline=False
        )
        
        embed.add_field(
            name="🛒 Shopping",
            value="`/shop` - Browse items to buy\n`/daily` - Claim daily rewards\n• Weapons, armor, consumables\n• Dynamic pricing system",
            inline=False
        )
        
        embed.add_field(
            name="🔨 Crafting System",
            value="`/craft` - Interactive crafting hub\n• Learn crafting skills\n• Gather materials\n• Create powerful items\n• Upgrade equipment",
            inline=False
        )
        
        embed.add_field(
            name="📦 Trading",
            value="`/inventory` - Manage your items\n• Trade with other players\n• Auction house (coming soon)\n• Market listings",
            inline=False
        )
        
        view = HelpNavigationView(self.bot, "main")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🗺️ Exploration", style=discord.ButtonStyle.primary, emoji="🗺️")
    async def exploration_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="🗺️ Exploration & Adventures",
            description="Discover the world!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🏰 Dungeons",
            value="`/dungeon` - Enter mysterious dungeons\n• Multiple floors to explore\n• Boss battles and treasures\n• Risk vs reward mechanics",
            inline=False
        )
        
        embed.add_field(
            name="📜 Quests",
            value="`/quests` - View available quests\n• Story-driven adventures\n• Daily and weekly quests\n• Epic quest chains",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Loot & Rewards",
            value="• Random item drops\n• Rare equipment finds\n• Achievement unlocks\n• Experience and gold",
            inline=False
        )
        
        embed.add_field(
            name="🐾 Pets & Companions",
            value="`/pets` - Manage your companions\n• Collect different pets\n• Pet battles and training\n• Companion bonuses",
            inline=False
        )
        
        view = HelpNavigationView(self.bot, "main")
        await interaction.response.edit_message(embed=embed, view=view)

class HelpNavigationView(discord.ui.View):
    def __init__(self, bot, return_to="main"):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.return_to = return_to

    @discord.ui.button(label="🏠 Main Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="🎮 RPG Bot Help Center",
            description="Welcome to the comprehensive help system! Select a category to explore:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📚 Quick Start", value="New to the bot? Start here for the basics!", inline=False)
        embed.add_field(name="⚔️ Combat & Skills", value="Learn about battles, skills, and equipment", inline=True)
        embed.add_field(name="🏰 Guilds & Social", value="Guild management, parties, and PvP", inline=True)
        embed.add_field(name="💰 Economy & Trading", value="Gold, shop, crafting, and marketplace", inline=True)
        embed.add_field(name="🗺️ Exploration", value="Dungeons, quests, and adventures", inline=True)
        embed.add_field(name="🎯 Character & Progression", value="Levels, skills, achievements, and profiles", inline=True)
        embed.add_field(name="⚙️ Settings & Admin", value="Bot settings and admin commands", inline=True)
        
        view = HelpMainView(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📋 Command List", style=discord.ButtonStyle.primary, emoji="📋")
    async def command_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="📋 Complete Command List",
            description="All available commands organized by category:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👤 Character",
            value="`/character` `/character create` `/profile` `/equipment` `/equip`",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Combat",
            value="`/hunt` `/pvp` `/arena` `/challenge`",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy",
            value="`/shop` `/daily` `/inventory` `/craft`",
            inline=False
        )
        
        embed.add_field(
            name="🏰 Social",
            value="`/guild` `/party` `/leaderboard` `/achievements`",
            inline=False
        )
        
        embed.add_field(
            name="🗺️ Adventure",
            value="`/dungeon` `/quests` `/pets` `/lootbox`",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Utility",
            value="`/play` `/help` `/tutorial` `/admin_panel`",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
