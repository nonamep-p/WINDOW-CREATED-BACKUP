import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load .env from project root
try:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
except UnicodeDecodeError:
    # Handle encoding issues by creating a new .env file
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        env_path.unlink()
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write("DISCORD_TOKEN=your_discord_bot_token_here\n")
        f.write("BOT_PREFIX=!\n")
        f.write("DEBUG_MODE=False\n")
    load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Discord Bot Configuration
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/rpgbot")
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/rpgbot")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Message Queue Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # AI/LLM Configuration (for Adaptive AI features)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Webhook Configuration (for scalable architecture)
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    
    # Bot Settings
    BOT_PREFIX: str = os.getenv("BOT_PREFIX", "!")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    BOT_OWNER_ID: int | None = int(os.getenv("BOT_OWNER_ID", "0")) if os.getenv("BOT_OWNER_ID") else None
    
    # Game Configuration
    MAX_LEVEL: int = 100
    XP_MULTIPLIER: float = 1.0
    GOLD_MULTIPLIER: float = 1.0
    
    # Combat Configuration
    BASE_ATTACK_POWER: int = 10
    BASE_DEFENSE: int = 5
    CRITICAL_HIT_CHANCE: float = 0.1
    CRITICAL_HIT_MULTIPLIER: float = 2.0
    
    # Economy Configuration
    STARTING_GOLD: int = int(os.getenv("STARTING_GOLD", "100"))
    DAILY_REWARD_GOLD: int = 50
    
    # Dungeon Configuration
    FOREST_FLOORS: int = 10
    CAVE_FLOORS: int = 15
    CASTLE_FLOORS: int = 20
    ABYSS_FLOORS: int = 25
    
    # Rate Limiting
    COMMAND_COOLDOWN: int = 3  # seconds
    COMBAT_COOLDOWN: int = 30  # seconds
    DUNGEON_COOLDOWN: int = 300  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
