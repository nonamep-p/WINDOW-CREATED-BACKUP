"""
⚔️ PvP Arena System
Ultra-low latency competitive combat with rankings and rewards
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PvPSystem:
    def __init__(self, db, character_system, combat_system):
        self.db = db
        self.character_system = character_system
        self.combat_system = combat_system
        self.active_matches = {}
        self.matchmaking_queue = []
        
    async def challenge_player(self, challenger_id: int, target_id: int) -> Dict:
        """Challenge another player to PvP"""
        if challenger_id == target_id:
            return {"success": False, "message": "You cannot challenge yourself!"}
        
        # Check if players exist
        challenger = await self.character_system.get_character(challenger_id)
        target = await self.character_system.get_character(target_id)
        
        if not challenger:
            return {"success": False, "message": "You don't have a character!"}
        if not target:
            return {"success": False, "message": "Target player doesn't have a character!"}
        
        # Check if either player is in combat
        if await self.combat_system.is_in_battle(challenger_id):
            return {"success": False, "message": "You are already in combat!"}
        if await self.combat_system.is_in_battle(target_id):
            return {"success": False, "message": "Target is already in combat!"}
        
        # Create PvP match
        match_id = f"pvp_{challenger_id}_{target_id}_{int(datetime.utcnow().timestamp())}"
        match = {
            "match_id": match_id,
            "challenger_id": challenger_id,
            "target_id": target_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "winner": None,
            "rounds": [],
            "current_round": 1,
            "max_rounds": 3
        }
        
        self.active_matches[match_id] = match
        
        return {
            "success": True, 
            "message": f"Challenge sent to {target['username']}!",
            "match_id": match_id
        }
    
    async def accept_challenge(self, target_id: int, match_id: str) -> Dict:
        """Accept a PvP challenge"""
        match = self.active_matches.get(match_id)
        if not match:
            return {"success": False, "message": "Match not found!"}
        
        if match["target_id"] != target_id:
            return {"success": False, "message": "This challenge is not for you!"}
        
        if match["status"] != "pending":
            return {"success": False, "message": "Challenge already accepted or expired!"}
        
        # Start the PvP match
        match["status"] = "active"
        match["started_at"] = datetime.utcnow().isoformat()
        
        # Create first round
        await self._start_round(match_id)
        
        return {
            "success": True,
            "message": "Challenge accepted! PvP match started!",
            "match_id": match_id
        }
    
    async def _start_round(self, match_id: str) -> Dict:
        """Start a new round in PvP match"""
        match = self.active_matches.get(match_id)
        if not match:
            return {"success": False, "message": "Match not found!"}
        
        challenger = await self.character_system.get_character(match["challenger_id"])
        target = await self.character_system.get_character(match["target_id"])
        
        round_data = {
            "round": match["current_round"],
            "challenger_hp": challenger["stats"].get("hp", challenger["stats"].get("max_hp", 100)),
            "target_hp": target["stats"].get("hp", target["stats"].get("max_hp", 100)),
            "actions": [],
            "winner": None,
            # temporary flags valid until next hit
            "challenger_defend": False,
            "target_defend": False,
        }
        
        match["rounds"].append(round_data)
        
        return {"success": True, "round": round_data}
    
    async def perform_pvp_action(self, match_id: str, player_id: int, action: str, target: str = None) -> Dict:
        """Perform an action in PvP match"""
        match = self.active_matches.get(match_id)
        if not match:
            return {"success": False, "message": "Match not found!"}
        
        if player_id not in [match["challenger_id"], match["target_id"]]:
            return {"success": False, "message": "You are not in this match!"}
        
        if match["status"] != "active":
            return {"success": False, "message": "Match is not active!"}
        
        current_round = match["rounds"][-1]
        
        # Identify sides
        is_challenger = player_id == match["challenger_id"]
        attacker_side = "challenger" if is_challenger else "target"
        defender_side = "target" if is_challenger else "challenger"
        
        # Defend action: set flag and return
        if action == "defend":
            current_round[f"{attacker_side}_defend"] = True
            current_round["actions"].append({
                "player_id": player_id,
                "action": action,
                "damage": 0
            })
            return {"success": True, "damage": 0}
        
        # Flee action: concede match
        if action == "flee":
            winner = defender_side
            await self._end_match(match_id, winner)
            current_round["actions"].append({
                "player_id": player_id,
                "action": action,
                "damage": 0
            })
            return {"success": True, "message": "You fled the match."}
        
        # Simple PvP combat logic
        player = await self.character_system.get_character(player_id)
        opponent_id = match["target_id"] if is_challenger else match["challenger_id"]
        opponent = await self.character_system.get_character(opponent_id)
        
        damage = 0
        if action == "attack":
            damage = max(1, player["stats"].get("attack", 10) - opponent["stats"].get("defense", 5) // 2)
        elif action == "skill" and target:
            skill_info = self.character_system._get_skill_info(target)
            damage = int(skill_info.get("power", 10))
        else:
            # Unknown action
            return {"success": False, "message": "Unknown action"}
        
        # Apply defend reduction if defender used defend previously
        if current_round.get(f"{defender_side}_defend", False):
            damage = max(0, int(damage * 0.5))
            current_round[f"{defender_side}_defend"] = False
        
        # Apply damage
        if is_challenger:
            current_round["target_hp"] = max(0, current_round["target_hp"] - damage)
        else:
            current_round["challenger_hp"] = max(0, current_round["challenger_hp"] - damage)
        
        current_round["actions"].append({
            "player_id": player_id,
            "action": action,
            "target": target,
            "damage": damage
        })
        
        # Check if round is over
        if current_round["challenger_hp"] <= 0 or current_round["target_hp"] <= 0:
            await self._end_round(match_id)
        
        return {"success": True, "damage": damage}
    
    async def _end_round(self, match_id: str) -> Dict:
        """End current round and check match status"""
        match = self.active_matches.get(match_id)
        if not match:
            return {"success": False, "message": "Match not found!"}
        
        current_round = match["rounds"][-1]
        
        # Determine round winner
        if current_round["challenger_hp"] <= 0:
            current_round["winner"] = "target"
        elif current_round["target_hp"] <= 0:
            current_round["winner"] = "challenger"
        else:
            # Timeout - random winner
            current_round["winner"] = random.choice(["challenger", "target"])
        
        # Update match status
        challenger_wins = sum(1 for r in match["rounds"] if r["winner"] == "challenger")
        target_wins = sum(1 for r in match["rounds"] if r["winner"] == "target")
        
        if challenger_wins >= 2:
            await self._end_match(match_id, "challenger")
        elif target_wins >= 2:
            await self._end_match(match_id, "target")
        else:
            # Start next round
            match["current_round"] += 1
            await self._start_round(match_id)
        
        return {"success": True, "round_winner": current_round["winner"]}
    
    async def _end_match(self, match_id: str, winner: str) -> Dict:
        """End PvP match and award rewards"""
        match = self.active_matches.get(match_id)
        if not match:
            return {"success": False, "message": "Match not found!"}
        
        match["status"] = "completed"
        match["winner"] = winner
        match["ended_at"] = datetime.utcnow().isoformat()
        
        # Award rewards
        winner_id = match["challenger_id"] if winner == "challenger" else match["target_id"]
        loser_id = match["target_id"] if winner == "challenger" else match["challenger_id"]
        
        # Winner gets XP and gold
        await self.character_system.add_xp(winner_id, 50)
        await self.character_system.add_gold(winner_id, 25)
        
        # Loser gets some XP too
        await self.character_system.add_xp(loser_id, 20)
        
        # Update PvP stats
        winner_char = await self.character_system.get_character(winner_id)
        loser_char = await self.character_system.get_character(loser_id)
        
        winner_char.setdefault("pvp", {"wins": 0, "losses": 0})
        loser_char.setdefault("pvp", {"wins": 0, "losses": 0})
        winner_char["pvp"]["wins"] = winner_char["pvp"].get("wins", 0) + 1
        loser_char["pvp"]["losses"] = loser_char["pvp"].get("losses", 0) + 1
        
        await self.db.save_player(winner_id, winner_char)
        await self.db.save_player(loser_id, loser_char)
        
        return {"success": True, "winner": winner, "winner_id": winner_id}
    
    async def get_match_status(self, match_id: str) -> Optional[Dict]:
        """Get current match status"""
        return self.active_matches.get(match_id)
    
    async def get_player_matches(self, player_id: int) -> List[Dict]:
        """Get all matches for a player"""
        matches = []
        for match in self.active_matches.values():
            if player_id in [match["challenger_id"], match["target_id"]]:
                matches.append(match)
        return matches
