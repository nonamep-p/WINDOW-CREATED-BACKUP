import logging
from typing import Dict, Optional, List
from config import settings

logger = logging.getLogger(__name__)

class EconomySystem:
    def __init__(self, db):
        self.db = db
    
    async def get_shop_items(self) -> List[Dict]:
        """Get available shop items from current rotation with markup."""
        items_map = await self.db.load_items()
        shops = await self.db.load_shops()
        # Default: merge all items with positive price
        if not shops:
            return [
                {**it, "id": iid}
                for iid, it in items_map.items()
                if isinstance(it, dict) and it.get("price", it.get("value", 0)) > 0
            ]
        # Build an 'armory' rotation as default
        shop = shops.get("armory") or next(iter(shops.values()))
        markup = float(shop.get("markup", 1.0))
        rotation = shop.get("rotation", [])
        # Flatten weighted rotation; simple first list
        item_ids: List[str] = []
        for entry in rotation:
            ids = entry.get("items", [])
            item_ids.extend(ids)
        seen = set()
        results: List[Dict] = []
        for iid in item_ids:
            if iid in seen: continue
            seen.add(iid)
            item = items_map.get(iid)
            if not item: continue
            base = item.get("price", item.get("value", 0))
            if base <= 0: continue
            price = int(round(base * markup))
            results.append({**item, "id": iid, "price": price})
        return results
    
    async def buy_item(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Buy an item from the shop"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        # Get item data
        item = await self.db.get_item(item_id)
        if not item:
            return False
        
        price = item.get("price", item.get("value", 0))
        if price <= 0:
            return False
        total_cost = price * quantity
        
        # Check if player has enough gold
        if character["gold"] < total_cost:
            return False
        
        # Deduct gold and add item
        from systems.character import CharacterSystem
        char_system = CharacterSystem(self.db)
        
        if await char_system.spend_gold(user_id, total_cost):
            from systems.inventory import InventorySystem
            inv_system = InventorySystem(self.db)
            return await inv_system.add_item(user_id, item_id, quantity)
        
        return False
    
    async def sell_item(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Sell an item to the shop"""
        character = await self.db.get_player(user_id)
        if not character:
            return False
        
        # Get item data
        item = await self.db.get_item(item_id)
        if not item:
            return False
        
        # Check if player has the item
        from systems.inventory import InventorySystem
        inv_system = InventorySystem(self.db)
        
        if await inv_system.remove_item(user_id, item_id, quantity):
            # Calculate sell price (usually 50% of buy price)
            base_price = item.get("price", item.get("value", 0))
            sell_price = int(base_price * 0.5 * quantity)
            
            # Add gold
            from systems.character import CharacterSystem
            char_system = CharacterSystem(self.db)
            await char_system.add_gold(user_id, sell_price)
            
            return True
        
        return False
    
    async def get_daily_reward(self, user_id: int) -> Dict:
        """Give daily reward with simple streak bonus."""
        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        last_claim_iso = character.get("last_daily_claim")
        streak = int(character.get("daily_streak", 0))
        if last_claim_iso:
            try:
                last_dt = datetime.fromisoformat(last_claim_iso)
                if (now - last_dt) < timedelta(hours=20):
                    return {"success": False, "message": "Daily reward already claimed. Try later."}
                # within 48h counts for streak
                if (now - last_dt) <= timedelta(hours=48):
                    streak += 1
                else:
                    streak = 1
            except Exception:
                streak = 1
        else:
            streak = 1
        # Cap streak bonus at 7
        bonus_mult = 1.0 + 0.05 * min(7, streak)
        reward_gold = int(round(settings.DAILY_REWARD_GOLD * bonus_mult))
        reward_xp = int(round(50 * bonus_mult))
        
        from systems.character import CharacterSystem
        char_system = CharacterSystem(self.db)
        await char_system.add_gold(user_id, reward_gold)
        await char_system.add_xp(user_id, reward_xp)
        
        character["last_daily_claim"] = now.isoformat()
        character["daily_streak"] = streak
        await self.db.save_player(user_id, character)
        
        return {"success": True, "gold": reward_gold, "xp": reward_xp, "streak": streak, "message": f"Daily claimed (x{bonus_mult:.2f})!"}
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by gold"""
        all_players = await self.db.get_all_players()
        
        # Sort by gold
        sorted_players = sorted(all_players, key=lambda x: x.get("gold", 0), reverse=True)
        
        leaderboard = []
        for i, player in enumerate(sorted_players[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "username": player.get("username", "Unknown"),
                "level": player.get("level", 1),
                "gold": player.get("gold", 0),
                "xp": player.get("xp", 0)
            })
        
        return leaderboard
