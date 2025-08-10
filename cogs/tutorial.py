import discord
from discord.ext import commands
from discord import app_commands
from utils.helpers import create_embed
import logging

logger = logging.getLogger(__name__)

class TutorialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="tutorial", description="Interactive tutorial to learn the game")
    @app_commands.describe(action="Tutorial action")
    @app_commands.choices(action=[
            app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="basics", value="basics"),
        app_commands.Choice(name="combat", value="combat"),
        app_commands.Choice(name="economy", value="economy"),
        app_commands.Choice(name="social", value="social"),
        app_commands.Choice(name="advanced", value="advanced")
    ])
    async def tutorial(self, interaction: discord.Interaction, action: str = "start"):
        """Interactive tutorial system"""
        if action == "start":
            await self._tutorial_start(interaction)
        elif action == "basics":
            await self._tutorial_basics(interaction)
        elif action == "combat":
            await self._tutorial_combat(interaction)
        elif action == "economy":
            await self._tutorial_economy(interaction)
        elif action == "social":
            await self._tutorial_social(interaction)
        elif action == "advanced":
            await self._tutorial_advanced(interaction)

    async def _tutorial_start(self, interaction: discord.Interaction):
        """Main tutorial welcome screen"""
        embed = create_embed(
            title="🎓 Welcome to RPG Bot Tutorial!",
            description="Learn everything you need to know to become a legendary adventurer!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎮 What You'll Learn",
            value="• Character creation and management\n• Combat system and strategies\n• Economy and trading\n• Social features and guilds\n• Advanced gameplay mechanics",
            inline=False
        )
        
        embed.add_field(
            name="📚 Tutorial Sections",
            value="Select a section below to start learning!",
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: You can return to this menu anytime with /tutorial start")
        
        view = TutorialMainView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def _tutorial_basics(self, interaction: discord.Interaction):
        """Basic gameplay tutorial"""
        embed = create_embed(
            title="📚 Basics Tutorial",
            description="Master the fundamentals of the game!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="1️⃣ Create Your Character",
            value="Use `/character create` to begin your adventure!\nChoose your race and class wisely - they affect your stats and abilities.",
            inline=False
        )
        
        embed.add_field(
            name="2️⃣ Check Your Stats",
            value="Use `/character` to view your current stats, level, and equipment.\nYour HP, SP, Attack, and Defense are crucial for survival!",
            inline=False
        )
        
        embed.add_field(
            name="3️⃣ Main Game Menu",
            value="Use `/play` to access the main game menu.\nThis gives you quick access to all major features!",
            inline=False
        )
        
        embed.add_field(
            name="4️⃣ Daily Rewards",
            value="Don't forget to use `/daily` every day!\nDaily rewards help you progress faster with gold and items.",
            inline=False
        )
        
        embed.add_field(
            name="5️⃣ Get Help",
            value="Use `/help` anytime for detailed information about commands and features.",
            inline=False
        )
        
        view = TutorialNavigationView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def _tutorial_combat(self, interaction: discord.Interaction):
        """Combat tutorial"""
        embed = create_embed(
            title="⚔️ Combat Tutorial",
            description="Learn to fight and survive in battle!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🎯 Starting Combat",
            value="`/hunt` - Fight monsters for XP and loot\n`/pvp @user` - Challenge other players\n`/arena` - Enter ranked PvP battles",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Combat Actions",
            value="**⚔️ Attack** - Deal damage to your opponent\n**🛡️ Defend** - Reduce incoming damage and gain SP\n**🎯 Skills** - Use special abilities (costs SP)\n**🧪 Items** - Use potions and consumables\n**🔥 Ultimate** - Powerful special attack when charged",
            inline=False
        )
        
        embed.add_field(
            name="🎪 Combat Strategy",
            value="• Use **Defend** to build up SP for skills\n• Skills have cooldowns - use them wisely\n• Items can turn the tide of battle\n• Watch your HP and use healing items\n• Ultimate abilities charge as you fight",
            inline=False
        )
        
        embed.add_field(
            name="🎒 Equipment Matters",
            value="• Better weapons increase your attack\n• Armor reduces damage taken\n• Accessories provide special bonuses\n• Use `/equipment` to manage your gear",
            inline=False
        )
        
        view = TutorialNavigationView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def _tutorial_economy(self, interaction: discord.Interaction):
        """Economy tutorial"""
        embed = create_embed(
            title="💰 Economy Tutorial",
            description="Master wealth and trading!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💰 Earning Gold",
            value="• Win battles (`/hunt`, `/pvp`)\n• Complete daily rewards (`/daily`)\n• Sell items from your inventory\n• Complete quests and achievements",
            inline=False
        )
        
        embed.add_field(
            name="🛒 Shopping",
            value="`/shop` - Browse and buy items\n• Weapons and armor for combat\n• Consumables for healing and buffs\n• Materials for crafting\n• Premium items for advanced players",
            inline=False
        )
        
        embed.add_field(
            name="🔨 Crafting System",
            value="`/craft` - Create powerful items\n• Learn crafting skills\n• Gather materials from battles\n• Craft better equipment than you can buy\n• Sell crafted items for profit",
            inline=False
        )
        
        embed.add_field(
            name="📦 Inventory Management",
            value="`/inventory` - Manage your items\n• Organize by categories\n• Equip weapons and armor\n• Use consumables for healing\n• Sell unwanted items for gold",
            inline=False
        )
        
        view = TutorialNavigationView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def _tutorial_social(self, interaction: discord.Interaction):
        """Social features tutorial"""
        embed = create_embed(
            title="🏰 Social Tutorial",
            description="Connect with other players!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🏰 Guild System",
            value="`/guild` - Join or create a guild\n• Team up with other players\n• Share resources and strategies\n• Guild bonuses and perks\n• Participate in guild events",
            inline=False
        )
        
        embed.add_field(
            name="👥 Party System",
            value="`/party` - Form temporary groups\n• Team up for difficult content\n• Share experience and rewards\n• Coordinate strategies\n• Help newer players",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Competition",
            value="`/leaderboard` - See top players\n`/pvp` - Challenge others to duels\n`/arena` - Ranked competitive battles\n• Climb the rankings\n• Earn prestigious rewards",
            inline=False
        )
        
        embed.add_field(
            name="📊 Profiles & Achievements",
            value="`/profile` - View player profiles\n• Track your progress and achievements\n• Show off your accomplishments\n• Compare stats with friends\n• Unlock special titles and rewards",
            inline=False
        )
        
        view = TutorialNavigationView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def _tutorial_advanced(self, interaction: discord.Interaction):
        """Advanced features tutorial"""
        embed = create_embed(
            title="🎯 Advanced Tutorial",
            description="Master advanced gameplay mechanics!",
            color=discord.Color.dark_purple()
        )
        
        embed.add_field(
            name="🏰 Dungeon Exploration",
            value="`/dungeon` - Explore dangerous dungeons\n• Multiple floors with increasing difficulty\n• Boss battles with unique mechanics\n• Rare loot and special rewards\n• Risk vs reward gameplay",
            inline=False
        )
        
        embed.add_field(
            name="📜 Quest System",
            value="`/quests` - Take on epic adventures\n• Story-driven content\n• Daily and weekly challenges\n• Chain quests with continuing stories\n• Unique rewards and achievements",
            inline=False
        )
        
        embed.add_field(
            name="🐾 Pets & Companions",
            value="`/pets` - Collect and train companions\n• Pet battles and training\n• Companion bonuses in combat\n• Rare and legendary pets\n• Pet evolution and growth",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Special Features",
            value="`/lootbox` - Open mystery boxes\n• Random rewards and surprises\n• Seasonal events and content\n• Limited-time offers\n• Community challenges",
            inline=False
        )
        
        embed.add_field(
            name="💡 Pro Tips",
            value="• Plan your character build carefully\n• Save gold for important upgrades\n• Join an active guild for support\n• Participate in events for exclusive rewards\n• Help new players to build the community",
            inline=False
        )
        
        view = TutorialNavigationView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

class TutorialMainView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📚 Basics", style=discord.ButtonStyle.primary, emoji="📚")
    async def basics_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_basics(interaction)

    @discord.ui.button(label="⚔️ Combat", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def combat_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_combat(interaction)

    @discord.ui.button(label="💰 Economy", style=discord.ButtonStyle.success, emoji="💰")
    async def economy_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_economy(interaction)

    @discord.ui.button(label="🏰 Social", style=discord.ButtonStyle.secondary, emoji="🏰")
    async def social_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_social(interaction)

    @discord.ui.button(label="🎯 Advanced", style=discord.ButtonStyle.primary, emoji="🎯")
    async def advanced_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_advanced(interaction)

class TutorialNavigationView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🏠 Tutorial Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def back_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("TutorialCog")
        await cog._tutorial_start(interaction)

    @discord.ui.button(label="🎮 Start Playing", style=discord.ButtonStyle.success, emoji="🎮")
    async def start_playing(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="🎮 Ready to Play!",
            description="Great! You're ready to start your adventure. Here are your next steps:",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🚀 Quick Start Commands",
            value="`/character create` - Create your character\n`/play` - Access the main menu\n`/hunt` - Start your first battle\n`/daily` - Claim daily rewards",
            inline=False
        )
        
        embed.add_field(
            name="💡 Remember",
            value="• Use `/help` if you need assistance\n• Join a guild for support and friendship\n• Have fun and be respectful to other players!",
            inline=False
        )
        
        embed.set_footer(text="Welcome to the adventure! 🌟")
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❓ Get Help", style=discord.ButtonStyle.primary, emoji="❓")
    async def get_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Redirect to help system
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

async def setup(bot):
    await bot.add_cog(TutorialCog(bot))
