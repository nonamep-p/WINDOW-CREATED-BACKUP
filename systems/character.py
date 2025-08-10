import logging
from typing import Dict, Optional, List
from datetime import datetime
from config import settings
from utils.helpers import calculate_xp_for_level, calculate_level_from_xp, format_number

logger = logging.getLogger(__name__)

class CharacterSystem:
    def __init__(self, db, inventory_system=None):
        self.db = db
        self.inventory_system = inventory_system
    
    async def create_character(self, user_id: int, username: str, character_class: str = "Warrior") -> Dict:
        """Create a new character for a user"""
        character = {
            "user_id": user_id,
            "username": username,
            "character_class": character_class,
            "level": 1,
            "experience": 0,  # Changed from xp to experience
            "gold": settings.STARTING_GOLD,
            "xp_multiplier": 1.0,
            "gold_multiplier": 1.0,
            "rebirths": 0,
            "essence": 0,  # New: Essence for cultivation
            "cultivation_levels": {  # New: Track cultivation progress
                "attack": 0,
                "defense": 0,
                "speed": 0,
                "intelligence": 0,
                "luck": 0,
                "agility": 0
            },
            "stats": self._get_base_stats(character_class),
            "equipment": {
                "weapon": None,
                "armor": None,
                "accessory": None,
                "shield": None
            },
            "inventory": [],
            "skills": ["slash"],
            "techniques": [],
            "titles": [],
            "current_title": None,
            "faction": None,
            "companion": {"name": None, "level": 1, "xp": 0, "skills": {"attack": 0, "defense": 0, "hunting": 0, "sustainability": 0}},
            "pvp": {"elo": 1000, "wins": 0, "losses": 0},
            "achievements": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "total_battles": 0,
            "battles_won": 0,
            "battles_lost": 0,
            "dungeons_completed": 0,
            "bosses_defeated": 0
        }
        
        # Initialize current HP and SP
        character["current_hp"] = character["stats"]["hp"]
        character["current_sp"] = character["stats"]["sp"]
        
        # Initialize base stats from character class
        character["hp"] = character["stats"]["hp"]
        character["sp"] = character["stats"]["sp"]
        character["attack"] = character["stats"]["attack"]
        character["defense"] = character["stats"]["defense"]
        character["speed"] = character["stats"]["speed"]
        character["luck"] = character["stats"]["luck"]
        
        await self.db.save_player(user_id, character)
        logger.info(f"Created character for user {user_id}")
        return character
    
    def _get_base_stats(self, character_class: str) -> Dict:
        """Get base stats for a character class"""
        base_stats = {
            "Warrior": {
                "hp": 100,
                "max_hp": 100,
                "sp": 50,
                "max_sp": 50,
                "attack": 15,
                "defense": 10,
                "speed": 8,
                "intelligence": 5,
                "luck": 5,
                "agility": 7
            },
            "Mage": {
                "hp": 70,
                "max_hp": 70,
                "sp": 100,
                "max_sp": 100,
                "attack": 8,
                "defense": 5,
                "speed": 6,
                "intelligence": 15,
                "luck": 8,
                "agility": 5
            },
            "Archer": {
                "hp": 80,
                "max_hp": 80,
                "sp": 60,
                "max_sp": 60,
                "attack": 12,
                "defense": 6,
                "speed": 12,
                "intelligence": 7,
                "luck": 10,
                "agility": 12
            },
            "Rogue": {
                "hp": 75,
                "max_hp": 75,
                "sp": 70,
                "max_sp": 70,
                "attack": 10,
                "defense": 4,
                "speed": 15,
                "intelligence": 6,
                "luck": 12,
                "agility": 15
            }
        }
        
        return base_stats.get(character_class, base_stats["Warrior"])
    
    async def get_character(self, user_id: int) -> Optional[Dict]:
        """Get character data for a user"""
        try:
            character = await self.db.get_player(user_id)
            if not character:
                return None
            
            # Calculate experience-related fields
            character["next_level_exp"] = self._calculate_next_level_exp(character["level"])
            character["level_progress"] = self._calculate_level_progress(character["experience"], character["level"])
            
            return character
            
        except Exception as e:
            logger.error(f"Error getting character: {e}")
            return None

    def _calculate_next_level_exp(self, level: int) -> int:
        """Calculate experience required for next level"""
        # Base experience formula: level^2 * 100
        return int((level + 1) ** 2 * 100)

    def _calculate_level_progress(self, current_exp: int, level: int) -> float:
        """Calculate progress to next level as percentage"""
        current_level_exp = self._calculate_next_level_exp(level - 1) if level > 1 else 0
        next_level_exp = self._calculate_next_level_exp(level)
        
        exp_in_level = current_exp - current_level_exp
        exp_needed = next_level_exp - current_level_exp
        
        if exp_needed <= 0:
            return 100.0
        
        progress = (exp_in_level / exp_needed) * 100
        return min(100.0, max(0.0, progress))
    
    async def get_skills(self, user_id: int) -> List[Dict]:
        """Get character skills"""
        character = await self.get_character(user_id)
        if not character:
            return []
        
        skills = character.get("skills", [])
        skill_data = []
        
        for skill_name in skills:
            skill_info = self._get_skill_info(skill_name)
            if skill_info:
                skill_data.append(skill_info)
        
        return skill_data
    
    def _get_skill_info(self, skill_name: str) -> Dict:
        """Get skill information"""
        skill_database = {
            "slash": {
                "name": "Slash",
                "description": "A powerful melee attack",
                "power": 25,
                "sp_cost": 10,
                "cooldown": 0,
                "type": "physical"
            },
            "fireball": {
                "name": "Fireball",
                "description": "Launch a ball of fire",
                "power": 30,
                "sp_cost": 15,
                "cooldown": 2,
                "type": "fire"
            },
            "heal": {
                "name": "Heal",
                "description": "Restore HP to yourself",
                "power": 40,
                "sp_cost": 20,
                "cooldown": 3,
                "type": "healing"
            },
            "shield": {
                "name": "Shield",
                "description": "Create a protective barrier",
                "power": 0,
                "sp_cost": 15,
                "cooldown": 4,
                "type": "defensive"
            },
            "lightning": {
                "name": "Lightning Strike",
                "description": "Call down lightning from the sky",
                "power": 35,
                "sp_cost": 25,
                "cooldown": 3,
                "type": "lightning"
            }
        }
        
        return skill_database.get(skill_name, {
            "name": skill_name.title(),
            "description": "Unknown skill",
            "power": 10,
            "sp_cost": 5,
            "cooldown": 0,
            "type": "physical"
        })

    async def get_all_skills(self) -> List[Dict]:
        """Get all available skills in the game"""
        return [
            {
                "name": "Slash",
                "description": "A powerful melee attack",
                "power": 25,
                "sp_cost": 10,
                "type": "Physical",
                "level_requirement": 1,
                "cooldown": 0
            },
            {
                "name": "Fireball",
                "description": "Launch a ball of fire",
                "power": 30,
                "sp_cost": 15,
                "type": "Fire",
                "level_requirement": 5,
                "cooldown": 2
            },
            {
                "name": "Heal",
                "description": "Restore HP to yourself",
                "power": 40,
                "sp_cost": 20,
                "type": "Healing",
                "level_requirement": 8,
                "cooldown": 3
            },
            {
                "name": "Shield",
                "description": "Create a protective barrier",
                "power": 0,
                "sp_cost": 15,
                "type": "Defensive",
                "level_requirement": 10,
                "cooldown": 4
            },
            {
                "name": "Lightning Strike",
                "description": "Call down lightning from the sky",
                "power": 35,
                "sp_cost": 25,
                "type": "Lightning",
                "level_requirement": 15,
                "cooldown": 3
            }
        ]
    
    async def learn_skill(self, user_id: int, skill_name: str) -> Dict:
        """Learn a new skill"""
        character = await self.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        skills = character.get("skills", [])
        if skill_name.lower() in [s.lower() for s in skills]:
            return {"success": False, "message": "You already know this skill"}
        
        # Check if character can learn this skill
        if character["level"] < self._get_skill_requirement(skill_name):
            return {"success": False, "message": f"Level {self._get_skill_requirement(skill_name)} required to learn this skill"}
        
        skills.append(skill_name.lower())
        character["skills"] = skills
        
        await self.db.save_player(user_id, character)
        return {"success": True, "message": f"Learned {skill_name}!"}
    
    def _get_skill_requirement(self, skill_name: str) -> int:
        """Get level requirement for a skill"""
        requirements = {
            "slash": 1,
            "fireball": 5,
            "heal": 8,
            "shield": 10,
            "lightning": 15
        }
        return requirements.get(skill_name.lower(), 1)
    
    async def add_xp(self, user_id: int, xp_amount: int) -> Dict:
        """Add XP to a character and handle level ups"""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        
        old_level = character["level"]
        mult = float(character.get("xp_multiplier", 1.0))
        character["experience"] += int(round(xp_amount * mult)) # Changed from xp to experience
        character["level"] = calculate_level_from_xp(character["experience"]) # Changed from xp to experience
        
        # Handle level up
        level_ups = character["level"] - old_level
        if level_ups > 0:
            character = await self._handle_level_up(character, level_ups)
        
        await self.db.save_player(user_id, character)
        return character
    
    async def _handle_level_up(self, character: Dict, level_ups: int) -> Dict:
        """Handle level up logic including stat increases and Essence rewards"""
        old_level = character["level"]
        new_level = character["level"] + level_ups
        character["level"] = new_level
        
        # Calculate stat increases for each level
        total_stat_increases = {}
        essence_gained = 0
        
        for level in range(old_level + 1, new_level + 1):
            # Base stat increases per level
            stat_increases = self._get_level_stat_increases(character["character_class"], level)
            
            # Add to total increases
            for stat, increase in stat_increases.items():
                if stat not in total_stat_increases:
                    total_stat_increases[stat] = 0
                total_stat_increases[stat] += increase
            
            # Essence reward per level (increases with level)
            essence_reward = max(5, level * 2)  # Minimum 5, scales with level
            essence_gained += essence_reward
        
        # Apply stat increases
        for stat, increase in total_stat_increases.items():
            if stat in character["stats"]:
                character["stats"][stat] += increase
                # Update max values for HP/SP
                if stat == "hp":
                    character["stats"]["max_hp"] = character["stats"]["hp"]
                elif stat == "sp":
                    character["stats"]["max_sp"] = character["stats"]["sp"]
        
        # Add Essence reward
        character["essence"] += essence_gained
        
        # Save updated character
        await self.db.save_player(character["user_id"], character)
        
        return {
            "success": True,
            "old_level": old_level,
            "new_level": new_level,
            "stat_increases": total_stat_increases,
            "essence_gained": essence_gained,
            "message": f"Level up! You are now level {new_level} and gained {essence_gained} Essence!"
        }
    
    def _get_level_stat_increases(self, character_class: str, level: int) -> Dict[str, int]:
        """Get stat increases for a specific level based on character class"""
        base_increases = {
            "hp": 10,
            "max_hp": 10,
            "sp": 5,
            "max_sp": 5,
            "attack": 2,
            "defense": 1,
            "speed": 1,
            "intelligence": 1,
            "luck": 1,
            "agility": 1
        }
        
        # Class-specific bonuses
        class_bonuses = {
            "Warrior": {"hp": 5, "max_hp": 5, "attack": 1, "defense": 1},
            "Mage": {"sp": 3, "max_sp": 3, "intelligence": 2},
            "Archer": {"speed": 2, "agility": 1, "attack": 1},
            "Rogue": {"speed": 2, "luck": 1, "agility": 1}
        }
        
        # Apply class bonuses
        final_increases = base_increases.copy()
        if character_class in class_bonuses:
            for stat, bonus in class_bonuses[character_class].items():
                final_increases[stat] += bonus
        
        # Scale with level (higher levels get slightly more stats)
        level_multiplier = 1 + (level - 1) * 0.1  # 10% increase per level
        
        for stat in final_increases:
            final_increases[stat] = int(final_increases[stat] * level_multiplier)
        
        return final_increases
    
    def _get_class_stat_increases(self, character_class: str) -> Dict[str, int]:
        """Get stat increases for each class on level up"""
        class_increases = {
            "Warrior": {
                "max_hp": 15,
                "max_sp": 3,
                "attack": 3,
                "defense": 2,
                "speed": 1,
                "intelligence": 1,
                "luck": 1,
                "agility": 1
            },
            "Mage": {
                "max_hp": 8,
                "max_sp": 12,
                "attack": 1,
                "defense": 1,
                "speed": 1,
                "intelligence": 4,
                "luck": 2,
                "agility": 1
            },
            "Archer": {
                "max_hp": 10,
                "max_sp": 5,
                "attack": 2,
                "defense": 1,
                "speed": 3,
                "intelligence": 1,
                "luck": 2,
                "agility": 3
            },
            "Rogue": {
                "max_hp": 9,
                "max_sp": 4,
                "attack": 2,
                "defense": 1,
                "speed": 3,
                "intelligence": 1,
                "luck": 3,
                "agility": 2
            }
        }
        return class_increases.get(character_class, class_increases["Warrior"])
    
    async def add_gold(self, user_id: int, gold_amount: int) -> Dict:
        """Add gold to a character"""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        
        mult = float(character.get("gold_multiplier", 1.0))
        character["gold"] += int(round(gold_amount * mult))
        await self.db.save_player(user_id, character)
        return character
    
    async def spend_gold(self, user_id: int, gold_amount: int) -> bool:
        """Spend gold from a character"""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        
        if character["gold"] < gold_amount:
            return False
        
        character["gold"] -= gold_amount
        await self.db.save_player(user_id, character)
        return True
    
    async def update_stats(self, user_id: int, stat_changes: Dict) -> Dict:
        """Update character stats (for equipment, buffs, etc.)"""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        
        for stat, change in stat_changes.items():
            if stat in character["stats"]:
                character["stats"][stat] += change
                # Ensure stats don't go below 1
                character["stats"][stat] = max(1, character["stats"][stat])
        
        await self.db.save_player(user_id, character)
        return character
    
    async def heal_character(self, user_id: int, heal_amount: int) -> bool:
        """Heal a character by the specified amount"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return False
            
            # Update current HP
            character["current_hp"] = min(character["hp"], character["current_hp"] + heal_amount)
            
            # Save to database
            await self.db.update_character(user_id, {"current_hp": character["current_hp"]})
            return True
        except Exception as e:
            logger.error(f"Error healing character: {e}")
            return False

    async def restore_sp(self, user_id: int, sp_amount: int) -> bool:
        """Restore SP to a character by the specified amount"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return False
            
            # Update current SP
            character["current_sp"] = min(character["sp"], character["current_sp"] + sp_amount)
            
            # Save to database
            await self.db.update_character(user_id, {"current_sp": character["current_sp"]})
            return True
        except Exception as e:
            logger.error(f"Error restoring SP: {e}")
            return False

    async def update_battle_stats(self, user_id: int, won: bool) -> Dict:
        """Update battle statistics"""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        
        character["total_battles"] += 1
        if won:
            character["battles_won"] += 1
        else:
            character["battles_lost"] += 1
        
        character["last_active"] = datetime.utcnow().isoformat()
        await self.db.save_player(user_id, character)
        return character

    async def grant_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Grant an achievement to the user if not already present, applying rewards."""
        character = await self.get_character(user_id)
        if not character:
            return False
        if any(a.get("id") == achievement_id for a in character.get("achievements", [])):
            return False
        achievements = await self.db.get_achievements()
        ach = achievements.get(achievement_id)
        if not ach:
            return False
        character.setdefault("achievements", []).append({"id": achievement_id, "name": ach.get("name", achievement_id), "earned_at": datetime.utcnow().isoformat()})
        reward = ach.get("reward", {})
        if reward.get("gold"):
            character["gold"] = character.get("gold", 0) + int(reward["gold"])
        if reward.get("xp"):
            await self.add_xp(user_id, int(reward["xp"]))
            character = await self.get_character(user_id)
        await self.db.save_player(user_id, character)
        return True

    async def get_rebirth_requirements(self, user_id: int) -> Dict:
        """Return requirements and eligibility for rebirth (prestige)."""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        rebirths = int(character.get("rebirths", 0))
        req_level = 20 + rebirths * 10
        req_gold = 10000 * (rebirths + 1)
        eligible = character.get("level", 1) >= req_level and character.get("gold", 0) >= req_gold
        return {"required_level": req_level, "required_gold": req_gold, "eligible": eligible, "rebirths": rebirths}

    async def perform_rebirth(self, user_id: int) -> Dict:
        """Soft reset: consume level and gold to grant permanent multipliers."""
        character = await self.get_character(user_id)
        if not character:
            raise ValueError("Character not found")
        req = await self.get_rebirth_requirements(user_id)
        if not req["eligible"]:
            return {"success": False, "message": "Requirements not met"}
        # Consume
        character["gold"] -= req["required_gold"]
        character["level"] = 1
        character["experience"] = 0 # Changed from xp to experience
        # Increase multipliers
        character["rebirths"] = int(character.get("rebirths", 0)) + 1
        character["xp_multiplier"] = float(character.get("xp_multiplier", 1.0)) + 0.05
        character["gold_multiplier"] = float(character.get("gold_multiplier", 1.0)) + 0.05
        await self.db.save_player(user_id, character)
        return {"success": True, "message": "Rebirth complete! Permanent +5% XP/Gold gained.", "rebirths": character["rebirths"]}
    
    def get_current_stats(self, character: Dict) -> Dict:
        """Compute current stats including equipment, faction, and derived values."""
        # Start from base
        stats = character["stats"].copy()
        # Ensure max fields exist
        stats.setdefault("max_hp", stats.get("hp", 100))
        stats.setdefault("max_sp", stats.get("sp", 50))

        # Equipment effects (new grammar under 'effects')
        equipment = character.get("equipment", {})
        for slot, item in equipment.items():
            if not item:
                continue
            effects = item.get("effects") or {}
            for key, val in effects.items():
                # Percentage on hp%/sp%
                if key == "hp%":
                    stats["max_hp"] = int(round(stats.get("max_hp", 0) * (1.0 + float(val))))
                elif key == "sp%":
                    stats["max_sp"] = int(round(stats.get("max_sp", 0) * (1.0 + float(val))))
                else:
                    # Flat addition for core stats and derived
                    if key in {"atk", "defense", "speed", "intelligence", "luck", "agility", "accuracy", "evasion", "pen"}:
                        stats[key] = stats.get(key, 0) + int(val)
                    elif key in {"crit_base", "crit_dmg"}:
                        stats[key] = stats.get(key, 0.0) + float(val)
        
        # Faction bonuses (normalized to 'bonus')
        faction = character.get("faction")
        if faction and isinstance(faction, dict):
            bonus = faction.get("bonus") or faction.get("bonuses") or {}
            for key, val in bonus.items():
                if key.endswith("%"):
                    base_key = key[:-1]
                    # e.g., defense% applies multiplicatively to defense if present
                    if base_key in stats:
                        stats[base_key] = int(round(stats[base_key] * (1.0 + float(val))))
                else:
                    if key in {"atk", "defense", "speed", "intelligence", "luck", "agility", "accuracy", "evasion", "pen"}:
                        stats[key] = stats.get(key, 0) + int(val)
                    elif key in {"crit_base", "crit_dmg"}:
                        stats[key] = stats.get(key, 0.0) + float(val)
        
        # Derived stats defaults
        atk = stats.get("atk", stats.get("attack", 0))
        if "attack" in stats and "atk" not in stats:
            stats["atk"] = stats["attack"]
        stats.setdefault("defense", 0)
        stats.setdefault("speed", 0)
        stats.setdefault("intelligence", 0)
        stats.setdefault("luck", 0)
        stats.setdefault("agility", 0)

        # Compute accuracy/evasion if not present
        stats.setdefault("accuracy", 50 + stats.get("agility", 0) * 2 + 0)
        stats.setdefault("evasion", 30 + stats.get("agility", 0) + stats.get("luck", 0))
        # Crit baseline and damage
        stats.setdefault("crit_base", 0.05 + stats.get("luck", 0) * 0.002)
        stats.setdefault("crit_dmg", 1.5 + stats.get("luck", 0) * 0.003)
        # Penetration default
        stats.setdefault("pen", 0)

        # Clamp current to max
        stats["hp"] = min(stats.get("hp", stats.get("max_hp", 0)), stats.get("max_hp", 0))
        stats["sp"] = min(stats.get("sp", stats.get("max_sp", 0)), stats.get("max_sp", 0))
        
        return stats
    
    def format_character_display(self, character: Dict) -> Dict:
        """Format character data for display"""
        current_stats = self.get_current_stats(character)
        
        return {
            "username": character["username"],
            "level": character["level"],
            "xp": character["experience"], # Changed from xp to experience
            "xp_for_next": calculate_xp_for_level(character["level"]),
            "gold": character["gold"],
            "stats": current_stats,
            "equipment": character["equipment"],
            "battles_won": character["battles_won"],
            "battles_lost": character["battles_lost"],
            "win_rate": (character["battles_won"] / max(1, character["total_battles"])) * 100,
            "dungeons_completed": character["dungeons_completed"],
            "bosses_defeated": character["bosses_defeated"]
        }

    async def equip_item(self, user_id: int, item) -> Dict:
        """Equip an item to the character"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            # Handle case where item is a string (item ID) instead of dict
            if isinstance(item, str):
                # Load item data from database
                items_data = await self.db.load_json_data("items.json")
                if item not in items_data:
                    return {"success": False, "message": "Item not found"}
                item = items_data[item]
            elif not isinstance(item, dict):
                return {"success": False, "message": "Invalid item data"}
            
            item_type = item.get("type", "").lower()
            if item_type not in ["weapon", "armor", "accessory"]:
                return {"success": False, "message": "This item cannot be equipped"}
            
            # Get current equipment
            equipment = character.get("equipment", {})
            current_item = equipment.get(item_type)
            
            # Unequip current item if exists
            if current_item:
                # Add current item back to inventory
                if self.inventory_system:
                    await self.inventory_system.add_item(user_id, current_item.get("id", current_item.get("name")), 1)
            
            # Equip new item
            equipment[item_type] = item
            character["equipment"] = equipment
            
            # Remove item from inventory
            if self.inventory_system:
                await self.inventory_system.consume_item(user_id, item.get("id", item.get("name")), 1)
            
            # Recalculate stats with equipment bonuses
            await self._apply_equipment_bonuses(user_id, character)
            
            # Save character
            await self.db.save_player(user_id, character)
            
            # Generate stat change message
            effects = item.get("effects", {})
            effect_text = []
            for stat, value in effects.items():
                if stat == "atk":
                    effect_text.append(f"⚔️ Attack +{value}")
                elif stat == "defense":
                    effect_text.append(f"🛡️ Defense +{value}")
                elif stat == "hp":
                    effect_text.append(f"❤️ HP +{value}")
                elif stat == "hp%":
                    effect_text.append(f"❤️ HP +{value*100:.0f}%")
                elif stat == "sp":
                    effect_text.append(f"⚡ SP +{value}")
                elif stat == "sp%":
                    effect_text.append(f"⚡ SP +{value*100:.0f}%")
                elif stat == "crit_base":
                    effect_text.append(f"💥 Crit +{value*100:.1f}%")
                elif stat == "luck":
                    effect_text.append(f"🍀 Luck +{value}")
                elif stat == "agility":
                    effect_text.append(f"💨 Agility +{value}")
                elif stat == "intelligence":
                    effect_text.append(f"🧠 Intelligence +{value}")
                elif stat == "speed":
                    effect_text.append(f"🏃 Speed +{value}")
            
            effect_message = "\n".join(effect_text) if effect_text else "No stat bonuses"
            
            return {
                "success": True, 
                "message": f"**Equipment Effects:**\n{effect_message}",
                "previous_item": current_item
            }
            
        except Exception as e:
            logger.error(f"Error equipping item: {e}")
            return {"success": False, "message": "Failed to equip item"}

    async def unequip_item(self, user_id: int, item_type: str) -> Dict:
        """Unequip an item from the character"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            equipment = character.get("equipment", {})
            current_item = equipment.get(item_type.lower())
            
            if not current_item:
                return {"success": False, "message": f"No {item_type} equipped"}
            
            # Remove item from equipment
            equipment[item_type.lower()] = None
            character["equipment"] = equipment
            
            # Add item back to inventory
            await self.db.inventory_system.add_item(user_id, current_item["id"], 1)
            
            # Recalculate stats without equipment bonuses
            await self._apply_equipment_bonuses(user_id, character)
            
            # Save character
            await self.db.save_player(user_id, character)
            
            return {
                "success": True, 
                "message": f"Unequipped {current_item['name']}",
                "unequipped_item": current_item
            }
            
        except Exception as e:
            logger.error(f"Error unequipping item: {e}")
            return {"success": False, "message": "Failed to unequip item"}

    async def _apply_equipment_bonuses(self, user_id: int, character: Dict):
        """Apply equipment bonuses to character stats"""
        try:
            # Get base stats for character class
            base_stats = self._get_base_stats(character["character_class"])
            
            # Start with base stats
            current_stats = base_stats.copy()
            
            # Apply level bonuses (existing logic)
            level = character["level"]
            stat_points_per_level = 2
            total_bonus = (level - 1) * stat_points_per_level
            
            # Distribute stat points based on class
            class_distribution = {
                "Warrior": {"attack": 0.3, "defense": 0.3, "hp": 0.2, "max_hp": 0.2},
                "Mage": {"intelligence": 0.4, "sp": 0.3, "max_sp": 0.3},
                "Archer": {"speed": 0.3, "agility": 0.3, "attack": 0.2, "luck": 0.2},
                "Rogue": {"speed": 0.4, "agility": 0.3, "luck": 0.3}
            }
            
            distribution = class_distribution.get(character["character_class"], class_distribution["Warrior"])
            
            for stat, multiplier in distribution.items():
                bonus = int(total_bonus * multiplier)
                if stat in current_stats:
                    current_stats[stat] += bonus
                elif stat == "max_hp":
                    current_stats["max_hp"] += bonus
                elif stat == "max_sp":
                    current_stats["max_sp"] += bonus
            
            # Apply equipment bonuses
            equipment = character.get("equipment", {})
            
            for slot, item in equipment.items():
                if item and item.get("effects"):
                    effects = item["effects"]
                    
                    for effect, value in effects.items():
                        if effect == "atk":
                            current_stats["attack"] += value
                        elif effect == "defense":
                            current_stats["defense"] += value
                        elif effect == "hp":
                            current_stats["hp"] += value
                            current_stats["max_hp"] += value
                        elif effect == "hp%":
                            hp_bonus = int(base_stats["max_hp"] * value)
                            current_stats["hp"] += hp_bonus
                            current_stats["max_hp"] += hp_bonus
                        elif effect == "sp":
                            current_stats["sp"] += value
                            current_stats["max_sp"] += value
                        elif effect == "sp%":
                            sp_bonus = int(base_stats["max_sp"] * value)
                            current_stats["sp"] += sp_bonus
                            current_stats["max_sp"] += sp_bonus
                        elif effect == "crit_base":
                            current_stats["crit_chance"] = current_stats.get("crit_chance", 0.05) + value
                        elif effect in ["luck", "agility", "intelligence", "speed"]:
                            current_stats[effect] += value
                        elif effect == "accuracy":
                            current_stats["accuracy"] = current_stats.get("accuracy", 70) + value
                        elif effect == "evasion":
                            current_stats["evasion"] = current_stats.get("evasion", 10) + value
                        elif effect == "pen":
                            current_stats["penetration"] = current_stats.get("penetration", 0) + value
            
            # Ensure HP and SP don't exceed max values
            current_stats["hp"] = min(current_stats["hp"], current_stats["max_hp"])
            current_stats["sp"] = min(current_stats["sp"], current_stats["max_sp"])
            
            # Apply faction bonuses if any
            if character.get("faction"):
                faction_bonus = await self._get_faction_bonus(user_id)
                if faction_bonus:
                    for stat, value in faction_bonus.items():
                        if stat in current_stats:
                            current_stats[stat] += value
            
            # Update character stats
            character["stats"] = current_stats
            
        except Exception as e:
            logger.error(f"Error applying equipment bonuses: {e}")

    async def _get_faction_bonus(self, user_id: int) -> Dict:
        """Get faction stat bonuses"""
        try:
            # This would integrate with the faction system
            # For now, return empty dict
            return {}
        except Exception as e:
            logger.error(f"Error getting faction bonus: {e}")
            return {}

    async def cultivate_stat(self, user_id: int, stat_name: str, essence_cost: int) -> Dict:
        """Cultivate a stat using Essence"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            # Check if stat exists
            if stat_name not in ["hp", "sp", "attack", "defense", "speed", "luck"]:
                return {"success": False, "message": "Invalid stat to cultivate"}
            
            # Check Essence requirement
            if character.get("essence", 0) < essence_cost:
                return {"success": False, "message": f"Not enough Essence! Need {essence_cost}, have {character.get('essence', 0)}"}
            
            # Check level requirement (can only cultivate stats at higher levels)
            min_level = self._get_cultivation_level_requirement(stat_name)
            if character["level"] < min_level:
                return {"success": False, "message": f"Level {min_level} required to cultivate {stat_name}"}
            
            # Calculate stat increase
            stat_increase = self._calculate_cultivation_bonus(character["level"], stat_name)
            
            # Apply cultivation
            character[stat_name] += stat_increase
            character["essence"] -= essence_cost
            
            # Save to database
            await self.db.update_character(user_id, {
                stat_name: character[stat_name],
                "essence": character["essence"]
            })
            
            return {
                "success": True,
                "message": f"Successfully cultivated {stat_name}! +{stat_increase} {stat_name}",
                "new_value": character[stat_name],
                "essence_remaining": character["essence"]
            }
            
        except Exception as e:
            logger.error(f"Error cultivating stat: {e}")
            return {"success": False, "message": "Error during cultivation"}

    def _get_cultivation_level_requirement(self, stat_name: str) -> int:
        """Get the minimum level required to cultivate a stat"""
        requirements = {
            "hp": 5,
            "sp": 5,
            "attack": 3,
            "defense": 3,
            "speed": 7,
            "luck": 10
        }
        return requirements.get(stat_name, 1)

    def _calculate_cultivation_bonus(self, level: int, stat_name: str) -> int:
        """Calculate the stat bonus from cultivation based on level"""
        base_bonus = {
            "hp": 10,
            "sp": 5,
            "attack": 2,
            "defense": 2,
            "speed": 1,
            "luck": 1
        }
        
        # Higher levels give better cultivation bonuses
        level_multiplier = 1 + (level - 1) * 0.1
        return int(base_bonus.get(stat_name, 1) * level_multiplier)

    async def get_cultivation_info(self, user_id: int) -> Dict:
        """Get cultivation information for a character"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            cultivation_info = {}
            for stat in ["hp", "sp", "attack", "defense", "speed", "luck"]:
                min_level = self._get_cultivation_level_requirement(stat)
                essence_cost = self._get_cultivation_essence_cost(stat, character["level"])
                stat_increase = self._calculate_cultivation_bonus(character["level"], stat)
                
                cultivation_info[stat] = {
                    "min_level": min_level,
                    "can_cultivate": character["level"] >= min_level,
                    "essence_cost": essence_cost,
                    "stat_increase": stat_increase,
                    "current_value": character[stat]
                }
            
            return {
                "success": True,
                "essence": character.get("essence", 0),
                "cultivation_info": cultivation_info
            }
            
        except Exception as e:
            logger.error(f"Error getting cultivation info: {e}")
            return {"success": False, "message": "Error getting cultivation info"}

    def _get_cultivation_essence_cost(self, stat_name: str, level: int) -> int:
        """Calculate the Essence cost for cultivating a stat"""
        base_costs = {
            "hp": 50,
            "sp": 40,
            "attack": 60,
            "defense": 60,
            "speed": 80,
            "luck": 100
        }
        
        # Higher levels cost more Essence
        level_multiplier = 1 + (level - 1) * 0.2
        return int(base_costs.get(stat_name, 50) * level_multiplier)
    
    async def is_ultimate_ready(self, user_id: int) -> bool:
        """Check if ultimate is ready (100% SP required)"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        current_sp = character.get("stats", {}).get("sp", 0)
        max_sp = character.get("stats", {}).get("max_sp", 1)
        
        # Ultimate requires 100% SP
        return current_sp >= max_sp
    
    async def use_ultimate(self, user_id: int) -> Dict:
        """Use ultimate ability (consumes 100% SP)"""
        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        current_sp = character.get("stats", {}).get("sp", 0)
        max_sp = character.get("stats", {}).get("max_sp", 1)
        
        # Check if enough SP
        if current_sp < max_sp:
            return {"success": False, "message": f"Not enough SP. Need {max_sp}, have {current_sp}"}
        
        # Consume all SP
        character["stats"]["sp"] = 0
        
        # Save updated character
        await self.db.save_player(user_id, character)
        
        return {
            "success": True,
            "message": "Ultimate unleashed! All SP consumed.",
            "sp_consumed": max_sp
        }

    async def get_ultimate_info(self, user_id: int) -> Dict:
        """Get ultimate ability information for a character"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return None
            
            # Basic ultimate info
            ultimate_info = {
                "name": "Ultimate Strike",
                "description": "A devastating attack that consumes all SP",
                "sp_cost": character["sp"],  # Costs 100% of SP
                "damage_multiplier": 3,
                "effects": ["Massive damage", "Stun chance"]
            }
            
            return ultimate_info
            
        except Exception as e:
            logger.error(f"Error getting ultimate info: {e}")
            return None

    async def get_equipment(self, user_id: int) -> Dict:
        """Get character's equipped items"""
        try:
            character = await self.get_character(user_id)
            if not character:
                return {}
            
            # Return equipped items
            equipment = {
                "weapon": character.get("equipped_weapon"),
                "armor": character.get("equipped_armor"),
                "accessory": character.get("equipped_accessory")
            }
            
            return equipment
            
        except Exception as e:
            logger.error(f"Error getting equipment: {e}")
            return {}

    async def get_skill_info(self, skill_id: str) -> Dict:
        """Get skill information by ID"""
        try:
            # Get skill from database
            skill = await self.db.get_skill(skill_id)
            if not skill:
                return None
            
            return skill
            
        except Exception as e:
            logger.error(f"Error getting skill info: {e}")
            return None
