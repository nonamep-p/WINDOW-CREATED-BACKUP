import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from enum import Enum
import discord

logger = logging.getLogger(__name__)

class GuildRole(Enum):
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"
    RECRUIT = "recruit"

class GuildActivity(Enum):
    GUILD_RAID = "guild_raid"
    GUILD_QUEST = "guild_quest"
    GUILD_WAR = "guild_war"
    GUILD_CRAFTING = "guild_crafting"
    GUILD_TRADING = "guild_trading"

class GuildSystem:
    def __init__(self, db, character_system=None, economy_system=None):
        self.db = db
        self.character_system = character_system
        self.economy_system = economy_system
        self.active_guild_activities: Dict[str, Dict] = {}
        
        # Guild level requirements and bonuses
        self.guild_levels = {
            1: {"xp_required": 0, "member_limit": 10, "bonuses": {}},
            2: {"xp_required": 1000, "member_limit": 15, "bonuses": {"xp_bonus": 0.05}},
            3: {"xp_required": 2500, "member_limit": 20, "bonuses": {"xp_bonus": 0.10, "gold_bonus": 0.05}},
            4: {"xp_required": 5000, "member_limit": 25, "bonuses": {"xp_bonus": 0.15, "gold_bonus": 0.10}},
            5: {"xp_required": 10000, "member_limit": 30, "bonuses": {"xp_bonus": 0.20, "gold_bonus": 0.15, "crafting_bonus": 0.10}}
        }

    async def create_guild(self, leader_id: int, guild_name: str, guild_description: str = "") -> Dict:
        """Create a new guild"""
        # Check if user is already in a guild
        existing_guild = await self.get_user_guild(leader_id)
        if existing_guild:
            return {"success": False, "message": "You are already in a guild!"}

        # Check if guild name is taken
        existing_guilds = await self.db.get_guilds()
        for guild in existing_guilds:
            if guild["name"].lower() == guild_name.lower():
                return {"success": False, "message": "Guild name already taken!"}

        # Create guild
        guild_id = f"guild_{int(datetime.utcnow().timestamp())}"
        guild_data = {
            "guild_id": guild_id,
            "name": guild_name,
            "description": guild_description,
            "leader_id": leader_id,
            "level": 1,
            "xp": 0,
            "gold": 0,
            "members": [{
                "user_id": leader_id,
                "role": GuildRole.LEADER.value,
                "joined_at": datetime.utcnow().isoformat(),
                "contribution_xp": 0,
                "contribution_gold": 0
            }],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "settings": {
                "auto_accept": False,
                "min_level_requirement": 1,
                "guild_announcements": True
            },
            "achievements": [],
            "guild_bank": {
                "gold": 0,
                "items": []
            },
            "guild_skills": {
                "combat_bonus": 0,
                "crafting_bonus": 0,
                "trading_bonus": 0,
                "xp_bonus": 0
            }
        }

        await self.db.save_guild(guild_data)
        
        # Update user's guild info
        await self.db.update_player_guild(leader_id, guild_id)
        
        return {"success": True, "guild": guild_data, "message": f"Guild '{guild_name}' created successfully!"}

    async def join_guild(self, user_id: int, guild_id: str) -> Dict:
        """Join a guild"""
        # Check if user is already in a guild
        existing_guild = await self.get_user_guild(user_id)
        if existing_guild:
            return {"success": False, "message": "You are already in a guild!"}

        guild = await self.db.get_guild(guild_id)
        if not guild:
            return {"success": False, "message": "Guild not found!"}

        # Check member limit
        member_limit = self.guild_levels[guild["level"]]["member_limit"]
        if len(guild["members"]) >= member_limit:
            return {"success": False, "message": "Guild is full!"}

        # Check level requirement
        character = await self.character_system.get_character(user_id)
        if character["level"] < guild["settings"]["min_level_requirement"]:
            return {"success": False, "message": f"Minimum level {guild['settings']['min_level_requirement']} required!"}

        # Add member
        new_member = {
            "user_id": user_id,
            "role": GuildRole.RECRUIT.value,
            "joined_at": datetime.utcnow().isoformat(),
            "contribution_xp": 0,
            "contribution_gold": 0
        }
        guild["members"].append(new_member)
        guild["last_activity"] = datetime.utcnow().isoformat()

        await self.db.save_guild(guild)
        await self.db.update_player_guild(user_id, guild_id)

        return {"success": True, "guild": guild, "message": f"Welcome to {guild['name']}!"}

    async def leave_guild(self, user_id: int) -> Dict:
        """Leave the current guild"""
        guild = await self.get_user_guild(user_id)
        if not guild:
            return {"success": False, "message": "You are not in a guild!"}

        # Remove member
        guild["members"] = [m for m in guild["members"] if m["user_id"] != user_id]
        guild["last_activity"] = datetime.utcnow().isoformat()

        # If leader leaves, transfer leadership or disband
        if guild["leader_id"] == user_id:
            if len(guild["members"]) > 0:
                # Transfer to highest ranking officer
                officers = [m for m in guild["members"] if m["role"] == GuildRole.OFFICER.value]
                if officers:
                    new_leader = officers[0]
                    guild["leader_id"] = new_leader["user_id"]
                    new_leader["role"] = GuildRole.LEADER.value
                else:
                    # Transfer to first member
                    guild["leader_id"] = guild["members"][0]["user_id"]
                    guild["members"][0]["role"] = GuildRole.LEADER.value
            else:
                # Disband guild
                await self.db.delete_guild(guild["guild_id"])
                await self.db.update_player_guild(user_id, None)
                return {"success": True, "message": "Guild disbanded due to no members."}

        await self.db.save_guild(guild)
        await self.db.update_player_guild(user_id, None)

        return {"success": True, "message": f"You left {guild['name']}."}

    async def get_user_guild(self, user_id: int) -> Optional[Dict]:
        """Get the guild a user belongs to"""
        guilds = await self.db.get_guilds()
        for guild in guilds:
            for member in guild["members"]:
                if member["user_id"] == user_id:
                    return guild
        return None

    async def get_guild_member(self, guild_id: str, user_id: int) -> Optional[Dict]:
        """Get a specific member from a guild"""
        guild = await self.db.get_guild(guild_id)
        if not guild:
            return None
        
        for member in guild["members"]:
            if member["user_id"] == user_id:
                return member
        return None

    async def promote_member(self, guild_id: str, user_id: int, promoter_id: int) -> Dict:
        """Promote a guild member"""
        guild = await self.db.get_guild(guild_id)
        if not guild:
            return {"success": False, "message": "Guild not found!"}

        # Check permissions
        promoter = await self.get_guild_member(guild_id, promoter_id)
        if not promoter or promoter["role"] not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            return {"success": False, "message": "You don't have permission to promote members!"}

        target_member = await self.get_guild_member(guild_id, user_id)
        if not target_member:
            return {"success": False, "message": "Member not found!"}

        # Promote member
        if target_member["role"] == GuildRole.RECRUIT.value:
            target_member["role"] = GuildRole.MEMBER.value
        elif target_member["role"] == GuildRole.MEMBER.value:
            target_member["role"] = GuildRole.OFFICER.value
        else:
            return {"success": False, "message": "Member is already at maximum rank!"}

        guild["last_activity"] = datetime.utcnow().isoformat()
        await self.db.save_guild(guild)

        return {"success": True, "message": f"{target_member['user_id']} has been promoted!"}

    async def demote_member(self, guild_id: str, user_id: int, demoter_id: int) -> Dict:
        """Demote a guild member"""
        guild = await self.db.get_guild(guild_id)
        if not guild:
            return {"success": False, "message": "Guild not found!"}

        # Check permissions
        demoter = await self.get_guild_member(guild_id, demoter_id)
        if not demoter or demoter["role"] not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            return {"success": False, "message": "You don't have permission to demote members!"}

        target_member = await self.get_guild_member(guild_id, user_id)
        if not target_member:
            return {"success": False, "message": "Member not found!"}

        # Demote member
        if target_member["role"] == GuildRole.OFFICER.value:
            target_member["role"] = GuildRole.MEMBER.value
        elif target_member["role"] == GuildRole.MEMBER.value:
            target_member["role"] = GuildRole.RECRUIT.value
        else:
            return {"success": False, "message": "Member is already at minimum rank!"}

        guild["last_activity"] = datetime.utcnow().isoformat()
        await self.db.save_guild(guild)

        return {"success": True, "message": f"{target_member['user_id']} has been demoted!"}

    async def start_guild_activity(self, guild_id: str, activity_type: GuildActivity, initiator_id: int) -> Dict:
        """Start a guild activity (raid, quest, etc.)"""
        guild = await self.db.get_guild(guild_id)
        if not guild:
            return {"success": False, "message": "Guild not found!"}

        # Check if activity is already active
        activity_id = f"{guild_id}_{activity_type.value}_{int(datetime.utcnow().timestamp())}"
        if activity_id in self.active_guild_activities:
            return {"success": False, "message": "Guild activity already in progress!"}

        # Check permissions
        initiator = await self.get_guild_member(guild_id, initiator_id)
        if not initiator or initiator["role"] not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            return {"success": False, "message": "You don't have permission to start guild activities!"}

        # Create activity
        activity_data = {
            "activity_id": activity_id,
            "guild_id": guild_id,
            "type": activity_type.value,
            "initiator_id": initiator_id,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=1),
            "participants": [initiator_id],
            "progress": 0,
            "rewards": {},
            "status": "active"
        }

        # Set activity-specific data
        if activity_type == GuildActivity.GUILD_RAID:
            activity_data.update({
                "boss": self._generate_guild_boss(guild["level"]),
                "target_damage": 10000 * len(guild["members"]),
                "current_damage": 0
            })
        elif activity_type == GuildActivity.GUILD_QUEST:
            activity_data.update({
                "quest": self._generate_guild_quest(guild["level"]),
                "target_progress": 100,
                "current_progress": 0
            })

        self.active_guild_activities[activity_id] = activity_data

        return {"success": True, "activity": activity_data, "message": f"Guild {activity_type.value.replace('_', ' ')} started!"}

    async def participate_in_guild_activity(self, activity_id: str, user_id: int, contribution: Dict) -> Dict:
        """Participate in an active guild activity"""
        activity = self.active_guild_activities.get(activity_id)
        if not activity:
            return {"success": False, "message": "Activity not found!"}

        if activity["status"] != "active":
            return {"success": False, "message": "Activity has ended!"}

        # Check if user is in the guild
        guild = await self.db.get_guild(activity["guild_id"])
        member = await self.get_guild_member(activity["guild_id"], user_id)
        if not member:
            return {"success": False, "message": "You must be a guild member to participate!"}

        # Add contribution based on activity type
        if activity["type"] == GuildActivity.GUILD_RAID.value:
            damage = contribution.get("damage", 0)
            activity["current_damage"] += damage
            activity["progress"] = min(100, (activity["current_damage"] / activity["target_damage"]) * 100)

        elif activity["type"] == GuildActivity.GUILD_QUEST.value:
            progress = contribution.get("progress", 0)
            activity["current_progress"] += progress
            activity["progress"] = min(100, (activity["current_progress"] / activity["target_progress"]) * 100)

        # Add participant if not already participating
        if user_id not in activity["participants"]:
            activity["participants"].append(user_id)

        # Check if activity is complete
        if activity["progress"] >= 100:
            await self._complete_guild_activity(activity_id)

        return {"success": True, "activity": activity, "message": "Contribution recorded!"}

    async def _complete_guild_activity(self, activity_id: str):
        """Complete a guild activity and distribute rewards"""
        activity = self.active_guild_activities[activity_id]
        guild = await self.db.get_guild(activity["guild_id"])

        # Calculate rewards
        base_reward = 100 * len(activity["participants"])
        guild_xp = base_reward * 2
        guild_gold = base_reward

        # Add to guild
        guild["xp"] += guild_xp
        guild["gold"] += guild_gold
        guild["last_activity"] = datetime.utcnow().isoformat()

        # Check for level up
        await self._check_guild_level_up(guild)

        # Distribute individual rewards
        individual_reward = base_reward // len(activity["participants"])
        for user_id in activity["participants"]:
            member = await self.get_guild_member(activity["guild_id"], user_id)
            if member:
                member["contribution_xp"] += individual_reward
                member["contribution_gold"] += individual_reward

        activity["status"] = "completed"
        activity["rewards"] = {
            "guild_xp": guild_xp,
            "guild_gold": guild_gold,
            "individual_reward": individual_reward
        }

        await self.db.save_guild(guild)

    async def _check_guild_level_up(self, guild: Dict):
        """Check if guild can level up"""
        current_level = guild["level"]
        current_xp = guild["xp"]

        for level, requirements in self.guild_levels.items():
            if level > current_level and current_xp >= requirements["xp_required"]:
                guild["level"] = level
                guild["last_activity"] = datetime.utcnow().isoformat()
                
                # Apply level bonuses
                bonuses = requirements["bonuses"]
                for bonus_type, value in bonuses.items():
                    guild["guild_skills"][bonus_type] = value

                await self.db.save_guild(guild)
                return {"success": True, "message": f"Guild leveled up to level {level}!"}

        return {"success": False, "message": "Guild cannot level up yet."}

    def _generate_guild_boss(self, guild_level: int) -> Dict:
        """Generate a guild boss based on guild level"""
        boss_templates = {
            "dragon": {"name": "Ancient Dragon", "hp": 50000, "attack": 500, "defense": 200},
            "demon": {"name": "Infernal Demon", "hp": 40000, "attack": 600, "defense": 150},
            "titan": {"name": "Crystal Titan", "hp": 60000, "attack": 400, "defense": 300}
        }

        boss_type = random.choice(list(boss_templates.keys()))
        boss = boss_templates[boss_type].copy()
        
        # Scale with guild level
        boss["hp"] *= (1 + guild_level * 0.2)
        boss["attack"] *= (1 + guild_level * 0.1)
        boss["defense"] *= (1 + guild_level * 0.1)

        return boss

    def _generate_guild_quest(self, guild_level: int) -> Dict:
        """Generate a guild quest based on guild level"""
        quest_templates = [
            {"name": "Monster Hunt", "description": "Defeat powerful monsters", "type": "combat"},
            {"name": "Resource Gathering", "description": "Collect rare materials", "type": "gathering"},
            {"name": "Dungeon Exploration", "description": "Explore dangerous dungeons", "type": "exploration"}
        ]

        quest = random.choice(quest_templates).copy()
        quest["difficulty"] = guild_level
        quest["reward_multiplier"] = 1 + (guild_level * 0.1)

        return quest

    def get_guild_embed(self, guild: Dict) -> Dict:
        """Generate guild information embed"""
        member_count = len(guild["members"])
        member_limit = self.guild_levels[guild["level"]]["member_limit"]
        
        # Calculate total contributions
        total_xp_contribution = sum(m["contribution_xp"] for m in guild["members"])
        total_gold_contribution = sum(m["contribution_gold"] for m in guild["members"])

        # Get role counts
        role_counts = {}
        for member in guild["members"]:
            role = member["role"]
            role_counts[role] = role_counts.get(role, 0) + 1

        embed_data = {
            "title": f"🏰 {guild['name']} (Level {guild['level']})",
            "description": guild.get("description", "No description"),
            "color": discord.Color.gold(),
            "fields": [
                {
                    "name": "📊 Guild Stats",
                    "value": f"Members: {member_count}/{member_limit}\n"
                            f"XP: {guild['xp']:,}\n"
                            f"Gold: {guild['gold']:,}\n"
                            f"Created: {guild['created_at'][:10]}",
                    "inline": True
                },
                {
                    "name": "👥 Members",
                    "value": f"Leader: 1\n"
                            f"Officers: {role_counts.get('officer', 0)}\n"
                            f"Members: {role_counts.get('member', 0)}\n"
                            f"Recruits: {role_counts.get('recruit', 0)}",
                    "inline": True
                },
                {
                    "name": "🎯 Guild Bonuses",
                    "value": f"XP Bonus: +{guild['guild_skills']['xp_bonus']*100:.0f}%\n"
                            f"Gold Bonus: +{guild['guild_skills'].get('gold_bonus', 0)*100:.0f}%\n"
                            f"Combat Bonus: +{guild['guild_skills']['combat_bonus']*100:.0f}%\n"
                            f"Crafting Bonus: +{guild['guild_skills']['crafting_bonus']*100:.0f}%",
                    "inline": True
                }
            ]
        }

        return embed_data
