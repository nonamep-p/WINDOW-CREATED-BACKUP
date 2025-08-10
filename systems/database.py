import logging
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.use_json_fallback = True
        
    async def initialize(self):
        """Initialize database connections"""
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        os.makedirs(os.path.join("data", "dungeons"), exist_ok=True)
        
        # Initialize default data
        await self._initialize_json_data()
        logger.info("Database initialized with JSON storage")
    
    async def _initialize_json_data(self):
        """Initialize default JSON data files"""
        default_files = {
            "players.json": {},
            # Do not overwrite provided sample data files
            "items.json": self._get_default_items(),
            "monsters.json": self._get_default_monsters(),
            # legacy dungeons.json only for fallback
            "dungeons.json": self._get_default_dungeons(),
            "skills.json": self._get_default_skills(),
            "achievements.json": self._get_default_achievements()
        }
        
        for filename, default_data in default_files.items():
            if not os.path.exists(os.path.join("data", filename)):
                await self.save_json_data(filename, default_data)
    
    def _get_default_items(self) -> Dict:
        """Get default items data"""
        return {
            "health_potion": {
                "name": "Health Potion",
                "type": "consumable",
                "rarity": "common",
                "heal_amount": 20,
                "price": 15,
                "description": "Restores 20 HP"
            },
            "iron_sword": {
                "name": "Iron Sword",
                "type": "weapon",
                "rarity": "common",
                "attack": 5,
                "defense": 0,
                "price": 50,
                "description": "A basic iron sword"
            }
        }
    
    def _get_default_monsters(self) -> Dict:
        """Get default monsters data"""
        return {
            "goblin": {
                "name": "Goblin",
                "level": 1,
                "hp": 30,
                "attack": 8,
                "defense": 2,
                "xp_reward": 15,
                "gold_reward": 10,
                "description": "A small, green creature with sharp teeth"
            }
        }
    
    def _get_default_dungeons(self) -> Dict:
        """Get default dungeons data"""
        return {
            "forest": {
                "name": "Mystic Forest",
                "description": "A mysterious forest filled with magical creatures",
                "floors": 10,
                "min_level": 1,
                "monsters": ["goblin"],
                "boss": "troll",
                "boss_floor": 10,
                "xp_multiplier": 1.0,
                "gold_multiplier": 1.0
            }
        }
    
    def _get_default_skills(self) -> Dict:
        """Get default skills data"""
        return {
            "slash": {
                "id": "slash",
                "name": "Slash",
                "description": "A basic sword attack",
                "type": "active",
                "sp_cost": 20,
                "effect": {"damage": 1.5},
                "unlock_level": 1
            }
        }
    
    async def get_skill(self, skill_id: str) -> Optional[Dict]:
        """Get skill definition."""
        data = await self.load_json_data("skills.json")
        if skill_id in data:
            return data[skill_id]
        # Fallback to defaults in code
        defaults = self._get_default_skills()
        return defaults.get(skill_id)
    
    def _get_default_achievements(self) -> Dict:
        """Get default achievements data"""
        return {
            "first_battle": {
                "id": "first_battle",
                "name": "First Blood",
                "description": "Win your first battle",
                "reward": {"gold": 100, "exp": 50},
                "type": "combat"
            },
            "dungeon_cleared": {
                "id": "dungeon_cleared",
                "name": "Crawler",
                "description": "Complete a dungeon",
                "reward": {"gold": 200, "exp": 100},
                "type": "dungeon"
            },
            "pvp_win": {
                "id": "pvp_win",
                "name": "Gladiator",
                "description": "Win a PvP battle",
                "reward": {"gold": 150, "exp": 75},
                "type": "pvp"
            }
        }

    async def get_achievements(self) -> Dict[str, Dict]:
        """Load achievements map, supporting new schema with top-level 'achievements'."""
        data = await self.load_json_data("achievements.json")
        if not data:
            return self._get_default_achievements()
        if isinstance(data, dict) and "achievements" in data and isinstance(data["achievements"], dict):
            # Normalize to id->entry with id included
            norm = {}
            for aid, entry in data["achievements"].items():
                norm[aid] = {"id": aid, **entry}
            return norm
        return data
    
    async def get_factions(self) -> Dict:
        """Load factions, normalize 'bonuses' -> 'bonus' for compatibility."""
        data = await self.load_json_data("factions.json")
        if not data or "factions" not in data:
            return {
                "valor": {"name": "Valor", "bonus": {"attack": 2}},
                "wit": {"name": "Wit", "bonus": {"intelligence": 2}},
                "shadow": {"name": "Shadow", "bonus": {"agility": 2}},
            }
        result = {}
        for fid, f in data["factions"].items():
            entry = {**f}
            if "bonuses" in entry and "bonus" not in entry:
                entry["bonus"] = entry["bonuses"]
            result[fid] = entry
        return result
    
    async def get_recipes(self) -> List[Dict]:
        return [
            {"id": "health_potion_plus", "inputs": {"health_potion": 2}, "output": {"health_potion": 1, "heal_amount": 50}},
        ]
    
    async def get_player(self, user_id: int) -> Optional[Dict]:
        """Get player data"""
        data = await self.load_json_data("players.json")
        return data.get(str(user_id))
    
    async def save_player(self, user_id: int, player_data: Dict):
        """Save player data to JSON"""
        try:
            players = await self.load_json_data("players.json")
            players[str(user_id)] = player_data
            await self.save_json_data("players.json", players)
            return True
        except Exception as e:
            logger.error(f"Error saving player: {e}")
            return False

    async def update_character(self, user_id: int, update_data: Dict) -> bool:
        """Update specific character fields"""
        try:
            players = await self.load_json_data("players.json")
            user_id_str = str(user_id)
            
            if user_id_str not in players:
                return False
            
            # Update only the specified fields
            for field, value in update_data.items():
                players[user_id_str][field] = value
            
            await self.save_json_data("players.json", players)
            return True
        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return False
    
    async def get_all_players(self) -> List[Dict]:
        """Get all players"""
        data = await self.load_json_data("players.json")
        return list(data.values())
    
    async def load_items(self) -> Dict[str, Dict]:
        """Load items map supporting new schema (top-level 'items')."""
        data = await self.load_json_data("items.json")
        base: Dict[str, Dict] = {}
        if not data:
            base = {}
        elif isinstance(data, dict) and "items" in data and isinstance(data["items"], dict):
            base = data["items"].copy()
        else:
            base = data.copy() if isinstance(data, dict) else {}
        # Merge items_extra.json if present
        extra = await self.load_json_data("items_extra.json")
        if isinstance(extra, dict) and "items" in extra and isinstance(extra["items"], dict):
            for k, v in extra["items"].items():
                base[k] = v
        return base

    async def get_item(self, item_id: str) -> Optional[Dict]:
        items = await self.load_items()
        if item_id in items:
            return items[item_id]
        # If categorized (legacy)
        for category in items.values():
            if isinstance(category, dict) and item_id in category:
                return category[item_id]
        return None
    
    async def load_monsters(self) -> Dict[str, Dict]:
        """Load monsters map supporting new schema (top-level 'monsters')."""
        data = await self.load_json_data("monsters.json")
        base: Dict[str, Dict] = {}
        if not data:
            base = {}
        elif isinstance(data, dict) and "monsters" in data and isinstance(data["monsters"], dict):
            base = data["monsters"].copy()
        else:
            base = data.copy() if isinstance(data, dict) else {}
        # Merge monsters_extra.json if present
        extra = await self.load_json_data("monsters_extra.json")
        if isinstance(extra, dict) and "monsters" in extra and isinstance(extra["monsters"], dict):
            for k, v in extra["monsters"].items():
                base[k] = v
        return base

    async def get_monster(self, monster_id: str) -> Optional[Dict]:
        monsters = await self.load_monsters()
        return monsters.get(monster_id)

    async def list_monster_ids(self) -> List[str]:
        monsters = await self.load_monsters()
        return list(monsters.keys())
    
    async def get_dungeon(self, dungeon_id: str) -> Optional[Dict]:
        """Get dungeon data from data/dungeons/{id}.json or legacy dungeons.json."""
        path = os.path.join("data", "dungeons", f"{dungeon_id}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        # legacy fallback
        data = await self.load_json_data("dungeons.json")
        return data.get(dungeon_id)

    async def list_dungeons(self) -> List[Dict[str, Any]]:
        """List available dungeons from folder with minimal metadata."""
        dungeons_dir = os.path.join("data", "dungeons")
        results: List[Dict[str, Any]] = []
        try:
            for fname in os.listdir(dungeons_dir):
                if not fname.endswith(".json"): continue
                try:
                    with open(os.path.join(dungeons_dir, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append({
                            "id": data.get("id") or fname[:-5],
                            "name": data.get("name", fname[:-5].title()),
                            "floors": len((data.get("floors") or {}).keys()) if isinstance(data.get("floors"), dict) else data.get("floors", 0)
                        })
                except Exception:
                    continue
        except FileNotFoundError:
            pass
        return results

    async def load_classes(self) -> Dict[str, Dict]:
        """Load classes config, top-level 'classes' dict."""
        data = await self.load_json_data("classes.json")
        if isinstance(data, dict) and "classes" in data and isinstance(data["classes"], dict):
            return data["classes"]
        return {}

    async def load_stats_config(self) -> Dict:
        """Load global stats constants config from stats.json."""
        data = await self.load_json_data("stats.json")
        if not isinstance(data, dict):
            return {}
        return data

    async def load_shops(self) -> Dict[str, Dict]:
        """Load shops config, top-level 'shops' dict."""
        data = await self.load_json_data("shops.json")
        if isinstance(data, dict) and "shops" in data and isinstance(data["shops"], dict):
            return data["shops"]
        return {}
    
    async def load_json_data(self, filename: str) -> Dict:
        """Load JSON data from file"""
        filepath = os.path.join("data", filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    async def save_json_data(self, filename: str, data: Dict) -> bool:
        """Save JSON data to file"""
        filepath = os.path.join("data", filename)
        try:
            os.makedirs("data", exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        pass
