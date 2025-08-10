#!/usr/bin/env python3
"""
🎮 Discord RPG Bot - Clean Startup Script
Ultra-low latency interactive gameplay with embeds, buttons, and real-time updates
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """Print a beautiful startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  🎮 Discord RPG Bot - Advanced Tactical Combat & Cooperative Gameplay      ║
║                                                                              ║
║  Features:                                                                   ║
║  ⚔️ Advanced Combat System with Elemental Damage & Status Effects          ║
║  🏰 Guild System with Cooperative Raids & PvP Arena                        ║
║  🔨 Crafting & Trading with Player-Driven Economy                          ║
║  🎯 Skills System with Ultimate Abilities & Team Coordination              ║
║  🏰 Dynamic Dungeon System with Multiple Floors & Boss Encounters         ║
║                                                                              ║
║  Ultra-low latency • Rate limiting • Caching • Error handling              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_environment():
    """Check and setup environment"""
    print("🔧 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. Current version:", sys.version)
        return False
    
    print("✅ Python version:", sys.version.split()[0])
    
    # Check .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Creating template...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("DISCORD_TOKEN=your_discord_bot_token_here\n")
            f.write("BOT_PREFIX=!\n")
            f.write("DEBUG_MODE=False\n")
        print("✅ Created .env template")
        print("⚠️  Please edit .env and add your Discord bot token!")
        return False
    
    # Check if token is set
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if "your_discord_bot_token_here" in content:
            print("⚠️  Discord token not set in .env file")
            print("📝 Please edit .env and replace 'your_discord_bot_token_here' with your actual token")
            return False
    
    print("✅ Environment check passed")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        ('discord', 'discord.py'),
        ('dotenv', 'python-dotenv'),
        ('pydantic', 'pydantic')
    ]
    
    missing_packages = []
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

async def main():
    """Main startup function"""
    print_banner()
    
    # Environment checks
    if not check_environment():
        print("\n🚫 Startup aborted. Please fix the issues above.")
        return
    
    if not check_dependencies():
        print("\n🚫 Startup aborted. Please install missing dependencies.")
        return
    
    print("\n🚀 Starting Discord RPG Bot...")
    print("=" * 60)
    
    try:
        # Import and run the main bot
        from main import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("💡 Check your Discord token and try again")
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
