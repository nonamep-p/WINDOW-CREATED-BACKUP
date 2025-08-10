import random
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class EffortLevel(Enum):
    MINIMAL = "minimal"      # Basic actions, low rewards
    MODERATE = "moderate"    # Standard gameplay, balanced rewards
    INTENSE = "intense"      # Complex strategies, high rewards
    MASTER = "master"        # Expert coordination, maximum rewards

class ActivityType(Enum):
    COMBAT = "combat"
    DUNGEON = "dungeon"
    GUILD_RAID = "guild_raid"
    PVP_MATCH = "pvp_match"
    CRAFTING = "crafting"

class EffortBasedRewardSystem:
    def __init__(self, db, character_system=None, inventory_system=None):
        self.db = db
        self.character_system = character_system
        self.inventory_system = inventory_system
        
        # Effort multipliers for different activity types
        self.effort_multipliers = {
            ActivityType.COMBAT: {
                EffortLevel.MINIMAL: 0.5,    # Basic attack spam
                EffortLevel.MODERATE: 1.0,   # Standard combat
                EffortLevel.INTENSE: 1.8,    # Elemental combos, status effects
                EffortLevel.MASTER: 2.5      # Perfect timing, team coordination
            },
            ActivityType.DUNGEON: {
                EffortLevel.MINIMAL: 0.6,    # Solo basic runs
                EffortLevel.MODERATE: 1.0,   # Standard team runs
                EffortLevel.INTENSE: 1.9,    # Speed runs, perfect clears
                EffortLevel.MASTER: 2.8      # No-damage runs, record times
            },
            ActivityType.GUILD_RAID: {
                EffortLevel.MINIMAL: 0.7,    # Basic participation
                EffortLevel.MODERATE: 1.0,   # Standard contribution
                EffortLevel.INTENSE: 2.0,    # High damage, coordination
                EffortLevel.MASTER: 3.0      # Perfect execution, leadership
            },
            ActivityType.PVP_MATCH: {
                EffortLevel.MINIMAL: 0.5,    # Basic participation
                EffortLevel.MODERATE: 1.0,   # Standard play
                EffortLevel.INTENSE: 1.8,    # Strategic play
                EffortLevel.MASTER: 2.5      # Perfect execution
            },
            ActivityType.CRAFTING: {
                EffortLevel.MINIMAL: 0.6,    # Basic crafting
                EffortLevel.MODERATE: 1.0,   # Standard recipes
                EffortLevel.INTENSE: 1.7,    # Complex recipes, perfect quality
                EffortLevel.MASTER: 2.3      # Master crafts, rare materials
            }
        }
        
        # Team coordination bonuses
        self.team_bonuses = {
            2: 1.1,   # 10% bonus for 2 players
            3: 1.25,  # 25% bonus for 3 players
            4: 1.4,   # 40% bonus for 4 players
            5: 1.6    # 60% bonus for 5+ players
        }
        
        # Effort tracking for each player
        self.player_effort: Dict[int, Dict] = {}
        
    async def calculate_effort_level(self, user_id: int, activity_type: ActivityType, 
                                   actions: List[Dict], duration: int, team_size: int = 1) -> EffortLevel:
        """Calculate effort level based on player actions and performance"""
        
        # Analyze actions for effort indicators
        effort_indicators = {
            "complex_actions": 0,
            "perfect_timing": 0,
            "team_coordination": 0,
            "risk_taking": 0,
            "efficiency": 0
        }
        
        for action in actions:
            action_type = action.get("type", "")
            
            # Complex actions (elemental combos, status effects, etc.)
            if action_type in ["elemental_attack", "status_effect", "combo_attack"]:
                effort_indicators["complex_actions"] += 1
            
            # Perfect timing (critical hits, perfect blocks)
            if action.get("perfect_timing", False):
                effort_indicators["perfect_timing"] += 1
            
            # Team coordination (support actions, buffs)
            if action_type in ["heal", "buff", "support"]:
                effort_indicators["team_coordination"] += 1
            
            # Risk taking (low HP actions, high-risk strategies)
            if action.get("risk_level", 0) > 0.7:
                effort_indicators["risk_taking"] += 1
            
            # Efficiency (optimal resource usage)
            if action.get("efficiency", 0) > 0.8:
                effort_indicators["efficiency"] += 1
        
        # Calculate effort score
        total_actions = len(actions)
        if total_actions == 0:
            return EffortLevel.MINIMAL
        
        effort_score = sum(effort_indicators.values()) / total_actions
        
        # Team coordination bonus
        if team_size > 1:
            effort_score *= self.team_bonuses.get(team_size, 1.0)
        
        # Determine effort level
        if effort_score >= 0.8:
            return EffortLevel.MASTER
        elif effort_score >= 0.6:
            return EffortLevel.INTENSE
        elif effort_score >= 0.4:
            return EffortLevel.MODERATE
        else:
            return EffortLevel.MINIMAL
    
    async def calculate_rewards(self, user_id: int, activity_type: ActivityType, 
                              base_rewards: Dict, effort_level: EffortLevel, 
                              team_size: int = 1, duration: int = 0) -> Dict:
        """Calculate rewards based on effort level and team coordination"""
        
        # Get base multiplier for activity and effort level
        base_multiplier = self.effort_multipliers[activity_type][effort_level]
        
        # Team coordination bonus
        team_multiplier = self.team_bonuses.get(team_size, 1.0)
        
        # Duration bonus (longer activities get slightly more rewards)
        duration_bonus = min(1.2, 1.0 + (duration / 3600) * 0.2)  # Max 20% bonus for 1+ hour
        
        # Calculate final multiplier
        final_multiplier = base_multiplier * team_multiplier * duration_bonus
        
        # Calculate rewards
        rewards = {}
        for reward_type, base_amount in base_rewards.items():
            if isinstance(base_amount, (int, float)):
                rewards[reward_type] = int(base_amount * final_multiplier)
            else:
                rewards[reward_type] = base_amount
        
        # Add effort-specific bonuses
        if effort_level == EffortLevel.MASTER:
            rewards["bonus_xp"] = rewards.get("xp", 0) * 0.5  # 50% bonus XP
            rewards["rare_chance"] = 0.15  # 15% chance for rare items
        elif effort_level == EffortLevel.INTENSE:
            rewards["bonus_xp"] = rewards.get("xp", 0) * 0.25  # 25% bonus XP
            rewards["rare_chance"] = 0.08  # 8% chance for rare items
        
        # Add team coordination rewards
        if team_size > 1:
            rewards["team_bonus"] = {
                "xp_share": rewards.get("xp", 0) * 0.1,  # 10% XP shared with team
                "gold_share": rewards.get("gold", 0) * 0.05  # 5% gold shared with team
            }
        
        return rewards
    
    async def distribute_team_rewards(self, team_members: List[int], rewards: Dict, 
                                    effort_levels: Dict[int, EffortLevel]) -> Dict[int, Dict]:
        """Distribute rewards among team members based on individual effort"""
        
        team_rewards = {}
        
        for user_id in team_members:
            effort_level = effort_levels.get(user_id, EffortLevel.MINIMAL)
            
            # Individual effort multiplier
            if effort_level == EffortLevel.MASTER:
                individual_multiplier = 1.5
            elif effort_level == EffortLevel.INTENSE:
                individual_multiplier = 1.2
            elif effort_level == EffortLevel.MODERATE:
                individual_multiplier = 1.0
            else:
                individual_multiplier = 0.8
            
            # Calculate individual rewards
            individual_rewards = {}
            for reward_type, amount in rewards.items():
                if isinstance(amount, (int, float)):
                    individual_rewards[reward_type] = int(amount * individual_multiplier / len(team_members))
                else:
                    individual_rewards[reward_type] = amount
            
            team_rewards[user_id] = individual_rewards
        
        return team_rewards
    
    async def track_activity_session(self, user_id: int, activity_type: ActivityType, 
                                   session_data: Dict) -> None:
        """Track player activity session for effort analysis"""
        
        if user_id not in self.player_effort:
            self.player_effort[user_id] = {
                "sessions": [],
                "total_effort": 0,
                "activity_types": {}
            }
        
        session = {
            "activity_type": activity_type,
            "start_time": session_data.get("start_time", datetime.utcnow()),
            "duration": session_data.get("duration", 0),
            "actions": session_data.get("actions", []),
            "effort_level": session_data.get("effort_level", EffortLevel.MINIMAL),
            "team_size": session_data.get("team_size", 1),
            "rewards_earned": session_data.get("rewards", {})
        }
        
        self.player_effort[user_id]["sessions"].append(session)
        
        # Update total effort tracking
        effort_value = {
            EffortLevel.MINIMAL: 1,
            EffortLevel.MODERATE: 2,
            EffortLevel.INTENSE: 3,
            EffortLevel.MASTER: 4
        }.get(session["effort_level"], 1)
        
        self.player_effort[user_id]["total_effort"] += effort_value
        
        # Track activity type preferences
        activity_name = activity_type.value
        if activity_name not in self.player_effort[user_id]["activity_types"]:
            self.player_effort[user_id]["activity_types"][activity_name] = 0
        self.player_effort[user_id]["activity_types"][activity_name] += 1
    
    async def get_player_effort_summary(self, user_id: int) -> Dict:
        """Get summary of player's effort and activity patterns"""
        
        if user_id not in self.player_effort:
            return {
                "total_sessions": 0,
                "average_effort": EffortLevel.MINIMAL.value,
                "favorite_activity": "None",
                "total_effort_score": 0,
                "recent_performance": []
            }
        
        player_data = self.player_effort[user_id]
        sessions = player_data.get("sessions", [])
        
        if not sessions:
            return {
                "total_sessions": 0,
                "average_effort": EffortLevel.MINIMAL.value,
                "favorite_activity": "None",
                "total_effort_score": 0,
                "recent_performance": []
            }
        
        # Calculate average effort level
        effort_scores = [session.get("effort_level", EffortLevel.MINIMAL) for session in sessions]
        effort_values = {
            EffortLevel.MINIMAL: 1,
            EffortLevel.MODERATE: 2,
            EffortLevel.INTENSE: 3,
            EffortLevel.MASTER: 4
        }
        
        avg_effort_value = sum(effort_values.get(level, 1) for level in effort_scores) / len(effort_scores)
        
        if avg_effort_value >= 3.5:
            average_effort = EffortLevel.MASTER
        elif avg_effort_value >= 2.5:
            average_effort = EffortLevel.INTENSE
        elif avg_effort_value >= 1.5:
            average_effort = EffortLevel.MODERATE
        else:
            average_effort = EffortLevel.MINIMAL
        
        # Find favorite activity
        activity_counts = player_data.get("activity_types", {})
        favorite_activity = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else "None"
        
        # Recent performance (last 5 sessions)
        recent_sessions = sessions[-5:] if len(sessions) > 5 else sessions
        recent_performance = []
        
        for session in recent_sessions:
            recent_performance.append({
                "activity": session["activity_type"].value,
                "effort": session["effort_level"].value,
                "duration": session["duration"],
                "team_size": session["team_size"]
            })
        
        return {
            "total_sessions": len(sessions),
            "average_effort": average_effort.value,
            "favorite_activity": favorite_activity,
            "total_effort_score": player_data.get("total_effort", 0),
            "recent_performance": recent_performance
        }
