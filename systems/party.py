"""
👥 Party System
Ultra-low latency group formation and cooperative gameplay
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PartySystem:
    def __init__(self, db, character_system, combat_system):
        self.db = db
        self.character_system = character_system
        self.combat_system = combat_system
        self.active_parties = {}
        self.party_invites = {}
        
    async def create_party(self, leader_id: int, party_name: str = None) -> Dict:
        """Create a new party"""
        character = await self.character_system.get_character(leader_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        # Check if already in a party
        if await self.get_player_party(leader_id):
            return {"success": False, "message": "You are already in a party"}
        
        party_id = f"party_{leader_id}_{int(datetime.utcnow().timestamp())}"
        party_name = party_name or f"{character['username']}'s Party"
        
        party = {
            "party_id": party_id,
            "name": party_name,
            "leader_id": leader_id,
            "members": [leader_id],
            "max_members": 4,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "shared_xp": True,
            "shared_loot": True,
            "auto_loot_distribution": True,
            "settings": {
                "xp_split": "equal",  # equal, level_weighted, damage_weighted
                "loot_split": "round_robin",  # round_robin, need_based, random
                "auto_accept_invites": False
            }
        }
        
        self.active_parties[party_id] = party
        return {"success": True, "party": party, "message": f"Party '{party_name}' created!"}
    
    async def invite_player(self, inviter_id: int, target_id: int) -> Dict:
        """Invite a player to the party"""
        inviter_party = await self.get_player_party(inviter_id)
        if not inviter_party:
            return {"success": False, "message": "You are not in a party"}
        
        if inviter_party["leader_id"] != inviter_id:
            return {"success": False, "message": "Only the party leader can invite players"}
        
        if len(inviter_party["members"]) >= inviter_party["max_members"]:
            return {"success": False, "message": "Party is full"}
        
        target_character = await self.character_system.get_character(target_id)
        if not target_character:
            return {"success": False, "message": "Target player not found"}
        
        if target_id in inviter_party["members"]:
            return {"success": False, "message": "Player is already in the party"}
        
        # Check if target is in another party
        target_party = await self.get_player_party(target_id)
        if target_party:
            return {"success": False, "message": "Player is already in another party"}
        
        # Create invite
        invite_id = f"invite_{inviter_id}_{target_id}_{int(datetime.utcnow().timestamp())}"
        invite = {
            "invite_id": invite_id,
            "party_id": inviter_party["party_id"],
            "inviter_id": inviter_id,
            "target_id": target_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "status": "pending"
        }
        
        self.party_invites[invite_id] = invite
        return {"success": True, "invite_id": invite_id, "message": f"Invited {target_character['username']} to the party"}
    
    async def accept_invite(self, target_id: int, invite_id: str) -> Dict:
        """Accept a party invite"""
        invite = self.party_invites.get(invite_id)
        if not invite:
            return {"success": False, "message": "Invite not found"}
        
        if invite["target_id"] != target_id:
            return {"success": False, "message": "This invite is not for you"}
        
        if invite["status"] != "pending":
            return {"success": False, "message": "Invite has expired or been used"}
        
        # Check if expired
        expires_at = datetime.fromisoformat(invite["expires_at"])
        if datetime.utcnow() > expires_at:
            invite["status"] = "expired"
            return {"success": False, "message": "Invite has expired"}
        
        party = self.active_parties.get(invite["party_id"])
        if not party:
            return {"success": False, "message": "Party no longer exists"}
        
        if len(party["members"]) >= party["max_members"]:
            return {"success": False, "message": "Party is now full"}
        
        # Add to party
        party["members"].append(target_id)
        invite["status"] = "accepted"
        
        return {"success": True, "party": party, "message": f"Joined {party['name']}!"}
    
    async def leave_party(self, player_id: int) -> Dict:
        """Leave the current party"""
        party = await self.get_player_party(player_id)
        if not party:
            return {"success": False, "message": "You are not in a party"}
        
        if player_id == party["leader_id"]:
            # Leader leaving - disband party or transfer leadership
            if len(party["members"]) == 1:
                # Only leader in party - disband
                del self.active_parties[party["party_id"]]
                return {"success": True, "message": "Party disbanded"}
            else:
                # Transfer leadership to next member
                new_leader_id = next(member_id for member_id in party["members"] if member_id != player_id)
                party["leader_id"] = new_leader_id
                party["members"].remove(player_id)
                return {"success": True, "message": "Leadership transferred and you left the party"}
        else:
            # Regular member leaving
            party["members"].remove(player_id)
            return {"success": True, "message": "Left the party"}
    
    async def kick_member(self, leader_id: int, target_id: int) -> Dict:
        """Kick a member from the party (leader only)"""
        party = await self.get_player_party(leader_id)
        if not party:
            return {"success": False, "message": "You are not in a party"}
        
        if party["leader_id"] != leader_id:
            return {"success": False, "message": "Only the party leader can kick members"}
        
        if target_id not in party["members"]:
            return {"success": False, "message": "Player is not in the party"}
        
        if target_id == leader_id:
            return {"success": False, "message": "You cannot kick yourself"}
        
        party["members"].remove(target_id)
        return {"success": True, "message": "Player kicked from party"}
    
    async def start_party_combat(self, leader_id: int, monster_data: Dict) -> Dict:
        """Start a party combat session"""
        party = await self.get_player_party(leader_id)
        if not party:
            return {"success": False, "message": "You are not in a party"}
        
        if party["leader_id"] != leader_id:
            return {"success": False, "message": "Only the party leader can start combat"}
        
        # Check if all members are available
        for member_id in party["members"]:
            if await self.combat_system.is_in_battle(member_id):
                return {"success": False, "message": "A party member is already in combat"}
        
        # Create party combat session
        combat_id = f"party_combat_{party['party_id']}_{int(datetime.utcnow().timestamp())}"
        
        # Scale monster based on party size
        scaled_monster = self._scale_monster_for_party(monster_data, len(party["members"]))
        
        party_combat = {
            "combat_id": combat_id,
            "party_id": party["party_id"],
            "monster": scaled_monster,
            "participants": party["members"].copy(),
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "rewards": {"xp": 0, "gold": 0, "items": []},
            "damage_dealt": {member_id: 0 for member_id in party["members"]}
        }
        
        # Store in combat system
        self.combat_system.party_combats[combat_id] = party_combat
        
        return {"success": True, "combat_id": combat_id, "message": "Party combat started!"}
    
    def _scale_monster_for_party(self, monster_data: Dict, party_size: int) -> Dict:
        """Scale monster stats based on party size"""
        scaled_monster = monster_data.copy()
        
        # Scale HP based on party size
        base_hp = scaled_monster.get("hp", 100)
        scaled_hp = int(base_hp * (1 + (party_size - 1) * 0.5))
        scaled_monster["hp"] = scaled_hp
        scaled_monster["max_hp"] = scaled_hp
        
        # Scale rewards
        base_xp = scaled_monster.get("xp_reward", 10)
        scaled_monster["xp_reward"] = int(base_xp * party_size)
        
        base_gold = scaled_monster.get("gold_reward", 5)
        scaled_monster["gold_reward"] = int(base_gold * party_size)
        
        return scaled_monster
    
    async def distribute_party_rewards(self, combat_id: str) -> Dict:
        """Distribute rewards among party members"""
        party_combat = self.combat_system.party_combats.get(combat_id)
        if not party_combat:
            return {"success": False, "message": "Combat session not found"}
        
        party = self.active_parties.get(party_combat["party_id"])
        if not party:
            return {"success": False, "message": "Party not found"}
        
        rewards = party_combat["rewards"]
        participants = party_combat["participants"]
        damage_dealt = party_combat["damage_dealt"]
        
        # Calculate individual rewards
        total_damage = sum(damage_dealt.values())
        individual_rewards = {}
        
        for member_id in participants:
            if total_damage > 0:
                damage_share = damage_dealt[member_id] / total_damage
            else:
                damage_share = 1.0 / len(participants)
            
            individual_rewards[member_id] = {
                "xp": int(rewards["xp"] * damage_share),
                "gold": int(rewards["gold"] * damage_share),
                "items": []  # Items distributed separately
            }
        
        # Distribute rewards
        for member_id, member_rewards in individual_rewards.items():
            character = await self.character_system.get_character(member_id)
            if character:
                await self.character_system.add_xp(member_id, member_rewards["xp"])
                await self.character_system.add_gold(member_id, member_rewards["gold"])
        
        return {"success": True, "rewards": individual_rewards}
    
    async def get_player_party(self, player_id: int) -> Optional[Dict]:
        """Get the party a player is in"""
        for party in self.active_parties.values():
            if player_id in party["members"]:
                return party
        return None
    
    async def get_party_info(self, party_id: str) -> Optional[Dict]:
        """Get detailed party information"""
        return self.active_parties.get(party_id)
    
    async def get_party_invites(self, player_id: int) -> List[Dict]:
        """Get pending invites for a player"""
        invites = []
        for invite in self.party_invites.values():
            if invite["target_id"] == player_id and invite["status"] == "pending":
                invites.append(invite)
        return invites
    
    async def update_party_settings(self, leader_id: int, settings: Dict) -> Dict:
        """Update party settings"""
        party = await self.get_player_party(leader_id)
        if not party:
            return {"success": False, "message": "You are not in a party"}
        
        if party["leader_id"] != leader_id:
            return {"success": False, "message": "Only the party leader can change settings"}
        
        party["settings"].update(settings)
        return {"success": True, "message": "Party settings updated"}
