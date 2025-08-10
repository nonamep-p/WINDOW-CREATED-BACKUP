"""
⚔️ PvP Arena Commands
Ultra-low latency competitive combat commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.helpers import create_embed

logger = logging.getLogger(__name__)

class PvPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pvp", description="PvP Arena - Challenge other players!")
    async def pvp(self, interaction: discord.Interaction):
        """Main PvP command"""
        user_id = interaction.user.id
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            await interaction.response.send_message("You need to create a character first! Use `/character`", ephemeral=True)
            return
        
        # Show PvP menu
        embed = self._create_pvp_embed(character)
        view = PvPView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="challenge", description="Challenge another player to PvP")
    async def challenge(self, interaction: discord.Interaction, target: discord.Member):
        """Challenge another player to PvP"""
        challenger_id = interaction.user.id
        target_id = target.id
        
        if challenger_id == target_id:
            await interaction.response.send_message("You cannot challenge yourself!", ephemeral=True)
            return
        
        result = await self.bot.pvp_system.challenge_player(challenger_id, target_id)
        
        if result["success"]:
            embed = create_embed(
                title="⚔️ PvP Challenge Sent!",
                description=f"**{interaction.user.display_name}** has challenged **{target.display_name}** to a PvP match!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Challenge ID", value=result["match_id"], inline=False)
            embed.add_field(name="Instructions", value=f"{target.mention} can accept the challenge with `/accept {result['match_id']}`", inline=False)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ Challenge failed: {result['message']}", ephemeral=True)

    @app_commands.command(name="accept", description="Accept a PvP challenge")
    async def accept(self, interaction: discord.Interaction, match_id: str):
        """Accept a PvP challenge"""
        target_id = interaction.user.id
        
        result = await self.bot.pvp_system.accept_challenge(target_id, match_id)
        
        if result["success"]:
            embed = create_embed(
                title="⚔️ PvP Challenge Accepted!",
                description="The PvP match has begun!",
                color=discord.Color.green()
            )
            embed.add_field(name="Match ID", value=match_id, inline=False)
            embed.add_field(name="Status", value="Active", inline=False)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ Failed to accept challenge: {result['message']}", ephemeral=True)

    @app_commands.command(name="arena", description="View PvP arena rankings")
    async def arena(self, interaction: discord.Interaction):
        """View PvP arena rankings"""
        # Get all players and sort by PvP wins
        all_players = await self.bot.db.get_all_players()
        
        if not all_players:
            await interaction.response.send_message("No players found!", ephemeral=True)
            return
        
        # all_players is a list of player dicts; sort by PvP wins (descending)
        sorted_players = sorted(
            all_players,
            key=lambda x: x.get("pvp", {}).get("rating", 1000),
            reverse=True
        )
        
        embed = create_embed(
            title="🏆 PvP Arena Rankings",
            description="Top PvP fighters in the realm",
            color=discord.Color.gold()
        )
        
        for i, player_data in enumerate(sorted_players[:10], 1):
            pvp_stats = player_data.get("pvp", {})
            wins = pvp_stats.get("wins", 0)
            losses = pvp_stats.get("losses", 0)
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0
            
            embed.add_field(
                name=f"#{i} {player_data['username']}",
                value=f"🏆 {wins} wins • 💀 {losses} losses • 📊 {win_rate:.1f}% win rate",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    def _create_pvp_embed(self, character):
        """Create PvP status embed"""
        pvp_stats = character.get("pvp", {})
        wins = pvp_stats.get("wins", 0)
        losses = pvp_stats.get("losses", 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        embed = create_embed(
            title="⚔️ PvP Arena",
            description=f"Welcome to the arena, **{character['username']}**!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🏆 Your PvP Stats",
            value=f"**Wins:** {wins}\n**Losses:** {losses}\n**Win Rate:** {win_rate:.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Available Actions",
            value="• `/challenge @player` - Challenge someone\n• `/arena` - View rankings\n• `/accept <id>` - Accept challenge",
            inline=True
        )
        
        return embed

class PvPView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🏆 Rankings", style=discord.ButtonStyle.primary, emoji="🏆")
    async def view_rankings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get all players and sort by PvP wins
        all_players = await self.bot.db.get_all_players()
        
        if not all_players:
            await interaction.response.send_message("No players found!", ephemeral=True)
            return
            
        # all_players is a list of player dicts; sort by PvP wins (descending)
        sorted_players = sorted(
            all_players,
            key=lambda p: p.get("pvp", {}).get("wins", 0),
            reverse=True
        )
            
        embed = create_embed(
            title="🏆 PvP Arena Rankings",
            description="Top PvP fighters in the realm",
            color=discord.Color.gold()
        )
            
        for i, player_data in enumerate(sorted_players[:10], 1):
            pvp_stats = player_data.get("pvp", {})
            wins = pvp_stats.get("wins", 0)
            losses = pvp_stats.get("losses", 0)
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0
            
            embed.add_field(
                name=f"#{i} {player_data['username']}",
                value=f"🏆 {wins} wins • 💀 {losses} losses • 📊 {win_rate:.1f}% win rate",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚔️ Active Matches", style=discord.ButtonStyle.success, emoji="⚔️")
    async def view_matches(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        matches = await self.bot.pvp_system.get_player_matches(self.user_id)
        
        if not matches:
            await interaction.response.send_message("You have no active PvP matches!", ephemeral=True)
            return
        
        embed = create_embed(
            title="⚔️ Your PvP Matches",
            description=f"You have {len(matches)} active match(es)",
            color=discord.Color.blue()
        )
        
        for match in matches[:5]:  # Show first 5 matches
            status = match["status"]
            status_emoji = "🟢" if status == "active" else "🟡" if status == "pending" else "🔴"
            
            embed.add_field(
                name=f"{status_emoji} Match {match['match_id'][:8]}",
                value=f"**Status:** {status.title()}\n**Rounds:** {match['current_round']}/{match['max_rounds']}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PvPCog(bot))

