"""
🏰 Faction System
Ultra-low latency faction management with cooperative gameplay
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

INVITE_TTL_HOURS = 24
DEFAULT_MEMBER_CAP = 50

class FactionSystem:
    def __init__(self, db, character_system):
        self.db = db
        self.character_system = character_system
        self.factions = {}
        self.faction_raids = {}
        
    async def initialize_factions(self):
        """Initialize default factions"""
        factions_data = await self.db.get_factions()
        if not factions_data:
            # Create default factions
            default_factions = {
                "knights": {
                    "name": "Knights of Valor",
                    "description": "Noble warriors dedicated to justice and honor",
                    "emoji": "⚔️",
                    "bonus": "attack",
                    "bonus_value": 10,
                    "members": [],
                    "owner_id": None,
                    "officers": [],
                    "invites": {},
                    "member_cap": DEFAULT_MEMBER_CAP,
                    "level": 1,
                    "xp": 0,
                    "gold": 0
                },
                "mages": {
                    "name": "Arcane Circle",
                    "description": "Masters of magic and ancient knowledge",
                    "emoji": "🔮",
                    "bonus": "intelligence",
                    "bonus_value": 15,
                    "members": [],
                    "owner_id": None,
                    "officers": [],
                    "invites": {},
                    "member_cap": DEFAULT_MEMBER_CAP,
                    "level": 1,
                    "xp": 0,
                    "gold": 0
                },
                "rogues": {
                    "name": "Shadow Brotherhood",
                    "description": "Stealthy assassins and skilled thieves",
                    "emoji": "🗡️",
                    "bonus": "speed",
                    "bonus_value": 12,
                    "members": [],
                    "owner_id": None,
                    "officers": [],
                    "invites": {},
                    "member_cap": DEFAULT_MEMBER_CAP,
                    "level": 1,
                    "xp": 0,
                    "gold": 0
                },
                "merchants": {
                    "name": "Golden Guild",
                    "description": "Wealthy traders and economic masters",
                    "emoji": "💰",
                    "bonus": "gold_multiplier",
                    "bonus_value": 1.2,
                    "members": [],
                    "owner_id": None,
                    "officers": [],
                    "invites": {},
                    "member_cap": DEFAULT_MEMBER_CAP,
                    "level": 1,
                    "xp": 0,
                    "gold": 0
                }
            }
            
            await self.db.save_json_data("factions.json", {"factions": default_factions})
            self.factions = default_factions
        else:
            # Accept both {"factions": {...}} and direct {...}
            self.factions = factions_data.get("factions", factions_data)
        # Ensure required keys exist
        for fid, f in self.factions.items():
            self._normalize_faction(f)
    
    def _normalize_faction(self, faction: Dict) -> None:
        faction.setdefault("members", [])
        faction.setdefault("owner_id", None)
        faction.setdefault("officers", [])
        faction.setdefault("invites", {})  # user_id(str) -> {inviter, created_at, expires_at}
        faction.setdefault("member_cap", DEFAULT_MEMBER_CAP)
        faction.setdefault("level", 1)
        faction.setdefault("xp", 0)
        faction.setdefault("gold", 0)
    
    def _apply_faction_bonus(self, character: Dict, faction: Dict, add: bool) -> None:
        """Apply or remove faction bonus. Supports string+value or dict bonuses."""
        bonus = faction.get("bonus")
        if bonus is None:
            return
        # Ensure containers
        character.setdefault("stats", {})
        if "gold_multiplier" not in character:
            character["gold_multiplier"] = 1.0
        
        if isinstance(bonus, dict):
            for stat_key, stat_value in bonus.items():
                try:
                    value = float(stat_value)
                except Exception:
                    continue
                if stat_key == "gold_multiplier":
                    character["gold_multiplier"] = value if add else 1.0
                else:
                    current = character["stats"].get(stat_key, 0)
                    character["stats"][stat_key] = max(0, current + (value if add else -value))
        else:
            # treat as string key with separate bonus_value
            bonus_value = faction.get("bonus_value", 0)
            try:
                value = float(bonus_value)
            except Exception:
                value = 0
            if bonus == "gold_multiplier":
                character["gold_multiplier"] = value if add else 1.0
            else:
                current = character["stats"].get(bonus, 0)
                character["stats"][bonus] = max(0, current + (value if add else -value))
    
    async def join_faction(self, user_id: int, faction_id: str) -> Dict:
        """Join a faction (enforces member cap; first member becomes owner)."""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        if faction_id not in self.factions:
            return {"success": False, "message": "Faction not found"}
        
        # Check if already in a faction
        if character.get("faction"):
            return {"success": False, "message": "You are already in a faction"}
        
        faction = self.factions[faction_id]
        self._normalize_faction(faction)
        # Enforce cap
        if len(faction["members"]) >= int(faction.get("member_cap", DEFAULT_MEMBER_CAP)):
            return {"success": False, "message": "This faction is full"}
        
        # Join faction
        if user_id not in faction["members"]:
            faction["members"].append(user_id)
        if not faction.get("owner_id"):
            faction["owner_id"] = user_id
        
        # Remove invite if exists
        faction["invites"].pop(str(user_id), None)
        
        # Apply faction bonus (supports dict or string)
        self._apply_faction_bonus(character, faction, add=True)
        
        character["faction"] = faction_id
        await self.db.save_player(user_id, character)
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        
        return {
            "success": True,
            "message": f"Welcome to {faction.get('name', faction_id)}!"
        }
    
    async def leave_faction(self, user_id: int) -> Dict:
        """Leave current faction; owners must transfer if others remain."""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        faction_id = character.get("faction")
        if not faction_id:
            return {"success": False, "message": "You are not in a faction"}
        
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        self._normalize_faction(faction)
        
        if faction.get("owner_id") == user_id and len(faction.get("members", [])) > 1:
            return {"success": False, "message": "Transfer ownership before leaving"}
        
        # Remove from faction
        try:
            faction["members"].remove(user_id)
        except ValueError:
            pass
        if faction.get("owner_id") == user_id:
            faction["owner_id"] = None
        if user_id in faction.get("officers", []):
            faction["officers"] = [m for m in faction["officers"] if m != user_id]
        
        # Remove faction bonus
        self._apply_faction_bonus(character, faction, add=False)
        
        character["faction"] = None
        await self.db.save_player(user_id, character)
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        
        return {"success": True, "message": "You have left your faction"}
    
    async def get_faction_info(self, faction_id: str) -> Optional[Dict]:
        """Get faction information"""
        return self.factions.get(faction_id)
    
    async def get_all_factions(self) -> Dict:
        """Get all factions"""
        return self.factions
    
    async def contribute_to_faction(self, user_id: int, gold_amount: int) -> Dict:
        """Contribute gold to faction"""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        faction_id = character.get("faction")
        if not faction_id:
            return {"success": False, "message": "You are not in a faction"}
        
        if gold_amount <= 0:
            return {"success": False, "message": "Invalid contribution amount"}
        
        if character.get("gold", 0) < gold_amount:
            return {"success": False, "message": "Not enough gold"}
        
        # Deduct gold from player
        character["gold"] = character.get("gold", 0) - gold_amount
        await self.db.save_player(user_id, character)
        
        # Add to faction treasury
        faction = self.factions[faction_id]
        faction["gold"] = faction.get("gold", 0) + gold_amount
        
        # Add faction XP
        xp_gain = gold_amount // 10
        faction["xp"] = faction.get("xp", 0) + xp_gain
        
        # Check for faction level up
        new_level = (faction["xp"] // 1000) + 1
        if new_level > faction.get("level", 1):
            faction["level"] = new_level
            level_bonus = f"Faction leveled up to level {new_level}!"
        else:
            level_bonus = ""
        
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        
        return {
            "success": True,
            "message": f"Contributed {gold_amount} gold to faction! {level_bonus}",
            "faction_xp": xp_gain
        }
    
    async def start_faction_raid(self, user_id: int, raid_type: str = "normal") -> Dict:
        """Start a faction raid"""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        faction_id = character.get("faction")
        if not faction_id:
            return {"success": False, "message": "You must be in a faction to start raids"}
        
        faction = self.factions[faction_id]
        if len(faction["members"]) < 2:
            return {"success": False, "message": "Need at least 2 faction members for raids"}
        
        # Create raid
        raid_id = f"raid_{faction_id}_{int(datetime.utcnow().timestamp())}"
        raid = {
            "raid_id": raid_id,
            "faction_id": faction_id,
            "type": raid_type,
            "participants": [user_id],
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "rewards": {"xp": 0, "gold": 0, "items": []}
        }
        
        self.faction_raids[raid_id] = raid
        
        return {
            "success": True,
            "message": f"Faction raid started! Other members can join with `/raid join {raid_id}`",
            "raid_id": raid_id
        }
    
    async def join_faction_raid(self, user_id: int, raid_id: str) -> Dict:
        """Join a faction raid"""
        raid = self.faction_raids.get(raid_id)
        if not raid:
            return {"success": False, "message": "Raid not found"}
        
        if raid["status"] != "active":
            return {"success": False, "message": "Raid is not active"}
        
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        if character.get("faction") != raid["faction_id"]:
            return {"success": False, "message": "You must be in the same faction"}
        
        if user_id in raid["participants"]:
            return {"success": False, "message": "Already participating in this raid"}
        
        raid["participants"].append(user_id)
        
        return {"success": True, "message": "Joined faction raid!"}
    
    async def get_faction_rankings(self) -> List[Dict]:
        """Get faction rankings by level and XP"""
        factions_list = []
        for faction_id, faction in self.factions.items():
            factions_list.append({
                "id": faction_id,
                "name": faction.get("name"),
                "emoji": faction.get("emoji"),
                "level": faction.get("level", 1),
                "xp": faction.get("xp", 0),
                "members": len(faction.get("members", [])),
                "gold": faction.get("gold", 0)
            })
        
        # Sort by level (descending), then by XP (descending)
        factions_list.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
        return factions_list

    # ==== Roles & Membership Management ====
    def _member_role(self, faction: Dict, user_id: int) -> Optional[str]:
        if not faction:
            return None
        if faction.get("owner_id") == user_id:
            return "owner"
        if user_id in faction.get("officers", []):
            return "officer"
        if user_id in faction.get("members", []):
            return "member"
        return None

    async def invite_member(self, inviter_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        self._normalize_faction(faction)
        role = self._member_role(faction, inviter_id)
        if role not in ("owner", "officer"):
            return {"success": False, "message": "Only owner or officers can invite"}
        if target_id in faction["members"]:
            return {"success": False, "message": "User is already a member"}
        key = str(target_id)
        now = datetime.utcnow()
        existing = faction["invites"].get(key)
        if existing:
            try:
                exp = datetime.fromisoformat(existing.get("expires_at"))
                if exp > now:
                    return {"success": False, "message": "Invite already pending"}
            except Exception:
                pass
        faction["invites"][key] = {
            "inviter": inviter_id,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=INVITE_TTL_HOURS)).isoformat()
        }
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Invite sent"}

    async def list_invites_for_user(self, user_id: int) -> List[Dict]:
        now = datetime.utcnow()
        results: List[Dict] = []
        for fid, f in self.factions.items():
            inv = f.get("invites", {}).get(str(user_id))
            if not inv:
                continue
            try:
                if datetime.fromisoformat(inv.get("expires_at")) < now:
                    continue
            except Exception:
                pass
            results.append({"faction_id": fid, "faction_name": f.get("name"), **inv})
        return results

    async def accept_invite(self, user_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        inv = faction.get("invites", {}).get(str(user_id))
        if not inv:
            return {"success": False, "message": "No invite found"}
        try:
            if datetime.fromisoformat(inv.get("expires_at")) < datetime.utcnow():
                return {"success": False, "message": "Invite expired"}
        except Exception:
            pass
        return await self.join_faction(user_id, faction_id)

    async def revoke_invite(self, actor_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        role = self._member_role(faction, actor_id)
        if role not in ("owner", "officer"):
            return {"success": False, "message": "Not permitted"}
        if str(target_id) in faction.get("invites", {}):
            faction["invites"].pop(str(target_id), None)
            await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Invite revoked"}

    async def promote_officer(self, owner_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        if faction.get("owner_id") != owner_id:
            return {"success": False, "message": "Only owner can promote"}
        if target_id not in faction.get("members", []):
            return {"success": False, "message": "Target is not a member"}
        if target_id in faction.get("officers", []):
            return {"success": False, "message": "Already an officer"}
        faction["officers"].append(target_id)
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Promoted to officer"}

    async def demote_officer(self, owner_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        if faction.get("owner_id") != owner_id:
            return {"success": False, "message": "Only owner can demote"}
        if target_id not in faction.get("officers", []):
            return {"success": False, "message": "Target is not an officer"}
        faction["officers"] = [m for m in faction["officers"] if m != target_id]
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Demoted officer"}

    async def kick_member(self, actor_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        self._normalize_faction(faction)
        role = self._member_role(faction, actor_id)
        if role not in ("owner", "officer"):
            return {"success": False, "message": "Not permitted"}
        if target_id not in faction.get("members", []):
            return {"success": False, "message": "Target is not a member"}
        if target_id == faction.get("owner_id"):
            return {"success": False, "message": "Cannot kick the owner"}
        # Officers cannot kick other officers
        if role == "officer" and target_id in faction.get("officers", []):
            return {"success": False, "message": "Officers cannot kick officers"}
        
        # Update target character
        target_char = await self.character_system.get_character(target_id)
        if target_char:
            # remove faction bonuses
            self._apply_faction_bonus(target_char, faction, add=False)
            target_char["faction"] = None
            await self.db.save_player(target_id, target_char)
        
        faction["members"] = [m for m in faction["members"] if m != target_id]
        if target_id in faction.get("officers", []):
            faction["officers"] = [m for m in faction["officers"] if m != target_id]
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Member removed"}

    async def transfer_ownership(self, owner_id: int, target_id: int, faction_id: str) -> Dict:
        faction = self.factions.get(faction_id)
        if not faction:
            return {"success": False, "message": "Faction not found"}
        if faction.get("owner_id") != owner_id:
            return {"success": False, "message": "Only owner can transfer"}
        if target_id not in faction.get("members", []):
            return {"success": False, "message": "Target must be a member"}
        if target_id == owner_id:
            return {"success": False, "message": "Already the owner"}
        faction["owner_id"] = target_id
        # make previous owner an officer (if not already)
        if owner_id not in faction.get("officers", []):
            faction["officers"].append(owner_id)
        await self.db.save_json_data("factions.json", {"factions": self.factions})
        return {"success": True, "message": "Ownership transferred"}
