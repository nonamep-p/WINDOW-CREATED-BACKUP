import logging
import random
from typing import Dict, Optional, List
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class DungeonSystem:
    def __init__(self, db):
        self.db = db
        self.active_dungeons: Dict[str, Dict] = {}
    
    async def start_dungeon(self, user_id: int, dungeon_id: str) -> Dict:
        """Start a new dungeon run"""
        character = await self.db.get_player(user_id)
        if not character:
            raise ValueError("Character not found")
        
        dungeon = await self.db.get_dungeon(dungeon_id)
        if not dungeon:
            raise ValueError("Dungeon not found")
        
        # Check if player is already in a dungeon
        for active_dungeon in self.active_dungeons.values():
            if active_dungeon["user_id"] == user_id:
                raise ValueError("Already in a dungeon")
        
        # Resolve max floors from schema (dict floors or legacy integer)
        floors_obj = dungeon.get("floors")
        if isinstance(floors_obj, dict):
            max_floor = len(floors_obj.keys())
        else:
            max_floor = dungeon.get("floors", 10)
        
        # Create dungeon session
        session_id = f"{user_id}_{dungeon_id}_{datetime.utcnow().timestamp()}"
        
        dungeon_session = {
            "session_id": session_id,
            "user_id": user_id,
            "dungeon_id": dungeon_id,
            "dungeon": dungeon.copy(),
            "current_floor": 1,
            "max_floor": max_floor,
            "rewards": {
                "gold": 0,
                "xp": 0,
                "items": []
            },
            "started_at": datetime.utcnow().isoformat()
        }
        
        self.active_dungeons[session_id] = dungeon_session
        logger.info(f"Started dungeon {session_id} for user {user_id}")
        
        return dungeon_session
    
    async def get_dungeon_session(self, user_id: int) -> Optional[Dict]:
        """Get active dungeon session for user"""
        for session in self.active_dungeons.values():
            if session["user_id"] == user_id:
                return session
        return None
    
    async def advance_floor(self, user_id: int) -> Dict:
        """Advance to next floor in dungeon"""
        session = await self.get_dungeon_session(user_id)
        if not session:
            raise ValueError("Not in a dungeon")
        
        # Generate floor encounter
        encounter = await self._generate_floor_encounter(session)
        session["last_encounter"] = encounter
        
        # If monster/boss, caller UI can initiate combat using encounter['monster']
        
        # Add rewards for completing floor (non-combat floors still give baseline)
        floor_rewards = await self._calculate_floor_rewards(session)
        session["rewards"]["gold"] += floor_rewards["gold"]
        session["rewards"]["xp"] += floor_rewards["xp"]
        session["rewards"]["items"].extend(floor_rewards["items"])
        
        session["current_floor"] += 1
        
        # Check if dungeon is complete
        if session["current_floor"] > session["max_floor"]:
            await self._complete_dungeon(session)
        
        return session
    
    async def _generate_floor_encounter(self, session: Dict) -> Dict:
        """Generate a random encounter for the current floor"""
        dungeon = session["dungeon"]
        current_floor = session["current_floor"]
        
        floors_obj = dungeon.get("floors")
        # New schema per-floor
        if isinstance(floors_obj, dict):
            floor_cfg = floors_obj.get(str(current_floor), {})
            encounters = floor_cfg.get("encounters", {})
            # Boss encounter
            boss_id = encounters.get("boss") if isinstance(encounters, dict) else None
            if boss_id:
                monster = await self.db.get_monster(boss_id)
                if monster:
                    return {"type": "boss", "monster": monster, "floor": current_floor}
            # Weighted random
            weights = encounters.get("weights") if isinstance(encounters, dict) else None
            if isinstance(weights, dict) and weights:
                population = list(weights.keys())
                probs = [max(0.0, float(weights[k])) for k in population]
                total = sum(probs) or 1.0
                probs = [p/total for p in probs]
                # random.choices is fine
                pick = random.choices(population, weights=probs, k=1)[0]
                monster = await self.db.get_monster(pick)
                if monster:
                    return {"type": "monster", "monster": monster, "floor": current_floor}
        
        # Legacy schema
        boss_id = dungeon.get("boss")
        boss_floor = dungeon.get("boss_floor")
        if boss_id and boss_floor and current_floor == boss_floor:
            monster = await self.db.get_monster(boss_id)
            if monster:
                return {"type": "boss", "monster": monster, "floor": current_floor}
        
        regular_monsters = dungeon.get("monsters", [])
        if regular_monsters:
            monster_id = random.choice(regular_monsters)
            monster = await self.db.get_monster(monster_id)
            if monster:
                # Simple legacy scaling
                scaled_monster = monster.copy()
                scale_factor = 1 + (current_floor - 1) * 0.1
                # Try both schemas
                if "hp" in scaled_monster:
                    scaled_monster["hp"] = int(scaled_monster["hp"] * scale_factor)
                    scaled_monster["attack"] = int(scaled_monster.get("attack", 1) * scale_factor)
                    scaled_monster["defense"] = int(scaled_monster.get("defense", 0) * scale_factor)
                return {"type": "monster", "monster": scaled_monster, "floor": current_floor}
        
        # Fallback: empty floor
        return {"type": "empty", "floor": current_floor}
    
    async def _calculate_floor_rewards(self, session: Dict) -> Dict:
        """Calculate rewards for completing a floor"""
        dungeon = session["dungeon"]
        current_floor = session["current_floor"]
        
        # New schema per-floor multipliers
        base_gold = 10 + (current_floor * 5)
        base_xp = 20 + (current_floor * 10)
        mult_gold = 1.0
        mult_xp = 1.0
        floors_obj = dungeon.get("floors")
        if isinstance(floors_obj, dict):
            floor_cfg = floors_obj.get(str(current_floor), {})
            rm = floor_cfg.get("rewardsMult", {})
            mult_gold = float(rm.get("gold", 1.0))
            mult_xp = float(rm.get("xp", 1.0))
        else:
            # Legacy top-level
            mult_gold = float(dungeon.get("gold_multiplier", 1.0))
            mult_xp = float(dungeon.get("xp_multiplier", 1.0))
        
        gold_reward = int(base_gold * mult_gold)
        xp_reward = int(base_xp * mult_xp)
        
        # Random item drops (use items loader)
        items = []
        if random.random() < 0.3:
            items_data = await self.db.load_items()
            all_items = list(items_data.keys())
            if all_items:
                random_item = random.choice(all_items)
                items.append(random_item)
         
        return {"gold": gold_reward, "xp": xp_reward, "items": items}
    
    async def _complete_dungeon(self, session: Dict):
        """Complete dungeon and give final rewards"""
        user_id = session["user_id"]
        
        # Give rewards to player
        from systems.character import CharacterSystem
        char_system = CharacterSystem(self.db)
        
        await char_system.add_xp(user_id, session["rewards"]["xp"])
        await char_system.add_gold(user_id, session["rewards"]["gold"])
        
        # Add items to inventory
        from systems.inventory import InventorySystem
        inv_system = InventorySystem(self.db)
        
        for item_id in session["rewards"]["items"]:
            await inv_system.add_item(user_id, item_id)
        
        # Update player stats
        character = await self.db.get_player(user_id)
        if character:
            character["dungeons_completed"] += 1
            await self.db.save_player(user_id, character)
        
        # Remove from active dungeons
        session_id = session["session_id"]
        if session_id in self.active_dungeons:
            del self.active_dungeons[session_id]
        
        logger.info(f"Completed dungeon {session_id} for user {user_id}")
    
    async def exit_dungeon(self, user_id: int) -> Dict:
        """Exit dungeon early with partial rewards"""
        session = await self.get_dungeon_session(user_id)
        if not session:
            raise ValueError("Not in a dungeon")
        
        # Give partial rewards (50% of current rewards)
        partial_rewards = {
            "gold": session["rewards"]["gold"] // 2,
            "xp": session["rewards"]["xp"] // 2,
            "items": session["rewards"]["items"][:len(session["rewards"]["items"]) // 2]
        }
        
        # Give rewards to player
        from systems.character import CharacterSystem
        char_system = CharacterSystem(self.db)
        
        await char_system.add_xp(user_id, partial_rewards["xp"])
        await char_system.add_gold(user_id, partial_rewards["gold"])
        
        # Add items to inventory
        from systems.inventory import InventorySystem
        inv_system = InventorySystem(self.db)
        
        for item_id in partial_rewards["items"]:
            await inv_system.add_item(user_id, item_id)
        
        # Remove from active dungeons
        session_id = session["session_id"]
        if session_id in self.active_dungeons:
            del self.active_dungeons[session_id]
        
        return {
            "success": True,
            "rewards": partial_rewards,
            "message": f"Exited dungeon early. Rewards: {partial_rewards['gold']} Gold, {partial_rewards['xp']} XP"
        }
