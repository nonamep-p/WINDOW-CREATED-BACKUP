import asyncio
import logging
import sys
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands

from config import settings
from systems.database import DatabaseManager
from systems.combat import CombatSystem
from systems.character import CharacterSystem
from systems.inventory import InventorySystem
from systems.dungeon import DungeonSystem
from systems.economy import EconomySystem
from systems.tutorial import TutorialSystem
from utils.helpers import setup_logging, create_embed
from utils.rate_limiter import RateLimiter

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class RPGBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=settings.BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        
        # Initialize systems
        self.db = DatabaseManager()
        self.rate_limiter = RateLimiter()
        # Create core systems first
        self.inventory_system = InventorySystem(self.db)
        self.character_system = CharacterSystem(self.db, self.inventory_system)
        self.dungeon_system = DungeonSystem(self.db)
        self.economy_system = EconomySystem(self.db)
        self.tutorial_system = TutorialSystem(self.db)
        # Now combat can depend on character/inventory systems
        self.combat_system = CombatSystem(self.db, self.character_system, self.inventory_system)
        # Advanced combat system
        from systems.advanced_combat import AdvancedCombatSystem
        self.advanced_combat_system = AdvancedCombatSystem(self.db, self.character_system, self.inventory_system)
        # Guild system
        from systems.guild import GuildSystem
        self.guild_system = GuildSystem(self.db, self.character_system, self.economy_system)
        # Faction system
        from systems.factions import FactionSystem
        self.faction_system = FactionSystem(self.db, self.character_system)
        # Party system
        from systems.party import PartySystem
        self.party_system = PartySystem(self.db, self.character_system, self.combat_system)
        # Profile system
        from systems.profiles import ProfileSystem
        self.profile_system = ProfileSystem(self.db, self.character_system)
        # PvP Arena system
        from systems.pvp import PvPSystem
        self.pvp_system = PvPSystem(self.db, self.character_system, self.combat_system)
        # Pet system
        from systems.pets import PetSystem
        self.pet_system = PetSystem(self.db, self.character_system)
        # Quest system
        from systems.quests import QuestSystem
        self.quest_system = QuestSystem(self.db, self.character_system, self.inventory_system)
        # Crafting & Trading system
        from systems.crafting_trading import CraftingTradingSystem
        self.crafting_system = CraftingTradingSystem(self.db, self.character_system, self.inventory_system)
        # Daily quests system
        # Quest system already initialized above
        # self.daily_quest_system = DailyQuestSystem(self.db, self.character_system, self.dungeon_system)  # Removed
        # Effort-based reward system
        from systems.rewards import EffortBasedRewardSystem
        self.reward_system = EffortBasedRewardSystem(self.db, self.character_system, self.inventory_system)
        # Team coordination system
        from systems.team_coordination import TeamCoordinationSystem
        self.team_coordination_system = TeamCoordinationSystem(self.db)
        
    async def on_error(self, event: str, *args, **kwargs):
        """Enhanced error handler for runtime errors"""
        import traceback
        import sys
        
        error_info = sys.exc_info()
        if error_info[0] is None:
            return
            
        error_type = error_info[0].__name__
        error_message = str(error_info[1])
        tb = traceback.extract_tb(error_info[2])
        
        print(f"\n🚨 RUNTIME ERROR DETECTED")
        print(f"🎯 Event: {event}")
        print(f"❌ Error Type: {error_type}")
        print(f"💬 Message: {error_message}")
        
        if tb:
            last_frame = tb[-1]
            print(f"📁 File: {last_frame.filename}")
            print(f"📍 Line {last_frame.lineno}: {last_frame.line}")
            
            print(f"\n📋 CALL STACK:")
            for i, frame in enumerate(tb[-3:]):  # Show last 3 frames
                print(f"  {i+1}. {frame.filename}:{frame.lineno} in {frame.name}")
                if frame.line:
                    print(f"     → {frame.line.strip()}")
        
        print(f"\n💡 RUNTIME ERROR TIPS:")
        print(f"   • Check the line mentioned above for issues")
        print(f"   • Verify all variables are properly initialized")
        print(f"   • Look for None values or missing data")
        print(f"   • Check Discord API rate limits and permissions")
        print("="*80)
        
        logger.error(f"Runtime error in {event}: {error_type} - {error_message}")

    async def on_command_error(self, ctx, error):
        """Enhanced command error handler"""
        import traceback
        
        error_type = type(error).__name__
        error_message = str(error)
        
        print(f"\n⚠️  COMMAND ERROR")
        print(f"🎯 Command: {ctx.command.name if ctx.command else 'Unknown'}")
        print(f"👤 User: {ctx.author} ({ctx.author.id})")
        print(f"❌ Error Type: {error_type}")
        print(f"💬 Message: {error_message}")
        
        # Provide user-friendly error messages
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            await ctx.send("❌ An error occurred while executing the command. Please try again.")
            
            # Log detailed error for debugging
            tb = traceback.format_exception(type(error), error, error.__traceback__)
            print(f"📋 Full traceback:\n{''.join(tb)}")
        
        print("="*50)
        logger.error(f"Command error: {error_type} - {error_message}")

    async def setup_hook(self):
        """Bot setup with enhanced error handling"""
        try:
            logger.info("Setting up RPG Bot...")
            
            # Initialize systems
            await self.db.initialize()
            await self.faction_system.initialize_factions()
            await self.profile_system.initialize_achievements()
            
            # Load cogs with enhanced error reporting
            cogs_to_load = [
                "cogs.character",
                "cogs.combat", 
                "cogs.economy",
                "cogs.inventory",
                "cogs.dungeon",
                "cogs.play",
                "cogs.tutorial",
                "cogs.pvp",
                "cogs.aliases",
                "cogs.guild_interactive",
                "cogs.party",
                "cogs.profiles",
                "cogs.admin_comprehensive",
                "cogs.crafting",
                "cogs.teams",
                "cogs.pets",
                "cogs.quests",
                "cogs.lootbox",
                "cogs.help"  # New comprehensive help system
            ]

            async def _load_ext(ext: str):
                try:
                    if hasattr(self, 'load_extension'):
                        await self.load_extension(ext)
                    else:
                        self.load_extension(ext)
                    logger.info(f"✅ Loaded extension: {ext}")
                except Exception as e:
                    # Enhanced error reporting with detailed information
                    import traceback
                    error_details = traceback.format_exc()
                    
                    # Extract useful information
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    # Try to get line number and context
                    tb = traceback.extract_tb(e.__traceback__)
                    if tb:
                        last_frame = tb[-1]
                        filename = last_frame.filename
                        line_number = last_frame.lineno
                        line_content = last_frame.line if last_frame.line else "Unknown"
                        
                        print(f"\n🔥 EXTENSION LOAD ERROR: {ext}")
                        print(f"📁 File: {filename}")
                        print(f"📍 Line {line_number}: {line_content}")
                        print(f"❌ Error Type: {error_type}")
                        print(f"💬 Message: {error_message}")
                        
                        # Provide helpful suggestions based on error type
                        if error_type == "SyntaxError":
                            print(f"🔧 SYNTAX ERROR DETECTED:")
                            print(f"   • Check for missing colons, parentheses, or brackets")
                            print(f"   • Verify proper indentation (Python uses 4 spaces)")
                            print(f"   • Look for unclosed strings or comments")
                            
                        elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
                            print(f"🔧 IMPORT ERROR DETECTED:")
                            print(f"   • Check if the imported module exists")
                            print(f"   • Verify the import path is correct")
                            print(f"   • Make sure __init__.py files exist in directories")
                            
                        elif error_type == "NameError":
                            print(f"🔧 NAME ERROR DETECTED:")
                            print(f"   • Check for typos in variable/function names")
                            print(f"   • Verify all variables are defined before use")
                            print(f"   • Check if imports are missing")
                            
                        elif error_type == "IndentationError":
                            print(f"🔧 INDENTATION ERROR DETECTED:")
                            print(f"   • Use consistent indentation (4 spaces recommended)")
                            print(f"   • Check for mixed tabs and spaces")
                            print(f"   • Verify proper nesting of code blocks")
                        
                        print(f"\n📋 FULL TRACEBACK:")
                        for i, frame in enumerate(tb):
                            print(f"  {i+1}. {frame.filename}:{frame.lineno} in {frame.name}")
                            if frame.line:
                                print(f"     → {frame.line.strip()}")
                        
                        print(f"\n💡 DEBUGGING TIPS:")
                        print(f"   1. Fix the syntax error on line {line_number}")
                        print(f"   2. Check the surrounding code for context")
                        print(f"   3. Use a Python syntax checker/linter")
                        print(f"   4. Compare with working code examples")
                        print(f"\n" + "="*80)
                    else:
                        print(f"\n🔥 EXTENSION LOAD ERROR: {ext}")
                        print(f"❌ {error_type}: {error_message}")
                        print(f"📋 Full Error:\n{error_details}")
                        print("="*80)
                    
                    logger.error(f"❌ Failed to load extension {ext}: {error_type} - {error_message}")
                    raise  # Re-raise to stop bot startup

            for ext in cogs_to_load:
                await _load_ext(ext)

            logger.info("RPG Bot setup complete!")
            
        except Exception as e:
            logger.error(f"Fatal error during setup: {e}")
            print(f"\n💥 FATAL SETUP ERROR")
            print(f"❌ {type(e).__name__}: {str(e)}")
            print(f"🔧 Check the error details above and fix before restarting")
            print("="*80)
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="RPG Adventure | /help"
        )
        await self.change_presence(activity=activity)
        # Ensure per-guild command sync for immediate availability
        try:
            await self.tree.sync()
            for guild in self.guilds:
                await self.tree.sync(guild=guild)
            logger.info("Command tree synced globally and per-guild")
        except Exception as e:
            logger.warning(f"Command sync warning: {e}")
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Send welcome message
        system_channel = guild.system_channel or guild.text_channels[0]
        if system_channel and system_channel.permissions_for(guild.me).send_messages:
            embed = create_embed(
                title="🎮 Welcome to RPG Bot!",
                description=(
                    "Thank you for adding RPG Bot to your server!\n\n"
                    "**Getting Started:**\n"
                    "• Use `/character create` to create your character\n"
                    "• Use `/tutorial start` for a guided introduction\n"
                    "• Use `/help` to see all available commands\n\n"
                    "**Core Commands:**\n"
                    "• `/hunt` - Fight monsters for XP and loot\n"
                    "• `/dungeon` - Explore dungeons for rare items\n"
                    "• `/inventory` - Manage your equipment\n"
                    "• `/shop` - Buy and sell items\n\n"
                    "Happy adventuring! 🗡️"
                ),
                color=discord.Color.green()
            )
            await system_channel.send(embed=embed)

async def main():
    """Main entry point"""
    try:
        # Validate required environment variables
        if not settings.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN environment variable is required!")
            sys.exit(1)
        
        # Create and run bot
        bot = RPGBot()
        await bot.start(settings.DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
