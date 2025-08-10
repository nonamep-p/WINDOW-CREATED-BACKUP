#!/usr/bin/env python3
"""
Setup script for Plagg Bot - Interactive Discord RPG Experience
"""

import os
import json
from pathlib import Path

def create_env_file():
    """Create a .env file with default values."""
    env_content = """# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here

# Bot Settings
BOT_PREFIX=!
DEBUG_MODE=False

# Game Configuration
MAX_LEVEL=100
XP_MULTIPLIER=1.0
GOLD_MULTIPLIER=1.0

# Combat Configuration
BASE_ATTACK_POWER=10
BASE_DEFENSE=5
CRITICAL_HIT_CHANCE=0.1
CRITICAL_HIT_MULTIPLIER=2.0

# Economy Configuration
STARTING_GOLD=100
DAILY_REWARD_GOLD=50

# Rate Limiting
COMMAND_COOLDOWN=3
COMBAT_COOLDOWN=30
DUNGEON_COOLDOWN=300
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Created .env file with default configuration")

def create_data_directory():
    """Create the data directory and ensure it exists."""
    Path("data").mkdir(exist_ok=True)
    print("✅ Created data directory")

def check_requirements():
    """Check if required packages are installed."""
    try:
        import discord
        import pydantic
        import aiohttp
        print("✅ All required packages are available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")

def main():
    """Main setup function."""
    print("🧀 Setting up Plagg Bot - Interactive Discord RPG Experience")
    print("=" * 60)
    
    # Create necessary directories and files
    create_data_directory()
    create_env_file()
    check_requirements()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your Discord bot token")
    print("2. Run: python main.py")
    print("3. Use /help in Discord to see available commands")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
