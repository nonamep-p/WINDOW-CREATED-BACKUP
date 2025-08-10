import logging
import discord
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import random
import json
import os

def setup_logging():
    """Setup logging configuration"""
    import os
    from logging.handlers import RotatingFileHandler

    os.makedirs("logs", exist_ok=True)

    log_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'

    # Console handler (clean, info+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Rotating file handler for detailed logs
    file_handler = RotatingFileHandler(
        filename=os.path.join("logs", "bot.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [console_handler, file_handler]

    # Tame overly verbose third-party loggers to keep console clean
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('discord.client').setLevel(logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

def create_embed(
    title: str = "",
    description: str = "",
    color: Optional[discord.Color] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[str] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> discord.Embed:
    """Create a formatted Discord embed"""
    if color is None:
        color = discord.Color.blue()
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp or datetime.utcnow()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    return embed

def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    elif num < 1000000000:
        return f"{num/1000000:.1f}M"
    else:
        return f"{num/1000000000:.1f}B"

def calculate_xp_for_level(level: int) -> int:
    """Calculate XP required for a given level"""
    return int(100 * (level ** 1.5))

def calculate_level_from_xp(xp: int) -> int:
    """Calculate level from total XP"""
    level = 1
    while xp >= calculate_xp_for_level(level):
        xp -= calculate_xp_for_level(level)
        level += 1
    return level

def get_random_item_from_pool(pool: List[Dict], weights: Optional[List[float]] = None) -> Optional[Dict]:
    """Get a random item from a pool with optional weights"""
    if not pool:
        return None
    
    if weights:
        return random.choices(pool, weights=weights, k=1)[0]
    else:
        return random.choice(pool)

def load_json_data(filename: str) -> Dict:
    """Load JSON data from file"""
    filepath = os.path.join("data", filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json_data(filename: str, data: Dict) -> bool:
    """Save JSON data to file"""
    filepath = os.path.join("data", filename)
    try:
        os.makedirs("data", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving {filename}: {e}")
        return False

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_rarity_color(rarity: str) -> discord.Color:
    """Get Discord color for item rarity"""
    colors = {
        "Common": discord.Color.light_grey(),
        "Uncommon": discord.Color.green(),
        "Rare": discord.Color.blue(),
        "Epic": discord.Color.purple(),
        "Legendary": discord.Color.orange(),
        "Mythic": discord.Color.red(),
        "Secret": discord.Color.dark_red()
    }
    rarity_key = (rarity or "Common").title()
    return colors.get(rarity_key, discord.Color.light_grey())

def get_rarity_emoji(rarity: str) -> str:
    """Get emoji for item rarity"""
    emojis = {
        "Common": "⚪",
        "Uncommon": "🟢",
        "Rare": "🔵",
        "Epic": "🟣",
        "Legendary": "🟠",
        "Mythic": "🔴",
        "Secret": "⚫"
    }
    rarity_key = (rarity or "Common").title()
    return emojis.get(rarity_key, "⚪")

def calculate_damage(attack: int, defense: int, critical: bool = False, multiplier: float = 1.0) -> int:
    """Calculate damage with attack, defense, and critical hits"""
    base_damage = max(1, attack - defense)
    if critical:
        base_damage = int(base_damage * 2.0)
    return max(1, int(base_damage * multiplier))

def is_critical_hit(critical_chance: float = 0.1) -> bool:
    """Determine if an attack is a critical hit"""
    return random.random() < critical_chance

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(value, max_val))

def get_plagg_quote() -> str:
    """Get a random Plagg quote"""
    quotes = [
        "🧀 Time to cause some chaos!",
        "🧀 Cheese is the answer to everything!",
        "🧀 Destruction is just another form of creation... with cheese!",
        "🧀 I'm not chaotic, I'm just... creatively destructive!",
        "🧀 The best battles are the ones with cheese rewards!",
        "🧀 Plagg, claws out! Time to wreck some stuff!",
        "🧀 Cheese makes everything better, even destruction!",
        "🧀 I may be the Kwami of Destruction, but I'm also the Kwami of Cheese!",
        "🧀 Chaos and cheese - that's my motto!",
        "🧀 Let's turn this place upside down... after we get some cheese!"
    ]
    return random.choice(quotes)
