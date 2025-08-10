"""
👤 Player Profile System
Ultra-low latency profile management with rich statistics and achievements
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProfileSystem:
    def __init__(self, db, character_system):
        self.db = db
        self.character_system = character_system
        self.achievements = {}
        self.player_stats = {}
        
    async def initialize_achievements(self):
        """Initialize achievement system"""
        achievements_data = await self.db.load_json_data("achievements.json")
        if not achievements_data:
            # Create default achievements
            default_achievements = {
                "first_blood": {
                    "id": "first_blood",
                    "name": "First Blood",
                    "description": "Win your first battle",
                    "icon": "⚔️",
                    "category": "combat",
                    "points": 10,
                    "secret": False
                },
                "monster_hunter": {
                    "id": "monster_hunter",
                    "name": "Monster Hunter",
                    "description": "Defeat 10 monsters",
                    "icon": "👹",
                    "category": "combat",
                    "points": 25,
                    "secret": False
                },
                "wealthy": {
                    "id": "wealthy",
                    "name": "Wealthy",
                    "description": "Accumulate 1000 gold",
                    "icon": "💰",
                    "category": "economy",
                    "points": 15,
                    "secret": False
                },
                "skill_master": {
                    "id": "skill_master",
                    "name": "Skill Master",
                    "description": "Learn 5 different skills",
                    "icon": "📚",
                    "category": "progression",
                    "points": 30,
                    "secret": False
                },
                "pvp_champion": {
                    "id": "pvp_champion",
                    "name": "PvP Champion",
                    "description": "Win 10 PvP matches",
                    "icon": "🏆",
                    "category": "pvp",
                    "points": 50,
                    "secret": False
                },
                "faction_leader": {
                    "id": "faction_leader",
                    "name": "Faction Leader",
                    "description": "Join a faction and contribute 500 gold",
                    "icon": "🏰",
                    "category": "social",
                    "points": 20,
                    "secret": False
                },
                "dungeon_crawler": {
                    "id": "dungeon_crawler",
                    "name": "Dungeon Crawler",
                    "description": "Complete 5 dungeon floors",
                    "icon": "🏰",
                    "category": "exploration",
                    "points": 35,
                    "secret": False
                },
                "lucky": {
                    "id": "lucky",
                    "name": "Lucky",
                    "description": "Get 3 critical hits in a single battle",
                    "icon": "🍀",
                    "category": "combat",
                    "points": 15,
                    "secret": True
                }
            }
            
            await self.db.save_json_data("achievements.json", {"achievements": default_achievements})
            self.achievements = default_achievements
        else:
            self.achievements = achievements_data.get("achievements", {})
    
    async def get_player_profile(self, user_id: int) -> Dict:
        """Get comprehensive player profile"""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        
        # Get detailed stats
        stats = await self._calculate_detailed_stats(user_id, character)
        
        # Get achievements
        achievements = await self._get_player_achievements(user_id)
        
        # Get recent activity
        recent_activity = await self._get_recent_activity(user_id)
        
        # Get rankings
        rankings = await self._get_player_rankings(user_id)
        
        profile = {
            "character": character,
            "stats": stats,
            "achievements": achievements,
            "recent_activity": recent_activity,
            "rankings": rankings,
            "profile_level": await self._calculate_profile_level(achievements, stats)
        }
        
        return {"success": True, "profile": profile}
    
    async def _calculate_detailed_stats(self, user_id: int, character: Dict) -> Dict:
        """Calculate comprehensive player statistics"""
        stats = character.get("stats", {})
        
        # Combat stats
        combat_stats = {
            "total_battles": character.get("total_battles", 0),
            "battles_won": character.get("battles_won", 0),
            "battles_lost": character.get("battles_lost", 0),
            "win_rate": (character.get("battles_won", 0) / max(character.get("total_battles", 1), 1)) * 100,
            "dungeons_completed": character.get("dungeons_completed", 0),
            "bosses_defeated": character.get("bosses_defeated", 0),
            "pvp_wins": character.get("pvp", {}).get("wins", 0),
            "pvp_losses": character.get("pvp", {}).get("losses", 0),
            "pvp_win_rate": 0
        }
        
        pvp_total = combat_stats["pvp_wins"] + combat_stats["pvp_losses"]
        if pvp_total > 0:
            combat_stats["pvp_win_rate"] = (combat_stats["pvp_wins"] / pvp_total) * 100
        
        # Economic stats
        economic_stats = {
            "total_gold_earned": character.get("total_gold_earned", 0),
            "total_gold_spent": character.get("total_gold_spent", 0),
            "current_gold": character.get("gold", 0),
            "items_owned": len(character.get("inventory", [])),
            "unique_items": len(set(item.get("name") for item in character.get("inventory", [])))
        }
        
        # Progression stats
        progression_stats = {
            "level": character.get("level", 1),
            "xp": character.get("xp", 0),
            "xp_to_next": await self._calculate_xp_to_next(character),
            "skills_learned": len(character.get("skills", [])),
            "rebirths": character.get("rebirths", 0),
            "days_active": await self._calculate_days_active(character),
            "last_active": character.get("last_active", "Never")
        }
        
        # Social stats
        social_stats = {
            "faction": character.get("faction"),
            "faction_contributions": character.get("faction_contributions", 0),
            "party_sessions": character.get("party_sessions", 0),
            "guild_memberships": character.get("guild_memberships", 0)
        }
        
        return {
            "combat": combat_stats,
            "economic": economic_stats,
            "progression": progression_stats,
            "social": social_stats,
            "base_stats": stats
        }
    
    async def _get_player_achievements(self, user_id: int) -> Dict:
        """Get player achievements"""
        character = await self.character_system.get_character(user_id)
        if not character:
            return {"unlocked": [], "locked": [], "total_points": 0, "completion_percentage": 0.0}
        
        # Normalize unlocked list to IDs
        unlocked = character.get("achievements", [])
        unlocked_ids: List[str] = []
        for entry in unlocked:
            if isinstance(entry, dict):
                eid = entry.get("id")
                if eid:
                    unlocked_ids.append(eid)
            elif isinstance(entry, str):
                unlocked_ids.append(entry)
        
        total_points = sum(
            self.achievements.get(aid, {}).get("points", 0)
            for aid in unlocked_ids
        )
        
        # Build achievements list
        all_achievements = []
        for ach_id, achievement in self.achievements.items():
            achievement_data = achievement.copy()
            achievement_data["unlocked"] = ach_id in unlocked_ids
            achievement_data["unlocked_at"] = (character.get("achievement_dates", {}) or {}).get(ach_id)
            all_achievements.append(achievement_data)
        
        total_defined = max(1, len(self.achievements))
        completion = (len(unlocked_ids) / total_defined) * 100
        
        return {
            "unlocked": [ach for ach in all_achievements if ach["unlocked"]],
            "locked": [ach for ach in all_achievements if not ach["unlocked"]],
            "total_points": total_points,
            "completion_percentage": completion
        }
    
    async def _get_recent_activity(self, user_id: int) -> List[Dict]:
        """Get recent player activity"""
        activities: List[Dict] = []
        character = await self.character_system.get_character(user_id)
        if not character:
            return activities
        # Minimal placeholders; real activity feed would be persisted
        if character.get("battles_won", 0) > 0:
            activities.append({"type": "battle_won", "description": f"Won a battle", "timestamp": datetime.utcnow().isoformat(), "icon": "⚔️"})
        if character.get("level", 1) > 1:
            activities.append({"type": "level_up", "description": f"Reached level {character['level']}", "timestamp": datetime.utcnow().isoformat(), "icon": "📈"})
        return activities[:5]
    
    async def _get_player_rankings(self, user_id: int) -> Dict:
        """Get player rankings in various categories"""
        players_map = await self.db.load_json_data("players.json")
        if not players_map:
            return {}
        players_list = [{"user_id": int(uid) if str(uid).isdigit() else uid, "data": pdata} for uid, pdata in players_map.items()]
        rankings: Dict[str, Dict] = {}
        
        # Level ranking
        level_ranking = sorted(players_list, key=lambda x: x["data"].get("level", 1), reverse=True)
        rankings["level"] = {"rank": next((i + 1 for i, p in enumerate(level_ranking) if p["user_id"] == user_id), None), "total": len(level_ranking)}
        # Gold ranking
        gold_ranking = sorted(players_list, key=lambda x: x["data"].get("gold", 0), reverse=True)
        rankings["gold"] = {"rank": next((i + 1 for i, p in enumerate(gold_ranking) if p["user_id"] == user_id), None), "total": len(gold_ranking)}
        # PvP ranking
        pvp_ranking = sorted(players_list, key=lambda x: x["data"].get("pvp", {}).get("wins", 0), reverse=True)
        rankings["pvp"] = {"rank": next((i + 1 for i, p in enumerate(pvp_ranking) if p["user_id"] == user_id), None), "total": len(pvp_ranking)}
        # Achievements ranking
        ach_ranking = sorted(players_list, key=lambda x: len(x["data"].get("achievements", [])), reverse=True)
        rankings["achievements"] = {"rank": next((i + 1 for i, p in enumerate(ach_ranking) if p["user_id"] == user_id), None), "total": len(ach_ranking)}
        return rankings
    
    async def _calculate_profile_level(self, achievements: Dict, stats: Dict) -> int:
        """Calculate profile level based on achievements and stats"""
        base_level = 1
        
        # Add levels for achievements
        achievement_points = achievements.get("total_points", 0)
        base_level += achievement_points // 50
        
        # Add levels for combat stats
        combat_stats = stats.get("combat", {})
        base_level += combat_stats.get("battles_won", 0) // 10
        base_level += combat_stats.get("dungeons_completed", 0) // 2
        
        # Add levels for economic stats
        economic_stats = stats.get("economic", {})
        base_level += economic_stats.get("total_gold_earned", 0) // 1000
        
        return min(base_level, 100)  # Cap at level 100
    
    async def _calculate_xp_to_next(self, character: Dict) -> int:
        """Calculate XP needed for next level"""
        current_level = character.get("level", 1)
        current_xp = character.get("xp", 0)
        
        # Simple XP calculation (can be made more complex)
        xp_for_current = (current_level - 1) * 100
        xp_for_next = current_level * 100
        
        return max(0, xp_for_next - (current_xp - xp_for_current))
    
    async def _calculate_days_active(self, character: Dict) -> int:
        """Calculate days since character creation"""
        created_at = character.get("created_at")
        if not created_at:
            return 0
        
        try:
            created_date = datetime.fromisoformat(created_at)
            days_active = (datetime.utcnow() - created_date).days
            return max(1, days_active)
        except:
            return 1
    
    async def check_achievements(self, user_id: int, action: str, **kwargs) -> List[Dict]:
        """Check and award achievements based on player actions"""
        character = await self.character_system.get_character(user_id)
        if not character:
            return []
        
        unlocked_achievements = character.get("achievements", [])
        newly_unlocked = []
        
        # Check various achievement conditions
        if action == "battle_won" and "first_blood" not in unlocked_achievements:
            newly_unlocked.append("first_blood")
        
        if action == "battle_won":
            battles_won = character.get("battles_won", 0)
            if battles_won >= 10 and "monster_hunter" not in unlocked_achievements:
                newly_unlocked.append("monster_hunter")
        
        if action == "gold_earned":
            gold = character.get("gold", 0)
            if gold >= 1000 and "wealthy" not in unlocked_achievements:
                newly_unlocked.append("wealthy")
        
        if action == "skill_learned":
            skills = character.get("skills", [])
            if len(skills) >= 5 and "skill_master" not in unlocked_achievements:
                newly_unlocked.append("skill_master")
        
        if action == "pvp_won":
            pvp_wins = character.get("pvp", {}).get("wins", 0)
            if pvp_wins >= 10 and "pvp_champion" not in unlocked_achievements:
                newly_unlocked.append("pvp_champion")
        
        if action == "faction_joined" and "faction_leader" not in unlocked_achievements:
            # Check if they've contributed enough gold
            faction_contributions = character.get("faction_contributions", 0)
            if faction_contributions >= 500:
                newly_unlocked.append("faction_leader")
        
        if action == "dungeon_completed":
            dungeons_completed = character.get("dungeons_completed", 0)
            if dungeons_completed >= 5 and "dungeon_crawler" not in unlocked_achievements:
                newly_unlocked.append("dungeon_crawler")
        
        # Award newly unlocked achievements
        for achievement_id in newly_unlocked:
            character["achievements"].append(achievement_id)
            
            # Initialize achievement dates if not exists
            if "achievement_dates" not in character:
                character["achievement_dates"] = {}
            
            character["achievement_dates"][achievement_id] = datetime.utcnow().isoformat()
            
            await self.db.save_player(user_id, character)
        
        return [self.achievements.get(ach_id, {}) for ach_id in newly_unlocked]
    
    async def get_leaderboard(self, category: str = "level", limit: int = 10) -> List[Dict]:
        """Get leaderboard for a specific category"""
        players_map = await self.db.load_json_data("players.json")
        if not players_map:
            return []
        players_list = [{"user_id": uid, "data": pdata} for uid, pdata in players_map.items()]
        if category == "level":
            sorted_players = sorted(players_list, key=lambda x: x["data"].get("level", 1), reverse=True)
        elif category == "gold":
            sorted_players = sorted(players_list, key=lambda x: x["data"].get("gold", 0), reverse=True)
        elif category == "pvp":
            sorted_players = sorted(players_list, key=lambda x: x["data"].get("pvp", {}).get("wins", 0), reverse=True)
        elif category == "achievements":
            sorted_players = sorted(players_list, key=lambda x: len(x["data"].get("achievements", [])), reverse=True)
        else:
            return []
        leaderboard: List[Dict] = []
        for i, player in enumerate(sorted_players[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_id": player["user_id"],
                "username": player["data"].get("username", "Unknown"),
                "value": self._get_leaderboard_value(player["data"], category)
            })
        return leaderboard
    
    def _get_leaderboard_value(self, player_data: Dict, category: str) -> int:
        """Get the value for leaderboard ranking"""
        if category == "level":
            return player_data.get("level", 1)
        elif category == "gold":
            return player_data.get("gold", 0)
        elif category == "pvp":
            return player_data.get("pvp", {}).get("wins", 0)
        elif category == "achievements":
            return len(player_data.get("achievements", []))
        return 0
