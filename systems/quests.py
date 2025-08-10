import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .database import DatabaseManager

class QuestSystem:
    def __init__(self, db: DatabaseManager, character_system=None, inventory_system=None):
        self.db = db
        self.character_system = character_system
        self.inventory_system = inventory_system
        
    async def get_quests(self, user_id: int) -> List[Dict]:
        """Get all active quests for user"""
        try:
            player = await self.db.load_player_data(user_id)
            return player.get("quests", [])
        except Exception as e:
            print(f"Error getting quests: {e}")
            return []
            
    async def get_daily_quests(self, user_id: int) -> List[Dict]:
        """Get daily quests for user"""
        try:
            player = await self.db.load_player_data(user_id)
            daily_quests = player.get("daily_quests", [])
            
            # Check if daily quests need refresh
            last_refresh = player.get("daily_quest_refresh", "")
            today = datetime.now().strftime("%Y-%m-%d")
            
            if last_refresh != today:
                # Generate new daily quests
                daily_quests = await self._generate_daily_quests()
                player["daily_quests"] = daily_quests
                player["daily_quest_refresh"] = today
                await self.db.save_player(user_id, player)
                
            return daily_quests
        except Exception as e:
            print(f"Error getting daily quests: {e}")
            return []
            
    async def get_weekly_quests(self, user_id: int) -> List[Dict]:
        """Get weekly quests for user"""
        try:
            player = await self.db.load_player_data(user_id)
            weekly_quests = player.get("weekly_quests", [])
            
            # Check if weekly quests need refresh
            last_refresh = player.get("weekly_quest_refresh", "")
            current_week = datetime.now().isocalendar()[1]
            
            if last_refresh != str(current_week):
                # Generate new weekly quests
                weekly_quests = await self._generate_weekly_quests()
                player["weekly_quests"] = weekly_quests
                player["weekly_quest_refresh"] = str(current_week)
                await self.db.save_player(user_id, player)
                
            return weekly_quests
        except Exception as e:
            print(f"Error getting weekly quests: {e}")
            return []
            
    async def get_achievement_quests(self, user_id: int) -> List[Dict]:
        """Get achievement quests for user"""
        try:
            player = await self.db.load_player_data(user_id)
            return player.get("achievement_quests", [])
        except Exception as e:
            print(f"Error getting achievement quests: {e}")
            return []
            
    async def _generate_daily_quests(self) -> List[Dict]:
        """Generate random daily quests"""
        quest_templates = [
            {
                "id": "defeat_monsters",
                "name": "Monster Hunter",
                "description": "Defeat 5 monsters in combat",
                "type": "combat",
                "target": 5,
                "progress": 0,
                "reward": {"gold": 100, "exp": 50}
            },
            {
                "id": "collect_gold",
                "name": "Gold Collector", 
                "description": "Collect 200 gold",
                "type": "gold",
                "target": 200,
                "progress": 0,
                "reward": {"gold": 150, "exp": 30}
            },
            {
                "id": "use_skills",
                "name": "Skill Master",
                "description": "Use skills 10 times in combat",
                "type": "skills",
                "target": 10,
                "progress": 0,
                "reward": {"gold": 75, "exp": 40}
            }
        ]
        
        # Select 3 random quests
        return random.sample(quest_templates, min(3, len(quest_templates)))
        
    async def _generate_weekly_quests(self) -> List[Dict]:
        """Generate random weekly quests"""
        quest_templates = [
            {
                "id": "dungeon_explorer",
                "name": "Dungeon Explorer",
                "description": "Complete 3 dungeon floors",
                "type": "dungeon",
                "target": 3,
                "progress": 0,
                "reward": {"gold": 500, "exp": 200, "item": "rare_weapon"}
            },
            {
                "id": "craft_items",
                "name": "Master Crafter",
                "description": "Craft 10 items",
                "type": "crafting",
                "target": 10,
                "progress": 0,
                "reward": {"gold": 300, "exp": 150}
            },
            {
                "id": "win_pvp",
                "name": "Arena Champion",
                "description": "Win 5 PvP battles",
                "type": "pvp",
                "target": 5,
                "progress": 0,
                "reward": {"gold": 400, "exp": 180}
            }
        ]
        
        # Select 2 random quests
        return random.sample(quest_templates, min(2, len(quest_templates)))
        
    async def update_quest_progress(self, user_id: int, quest_type: str, amount: int = 1):
        """Update progress for quests of a specific type"""
        try:
            player = await self.db.load_player_data(user_id)
            updated = False
            
            # Update daily quests
            for quest in player.get("daily_quests", []):
                if quest.get("type") == quest_type and not quest.get("completed", False):
                    quest["progress"] = min(quest["progress"] + amount, quest["target"])
                    if quest["progress"] >= quest["target"]:
                        quest["completed"] = True
                    updated = True
                    
            # Update weekly quests
            for quest in player.get("weekly_quests", []):
                if quest.get("type") == quest_type and not quest.get("completed", False):
                    quest["progress"] = min(quest["progress"] + amount, quest["target"])
                    if quest["progress"] >= quest["target"]:
                        quest["completed"] = True
                    updated = True
                    
            if updated:
                await self.db.save_player(user_id, player)
                
        except Exception as e:
            print(f"Error updating quest progress: {e}")
            
    async def claim_completed_rewards(self, user_id: int) -> Dict:
        """Claim rewards for all completed quests"""
        try:
            player = await self.db.load_player_data(user_id)
            total_gold = 0
            total_exp = 0
            items_gained = []
            
            # Check daily quests
            for quest in player.get("daily_quests", []):
                if quest.get("completed", False) and not quest.get("claimed", False):
                    reward = quest.get("reward", {})
                    total_gold += reward.get("gold", 0)
                    total_exp += reward.get("exp", 0)
                    if "item" in reward:
                        items_gained.append(reward["item"])
                    quest["claimed"] = True
                    
            # Check weekly quests
            for quest in player.get("weekly_quests", []):
                if quest.get("completed", False) and not quest.get("claimed", False):
                    reward = quest.get("reward", {})
                    total_gold += reward.get("gold", 0)
                    total_exp += reward.get("exp", 0)
                    if "item" in reward:
                        items_gained.append(reward["item"])
                    quest["claimed"] = True
                    
            if total_gold > 0 or total_exp > 0 or items_gained:
                # Apply rewards
                player["gold"] = player.get("gold", 0) + total_gold
                player["experience"] = player.get("experience", 0) + total_exp
                
                # Add items to inventory
                for item in items_gained:
                    if self.inventory_system:
                        await self.inventory_system.add_item(user_id, item, 1)
                        
                await self.db.save_player(user_id, player)
                
                reward_text = f"Gained {total_gold} gold, {total_exp} exp"
                if items_gained:
                    reward_text += f", {len(items_gained)} items"
                    
                return {"success": True, "message": reward_text}
            else:
                return {"success": False, "message": "No completed quests to claim"}
                
        except Exception as e:
            print(f"Error claiming quest rewards: {e}")
            return {"success": False, "message": "Failed to claim rewards"}
            
    async def claim_daily_rewards(self, user_id: int) -> Dict:
        """Claim daily quest rewards"""
        try:
            player = await self.db.load_player_data(user_id)
            total_gold = 0
            total_exp = 0
            
            for quest in player.get("daily_quests", []):
                if quest.get("completed", False) and not quest.get("claimed", False):
                    reward = quest.get("reward", {})
                    total_gold += reward.get("gold", 0)
                    total_exp += reward.get("exp", 0)
                    quest["claimed"] = True
                    
            if total_gold > 0 or total_exp > 0:
                player["gold"] = player.get("gold", 0) + total_gold
                player["experience"] = player.get("experience", 0) + total_exp
                await self.db.save_player(user_id, player)
                return {"success": True, "message": f"Claimed {total_gold} gold, {total_exp} exp!"}
            else:
                return {"success": False, "message": "No daily rewards to claim"}
                
        except Exception as e:
            print(f"Error claiming daily rewards: {e}")
            return {"success": False, "message": "Failed to claim daily rewards"}
            
    async def claim_weekly_rewards(self, user_id: int) -> Dict:
        """Claim weekly quest rewards"""
        try:
            player = await self.db.load_player_data(user_id)
            total_gold = 0
            total_exp = 0
            items_gained = []
            
            for quest in player.get("weekly_quests", []):
                if quest.get("completed", False) and not quest.get("claimed", False):
                    reward = quest.get("reward", {})
                    total_gold += reward.get("gold", 0)
                    total_exp += reward.get("exp", 0)
                    if "item" in reward:
                        items_gained.append(reward["item"])
                    quest["claimed"] = True
                    
            if total_gold > 0 or total_exp > 0 or items_gained:
                player["gold"] = player.get("gold", 0) + total_gold
                player["experience"] = player.get("experience", 0) + total_exp
                
                for item in items_gained:
                    if self.inventory_system:
                        await self.inventory_system.add_item(user_id, item, 1)
                        
                await self.db.save_player(user_id, player)
                
                reward_text = f"Claimed {total_gold} gold, {total_exp} exp"
                if items_gained:
                    reward_text += f", {len(items_gained)} items"
                    
                return {"success": True, "message": reward_text}
            else:
                return {"success": False, "message": "No weekly rewards to claim"}
                
        except Exception as e:
            print(f"Error claiming weekly rewards: {e}")
            return {"success": False, "message": "Failed to claim weekly rewards"}
