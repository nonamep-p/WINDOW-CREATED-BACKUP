import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class TeamRole(Enum):
    LEADER = "leader"
    TANK = "tank"
    HEALER = "healer"
    DPS = "dps"
    SUPPORT = "support"

class TeamStatus(Enum):
    FORMING = "forming"
    READY = "ready"
    IN_ACTIVITY = "in_activity"
    COMPLETED = "completed"

class TeamCoordinationSystem:
    def __init__(self, db):
        self.db = db
        self.active_teams: Dict[str, Dict] = {}
        
    async def create_team(self, leader_id: int, activity_type: str) -> str:
        """Create a new team"""
        team_id = f"team_{leader_id}_{int(datetime.utcnow().timestamp())}"
        
        team = {
            "team_id": team_id,
            "leader_id": leader_id,
            "activity_type": activity_type,
            "members": [leader_id],
            "roles": {leader_id: TeamRole.LEADER},
            "status": TeamStatus.FORMING,
            "ready_members": set(),
            "created_at": datetime.utcnow()
        }
        
        self.active_teams[team_id] = team
        return team_id
    
    async def join_team(self, user_id: int, team_id: str) -> bool:
        """Join a team"""
        if team_id not in self.active_teams:
            return False
        
        team = self.active_teams[team_id]
        if len(team["members"]) >= 5 or user_id in team["members"]:
            return False
        
        # Assign role based on team composition
        role = await self._assign_role(team)
        team["members"].append(user_id)
        team["roles"][user_id] = role
        
        return True
    
    async def leave_team(self, user_id: int, team_id: str) -> bool:
        """Leave a team"""
        if team_id not in self.active_teams:
            return False
        
        team = self.active_teams[team_id]
        if user_id not in team["members"]:
            return False
        
        team["members"].remove(user_id)
        del team["roles"][user_id]
        
        if user_id == team["leader_id"] and team["members"]:
            new_leader = team["members"][0]
            team["leader_id"] = new_leader
            team["roles"][new_leader] = TeamRole.LEADER
        
        if not team["members"]:
            del self.active_teams[team_id]
        
        return True
    
    async def set_ready(self, user_id: int, team_id: str, ready: bool) -> bool:
        """Set player ready status"""
        if team_id not in self.active_teams:
            return False
        
        team = self.active_teams[team_id]
        if user_id not in team["members"]:
            return False
        
        if ready:
            team["ready_members"].add(user_id)
        else:
            team["ready_members"].discard(user_id)
        
        # Check if all ready
        if len(team["ready_members"]) == len(team["members"]):
            team["status"] = TeamStatus.READY
        
        return True
    
    async def start_activity(self, team_id: str) -> bool:
        """Start team activity"""
        if team_id not in self.active_teams:
            return False
        
        team = self.active_teams[team_id]
        if len(team["ready_members"]) != len(team["members"]):
            return False
        
        team["status"] = TeamStatus.IN_ACTIVITY
        return True
    
    async def get_team_info(self, team_id: str) -> Optional[Dict]:
        """Get team information"""
        if team_id not in self.active_teams:
            return None
        
        team = self.active_teams[team_id]
        return {
            "team_id": team_id,
            "leader_id": team["leader_id"],
            "activity_type": team["activity_type"],
            "status": team["status"].value,
            "members": [
                {
                    "user_id": member_id,
                    "role": team["roles"][member_id].value,
                    "ready": member_id in team["ready_members"]
                }
                for member_id in team["members"]
            ]
        }
    
    async def _assign_role(self, team: Dict) -> TeamRole:
        """Assign best available role"""
        current_roles = list(team["roles"].values())
        
        for role in [TeamRole.TANK, TeamRole.HEALER, TeamRole.SUPPORT, TeamRole.DPS]:
            if role not in current_roles:
                return role
        
        return TeamRole.DPS
