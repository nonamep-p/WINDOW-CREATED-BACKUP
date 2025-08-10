"""
👤 Player Profile Commands
Ultra-low latency profile management commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.helpers import create_embed

logger = logging.getLogger(__name__)

class ProfilesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="👤 Player Profile")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View player profile"""
        target_user = user or interaction.user
        user_id = target_user.id
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            if user:
                await interaction.response.send_message(f"{user.mention} doesn't have a character yet!", ephemeral=True)
            else:
                await interaction.response.send_message("You need to create a character first! Use `/character`", ephemeral=True)
            return
        
        # Get comprehensive profile
        profile_result = await self.bot.profile_system.get_player_profile(user_id)
        
        if not profile_result["success"]:
            await interaction.response.send_message(f"❌ Failed to load profile: {profile_result['message']}", ephemeral=True)
            return
        
        profile = profile_result["profile"]
        embed = self._create_profile_embed(profile, target_user)
        view = ProfileView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    def _create_profile_embed(self, profile, user):
        """Create comprehensive profile embed"""
        character = profile["character"]
        stats = profile["stats"]
        achievements = profile["achievements"]
        rankings = profile["rankings"]
        
        cls = character.get("character_class", character.get("class", "Adventurer"))
        race = character.get("race", "Human")
        
        embed = create_embed(
            title=f"👤 {character['username']}'s Profile",
            description=f"Level {character.get('level',1)} • {cls} • {race}",
            color=discord.Color.blue()
        )
        
        # Combat stats
        combat_stats = stats["combat"]
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"**Battles:** {combat_stats['total_battles']} ({combat_stats['win_rate']:.1f}% win rate)\n"
                  f"**PvP:** {combat_stats['pvp_wins']}W/{combat_stats['pvp_losses']}L ({combat_stats['pvp_win_rate']:.1f}%)\n"
                  f"**Dungeons:** {combat_stats['dungeons_completed']} completed",
            inline=True
        )
        
        # Economic stats
        economic_stats = stats["economic"]
        embed.add_field(
            name="💰 Economic Stats",
            value=f"**Gold:** {economic_stats['current_gold']:,}\n"
                  f"**Total Earned:** {economic_stats['total_gold_earned']:,}\n"
                  f"**Items Owned:** {economic_stats['items_owned']} ({economic_stats['unique_items']} unique)",
            inline=True
        )
        
        # Progression stats
        progression_stats = stats["progression"]
        embed.add_field(
            name="📈 Progression",
            value=f"**Level:** {progression_stats['level']}\n"
                  f"**XP:** {progression_stats['xp']}/{progression_stats['xp'] + progression_stats['xp_to_next']}\n"
                  f"**Skills:** {progression_stats['skills_learned']} learned\n"
                  f"**Days Active:** {progression_stats['days_active']}",
            inline=True
        )
        
        # Achievements
        embed.add_field(
            name="🏆 Achievements",
            value=f"**Unlocked:** {len(achievements['unlocked'])}/{len(achievements['unlocked']) + len(achievements['locked'])}\n"
                  f"**Points:** {achievements['total_points']}\n"
                  f"**Completion:** {achievements['completion_percentage']:.1f}%",
            inline=True
        )
        
        # Rankings
        embed.add_field(
            name="🏅 Rankings",
            value=f"**Level:** #{rankings.get('level', {}).get('rank', 'N/A')}\n"
                  f"**Gold:** #{rankings.get('gold', {}).get('rank', 'N/A')}\n"
                  f"**PvP:** #{rankings.get('pvp', {}).get('rank', 'N/A')}\n"
                  f"**Achievements:** #{rankings.get('achievements', {}).get('rank', 'N/A')}",
            inline=True
        )
        
        # Base stats
        base_stats = stats["base_stats"]
        embed.add_field(
            name="📊 Base Stats",
            value=f"**HP:** {base_stats.get('hp', 0)}\n"
                  f"**Attack:** {base_stats.get('attack', 0)}\n"
                  f"**Defense:** {base_stats.get('defense', 0)}\n"
                  f"**Speed:** {base_stats.get('speed', 0)}",
            inline=True
        )
        
        embed.set_footer(text=f"Profile Level: {profile['profile_level']} • Last Active: {progression_stats['last_active']}")
        
        return embed

    @app_commands.command(name="profile_achievements", description="🏆 View Achievements")
    async def profile_achievements(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View player achievements"""
        target_user = user or interaction.user
        user_id = target_user.id
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            if user:
                await interaction.response.send_message(f"{user.mention} doesn't have a character yet!", ephemeral=True)
            else:
                await interaction.response.send_message("You need to create a character first! Use `/character`", ephemeral=True)
            return
        
        # Get achievements
        profile_result = await self.bot.profile_system.get_player_profile(user_id)
        
        if not profile_result["success"]:
            await interaction.response.send_message(f"❌ Failed to load achievements: {profile_result['message']}", ephemeral=True)
            return
        
        achievements = profile_result["profile"]["achievements"]
        embed = self._create_achievements_embed(achievements, target_user)
        await interaction.response.send_message(embed=embed)

    def _create_achievements_embed(self, achievements, user):
        """Create achievements embed"""
        embed = create_embed(
            title=f"🏆 {user.display_name}'s Achievements",
            description=f"**{len(achievements['unlocked'])}/{len(achievements['unlocked']) + len(achievements['locked'])}** achievements unlocked",
            color=discord.Color.gold()
        )
        
        # Show unlocked achievements
        if achievements['unlocked']:
            unlocked_text = ""
            for achievement in achievements['unlocked'][:10]:  # Show first 10
                unlocked_text += f"{achievement['icon']} **{achievement['name']}** - {achievement['description']}\n"
            
            if len(achievements['unlocked']) > 10:
                unlocked_text += f"\n... and {len(achievements['unlocked']) - 10} more"
            
            embed.add_field(
                name="✅ Unlocked",
                value=unlocked_text,
                inline=False
            )
        
        # Show some locked achievements (if any)
        if achievements['locked']:
            locked_text = ""
            for achievement in achievements['locked'][:5]:  # Show first 5
                if not achievement.get('secret', False):
                    locked_text += f"🔒 **{achievement['name']}** - {achievement['description']}\n"
            
            if locked_text:
                embed.add_field(
                    name="🔒 Locked",
                    value=locked_text,
                    inline=False
                )
        
        embed.add_field(
            name="📊 Stats",
            value=f"**Total Points:** {achievements['total_points']}\n"
                  f"**Completion:** {achievements['completion_percentage']:.1f}%",
            inline=True
        )
        
        return embed

    @app_commands.command(name="profile_leaderboard", description="🏆 View Leaderboards")
    async def profile_leaderboard(self, interaction: discord.Interaction, category: str = "level"):
        """View leaderboards"""
        # Validate category
        valid_categories = ["level", "gold", "pvp", "achievements"]
        if category not in valid_categories:
            await interaction.response.send_message(f"❌ Invalid category! Valid categories: {', '.join(valid_categories)}", ephemeral=True)
            return
        
        # Get leaderboard
        leaderboard = await self.bot.profile_system.get_leaderboard(category, 10)
        
        if not leaderboard:
            await interaction.response.send_message("No leaderboard data available!", ephemeral=True)
            return
        
        embed = create_embed(
            title=f"🏆 {category.title()} Leaderboard",
            description="Top 10 players",
            color=discord.Color.gold()
        )
        
        for i, player in enumerate(leaderboard, 1):
            embed.add_field(
                name=f"#{i} {player['username']}",
                value=f"**{category.title()}:** {player['value']:,}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

class ProfileView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.primary, emoji="🏆")
    async def view_achievements(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get achievements
        profile_result = await self.bot.profile_system.get_player_profile(self.user_id)
        
        if not profile_result["success"]:
            await interaction.response.send_message(f"❌ Failed to load achievements: {profile_result['message']}", ephemeral=True)
            return
        
        achievements = profile_result["profile"]["achievements"]
        embed = self._create_achievements_embed(achievements)
        await interaction.response.edit_message(embed=embed, view=None)

    def _create_achievements_embed(self, achievements):
        """Create achievements embed"""
        embed = create_embed(
            title="🏆 Your Achievements",
            description=f"**{len(achievements['unlocked'])}/{len(achievements['unlocked']) + len(achievements['locked'])}** achievements unlocked",
            color=discord.Color.gold()
        )
        
        # Show unlocked achievements
        if achievements['unlocked']:
            unlocked_text = ""
            for achievement in achievements['unlocked'][:10]:  # Show first 10
                unlocked_text += f"{achievement['icon']} **{achievement['name']}** - {achievement['description']}\n"
            
            if len(achievements['unlocked']) > 10:
                unlocked_text += f"\n... and {len(achievements['unlocked']) - 10} more"
            
            embed.add_field(
                name="✅ Unlocked",
                value=unlocked_text,
                inline=False
            )
        
        embed.add_field(
            name="📊 Stats",
            value=f"**Total Points:** {achievements['total_points']}\n"
                  f"**Completion:** {achievements['completion_percentage']:.1f}%",
            inline=True
        )
        
        return embed

    @discord.ui.button(label="📊 Recent Activity", style=discord.ButtonStyle.secondary, emoji="📊")
    async def view_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get recent activity
        profile_result = await self.bot.profile_system.get_player_profile(self.user_id)
        
        if not profile_result["success"]:
            await interaction.response.send_message(f"❌ Failed to load activity: {profile_result['message']}", ephemeral=True)
            return
        
        recent_activity = profile_result["profile"]["recent_activity"]
        
        embed = create_embed(
            title="📊 Recent Activity",
            description="Your recent actions and achievements",
            color=discord.Color.blue()
        )
        
        if recent_activity:
            activity_text = ""
            for activity in recent_activity:
                activity_text += f"{activity['icon']} {activity['description']}\n"
            
            embed.add_field(
                name="Recent Actions",
                value=activity_text,
                inline=False
            )
        else:
            embed.add_field(
                name="No Recent Activity",
                value="Start playing to see your activity here!",
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(ProfilesCog(bot))
