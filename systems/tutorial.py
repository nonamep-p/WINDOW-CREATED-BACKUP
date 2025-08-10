import logging
from typing import Dict, Optional, List
from config import settings

logger = logging.getLogger(__name__)

class TutorialSystem:
    def __init__(self, db):
        self.db = db
        self.tutorial_steps = [
            {
                "step": 1,
                "title": "Welcome to Plagg's RPG! 🧀",
                "description": "Welcome to the most chaotic RPG adventure! I'm Plagg, your guide through this cheese-filled journey.",
                "action": "welcome"
            },
            {
                "step": 2,
                "title": "Creating Your Character",
                "description": "First, let's create your character! Choose your class and start your adventure.",
                "action": "create_character"
            },
            {
                "step": 3,
                "title": "Your First Battle",
                "description": "Time to fight your first monster! Let's see how combat works.",
                "action": "first_battle"
            },
            {
                "step": 4,
                "title": "Exploring Dungeons",
                "description": "Dungeons are where the real adventure begins! Let's explore one.",
                "action": "dungeon_intro"
            },
            {
                "step": 5,
                "title": "Managing Your Inventory",
                "description": "Learn how to manage your items and equipment.",
                "action": "inventory_tutorial"
            },
            {
                "step": 6,
                "title": "The Shop & Economy",
                "description": "Buy and sell items to grow stronger!",
                "action": "shop_tutorial"
            },
            {
                "step": 7,
                "title": "Tutorial Complete!",
                "description": "Congratulations! You're ready to start your adventure!",
                "action": "complete"
            }
        ]
    
    async def start_tutorial(self, user_id: int) -> Dict:
        """Start the tutorial for a new player"""
        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        # Check if tutorial is already completed
        if character.get("tutorial_completed", False):
            return {"success": False, "message": "Tutorial already completed"}
        
        # Start tutorial at step 1
        character["tutorial_step"] = 1
        character["tutorial_started"] = True
        await self.db.save_player(user_id, character)
        
        current_step = self.tutorial_steps[0]
        return {
            "success": True,
            "step": current_step,
            "message": f"Tutorial started! Step {current_step['step']}: {current_step['title']}"
        }
    
    async def get_current_tutorial_step(self, user_id: int) -> Optional[Dict]:
        """Get the current tutorial step for a player"""
        character = await self.db.get_player(user_id)
        if not character:
            return None
        
        current_step_num = character.get("tutorial_step", 0)
        if current_step_num == 0 or current_step_num > len(self.tutorial_steps):
            return None
        
        return self.tutorial_steps[current_step_num - 1]
    
    async def advance_tutorial(self, user_id: int) -> Dict:
        """Advance to the next tutorial step"""
        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        current_step = character.get("tutorial_step", 0)
        if current_step == 0:
            return {"success": False, "message": "Tutorial not started"}
        
        if current_step >= len(self.tutorial_steps):
            return {"success": False, "message": "Tutorial already completed"}
        
        # Advance to next step
        character["tutorial_step"] = current_step + 1
        
        # Check if tutorial is complete
        if character["tutorial_step"] > len(self.tutorial_steps):
            character["tutorial_completed"] = True
            character["tutorial_completed_at"] = "2024-01-01T00:00:00"
        
        await self.db.save_player(user_id, character)
        
        if character["tutorial_completed"]:
            return {
                "success": True,
                "completed": True,
                "message": "🎉 Tutorial completed! You're ready for adventure!"
            }
        else:
            next_step = self.tutorial_steps[character["tutorial_step"] - 1]
            return {
                "success": True,
                "step": next_step,
                "message": f"Step {next_step['step']}: {next_step['title']}"
            }
    
    async def skip_tutorial(self, user_id: int) -> Dict:
        """Skip the tutorial and mark as completed"""
        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        character["tutorial_completed"] = True
        character["tutorial_skipped"] = True
        character["tutorial_completed_at"] = "2024-01-01T00:00:00"
        await self.db.save_player(user_id, character)
        
        return {
            "success": True,
            "message": "Tutorial skipped! You can always use /help for guidance."
        }
    
    def get_tutorial_help(self) -> List[Dict]:
        """Get tutorial help information"""
        return [
            {
                "title": "Basic Commands",
                "commands": [
                    "/character create - Create your character",
                    "/hunt - Fight monsters for XP and loot",
                    "/dungeon - Explore dungeons",
                    "/inventory - View your items",
                    "/shop - Buy and sell items",
                    "/profile - View your character stats"
                ]
            },
            {
                "title": "Combat Guide",
                "info": [
                    "Use /hunt to fight random monsters",
                    "Each battle gives you XP and gold",
                    "Stronger monsters give better rewards",
                    "Use items during battle for advantages"
                ]
            },
            {
                "title": "Dungeon Guide",
                "info": [
                    "Dungeons have multiple floors",
                    "Each floor gets progressively harder",
                    "Boss floors appear every 5th floor",
                    "Complete dungeons for rare rewards"
                ]
            },
            {
                "title": "Economy Guide",
                "info": [
                    "Earn gold by fighting monsters",
                    "Buy items from the shop",
                    "Sell unwanted items for gold",
                    "Daily rewards give bonus gold and XP"
                ]
            }
        ]
    
    async def check_tutorial_progress(self, user_id: int) -> Dict:
        """Check tutorial progress for a player"""
        character = await self.db.get_player(user_id)
        if not character:
            return {"has_character": False, "tutorial_completed": False}
        
        tutorial_completed = character.get("tutorial_completed", False)
        tutorial_step = character.get("tutorial_step", 0)
        
        return {
            "has_character": True,
            "tutorial_completed": tutorial_completed,
            "tutorial_step": tutorial_step,
            "total_steps": len(self.tutorial_steps)
        }
