import logging
from typing import Dict, Optional, List
from config import settings

logger = logging.getLogger(__name__)

class InventorySystem:
    def __init__(self, db):
        self.db = db
    
    async def add_item(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Add item to player's inventory"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        # Get item data
        item = await self.db.get_item(item_id)
        if not item:
            return False
        
        # Add to inventory
        inventory = character.get("inventory", [])
        
        # Determine stackable default by type
        item_type = (item.get("type", "").lower())
        default_stackable = item_type in {"consumable", "material"}
        
        # Check if item already exists
        existing_item = None
        for inv_item in inventory:
            if inv_item["id"] == item_id:
                existing_item = inv_item
                break
        
        if existing_item and item.get("stackable", default_stackable):
            existing_item["quantity"] += quantity
        else:
            inventory.append({
                "id": item_id,
                "quantity": quantity,
                "acquired_at": "2024-01-01T00:00:00"
            })
        
        character["inventory"] = inventory
        await self.db.save_player(user_id, character)
        return True
    
    async def remove_item(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Remove item from player's inventory"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        inventory = character.get("inventory", [])
        
        for i, inv_item in enumerate(inventory):
            if inv_item["id"] == item_id:
                if inv_item["quantity"] <= quantity:
                    inventory.pop(i)
                else:
                    inv_item["quantity"] -= quantity
                
                character["inventory"] = inventory
                await self.db.save_player(user_id, character)
                return True
        
        return False
    
    async def consume_item(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Consume an item from player's inventory"""
        try:
            character = await self.db.get_player(user_id)
            if not character:
                return False
            
            inventory = character.get("inventory", [])
            
            # Find the item
            for i, inv_item in enumerate(inventory):
                if inv_item.get("id", inv_item.get("name")) == item_id:
                    current_quantity = inv_item.get("quantity", 1)
                    
                    if current_quantity >= quantity:
                        if current_quantity == quantity:
                            # Remove item completely
                            inventory.pop(i)
                        else:
                            # Reduce quantity
                            inv_item["quantity"] = current_quantity - quantity
                        
                        character["inventory"] = inventory
                        await self.db.save_player(user_id, character)
                        return True
                    else:
                        # Not enough items
                        return False
            
            # Item not found
            return False
            
        except Exception as e:
            logger.error(f"Error consuming item: {e}")
            return False

    async def save_inventory(self, user_id: int, inventory: List[Dict]) -> bool:
        """Save inventory to player data"""
        try:
            character = await self.db.get_player(user_id)
            if not character:
                return False
            
            character["inventory"] = inventory
            await self.db.save_player(user_id, character)
            return True
            
        except Exception as e:
            logger.error(f"Error saving inventory: {e}")
            return False

    async def get_inventory(self, user_id: int) -> List[Dict]:
        """Get player's inventory with full item details"""
        try:
            character = await self.db.get_player(user_id)
            if not character:
                return []
            
            inventory = character.get("inventory", [])
            detailed_inventory = []
            
            # Load all items data
            items_data = await self.db.load_items()
            
            for inv_item in inventory:
                item_id = inv_item.get("id", inv_item.get("name"))
                if item_id in items_data:
                    item_data = items_data[item_id].copy()
                    item_data.update(inv_item)  # Merge with inventory data (quantity, etc.)
                    detailed_inventory.append(item_data)
                else:
                    # Item not in database, keep as is
                    detailed_inventory.append(inv_item)
            
            return detailed_inventory
            
        except Exception as e:
            logger.error(f"Error getting inventory: {e}")
            return []
    
    async def count_item(self, user_id: int, item_id: str) -> int:
        """Count how many of an item the player has."""
        character = await self.db.get_player(user_id)
        if not character:
            return 0
        total = 0
        for inv_item in character.get("inventory", []):
            if inv_item.get("id") == item_id:
                total += int(inv_item.get("quantity", 0))
        return total
    
    async def use_item(self, user_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Use an item and apply its effects to the character"""
        try:
            # Get item info
            item = await self.db.get_item(item_id)
            if not item:
                return {"success": False, "message": "Item not found"}
            
            # Check if player has the item
            player_items = await self.get_player_items(user_id)
            if item_id not in player_items or player_items[item_id]["quantity"] < quantity:
                return {"success": False, "message": "Not enough items"}
            
            # Get character
            character = await self.character_system.get_character(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            # Apply item effects
            effects = {}
            
            # HP restoration
            if "heal_amount" in item and item["heal_amount"] > 0:
                heal_amount = item["heal_amount"] * quantity
                old_hp = character["current_hp"]
                character["current_hp"] = min(character["hp"], character["current_hp"] + heal_amount)
                effects["hp_healed"] = character["current_hp"] - old_hp
            
            # SP restoration
            if "sp_restore" in item and item["sp_restore"] > 0:
                sp_amount = item["sp_restore"] * quantity
                old_sp = character["current_sp"]
                character["current_sp"] = min(character["sp"], character["current_sp"] + sp_amount)
                effects["sp_restored"] = character["current_sp"] - old_sp
            
            # Stat boosts
            for stat in ["attack", "defense", "speed", "luck"]:
                if stat in item and item[stat] > 0:
                    boost_amount = item[stat] * quantity
                    character[stat] += boost_amount
                    effects[f"{stat}_boost"] = boost_amount
            
            # Remove the used items
            await self.remove_item(user_id, item_id, quantity)
            
            # Update character in database
            update_data = {}
            if "hp_healed" in effects:
                update_data["current_hp"] = character["current_hp"]
            if "sp_restored" in effects:
                update_data["current_sp"] = character["current_sp"]
            for stat in ["attack", "defense", "speed", "luck"]:
                if f"{stat}_boost" in effects:
                    update_data[stat] = character[stat]
            
            if update_data:
                await self.db.update_character(user_id, update_data)
            
            return {
                "success": True,
                "message": f"Used {quantity}x {item.get('name', item_id)}",
                "effects": effects,
                "item_name": item.get("name", item_id)
            }
            
        except Exception as e:
            logger.error(f"Error using item: {e}")
            return {"success": False, "message": "Error using item"}
    
    async def _apply_item_effects(self, user_id: int, item_data: Dict) -> Dict:
        """Apply item effects to character stats"""
        try:
            character = await self.db.get_player(user_id)
            if not character:
                return {"success": False, "message": "Character not found"}
            
            effects_applied = []
            stats = character.get("stats", {})
            
            # Apply healing effects
            if "heal_amount" in item_data:
                heal_amount = item_data["heal_amount"]
                old_hp = stats.get("hp", 0)
                max_hp = stats.get("max_hp", 100)
                new_hp = min(max_hp, old_hp + heal_amount)
                stats["hp"] = new_hp
                actual_heal = new_hp - old_hp
                if actual_heal > 0:
                    effects_applied.append(f"Restored {actual_heal} HP")
            
            # Apply SP restoration
            if "sp_amount" in item_data:
                sp_amount = item_data["sp_amount"]
                old_sp = stats.get("sp", 0)
                max_sp = stats.get("max_sp", 50)
                new_sp = min(max_sp, old_sp + sp_amount)
                stats["sp"] = new_sp
                actual_sp = new_sp - old_sp
                if actual_sp > 0:
                    effects_applied.append(f"Restored {actual_sp} SP")
            
            # Apply stat buffs
            stat_buffs = item_data.get("stat_buffs", {})
            for stat, buff in stat_buffs.items():
                if stat in stats:
                    old_value = stats[stat]
                    if isinstance(buff, dict):
                        # Percentage-based buff
                        if "percent" in buff:
                            increase = int(old_value * (buff["percent"] / 100))
                            stats[stat] += increase
                            effects_applied.append(f"+{increase} {stat.title()} ({buff['percent']}%)")
                        # Flat buff
                        elif "flat" in buff:
                            stats[stat] += buff["flat"]
                            effects_applied.append(f"+{buff['flat']} {stat.title()}")
                    else:
                        # Simple flat buff
                        stats[stat] += buff
                        effects_applied.append(f"+{buff} {stat.title()}")
            
            # Apply temporary buffs (for combat)
            temp_buffs = item_data.get("temporary_buffs", {})
            if temp_buffs:
                if "temp_buffs" not in character:
                    character["temp_buffs"] = {}
                character["temp_buffs"].update(temp_buffs)
                effects_applied.append("Temporary buffs applied")
            
            # Apply status effect cures
            if item_data.get("cures_status"):
                if "statuses" in character:
                    cured_count = len(character["statuses"])
                    character["statuses"] = []
                    if cured_count > 0:
                        effects_applied.append(f"Cured {cured_count} status effects")
            
            # Update character stats
            character["stats"] = stats
            await self.db.save_player(user_id, character)
            
            effect_message = " | ".join(effects_applied) if effects_applied else "Item used successfully"
            
            return {
                "success": True,
                "message": effect_message,
                "effects_applied": effects_applied
            }
            
        except Exception as e:
            logger.error(f"Error applying item effects: {e}")
            return {"success": False, "message": "Failed to apply item effects"}

    def _get_item_effect(self, item: Dict) -> str:
        """Get the effect description of using an item"""
        item_effects = {
            "health_potion": "Restored 50 HP!",
            "mana_potion": "Restored 30 SP!",
            "strength_potion": "Attack increased for 3 turns!",
            "defense_potion": "Defense increased for 3 turns!",
            "speed_potion": "Speed increased for 3 turns!",
            "healing_scroll": "Fully restored HP!",
            "mana_scroll": "Fully restored SP!",
            "revival_scroll": "Revived with full health!",
            "blessing_scroll": "All stats increased for 5 turns!",
            "antidote": "Cured all status effects!",
            "elixir": "Restored all HP and SP!"
        }
        
        return item_effects.get(item.get("id", ""), "Item used!")
    
    async def equip_item(self, user_id: int, item_id: str, slot: str) -> bool:
        """Equip an item"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        # Check if player has the item
        inventory = character.get("inventory", [])
        has_item = False
        for inv_item in inventory:
            if inv_item["id"] == item_id:
                has_item = True
                break
        
        if not has_item:
            return False
        
        # Get item data
        item = await self.db.get_item(item_id)
        if not item:
            return False
        
        # Check if item type matches slot
        valid_slots = {
            "weapon": "weapon",
            "armor": "armor",
            "accessory": "accessory",
            "shield": "shield"
        }
        
        if item.get("type", "").lower() not in valid_slots:
            return False
        
        equipment = character.get("equipment", {})
        equipment[slot] = item
        
        character["equipment"] = equipment
        await self.db.save_player(user_id, character)
        return True
    
    async def unequip_item(self, user_id: int, slot: str) -> bool:
        """Unequip an item"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        equipment = character.get("equipment", {})
        if slot in equipment:
            equipment[slot] = None
            character["equipment"] = equipment
            await self.db.save_player(user_id, character)
            return True
        
        return False

    async def get_player_items(self, user_id: int) -> Dict:
        """Get all items for a specific player"""
        try:
            players = await self.db.load_json_data("players.json")
            player_data = players.get(str(user_id), {})
            return player_data.get("inventory", {})
        except Exception as e:
            logger.error(f"Error getting player items: {e}")
            return {}
