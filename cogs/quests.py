import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List
from datetime import datetime, timedelta
import random

from utils.helpers import create_embed, format_number

logger = logging.getLogger(__name__)

class QuestsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="quests", description="View and manage your quests")
    async def quests(self, interaction: discord.Interaction):
        """View and manage quests"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get quests
        quests = await self.bot.quest_system.get_quests(user_id)
        
        embed = self._create_quests_embed(character, quests)
        view = QuestsView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="dailyquests", description="View daily quests")
    async def daily_quests(self, interaction: discord.Interaction):
        """View daily quests"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get daily quests
        daily_quests = await self.bot.quest_system.get_daily_quests(user_id)
        
        embed = self._create_daily_quests_embed(character, daily_quests)
        view = DailyQuestsView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="weeklyquests", description="View weekly quests")
    async def weekly_quests(self, interaction: discord.Interaction):
        """View weekly quests"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get weekly quests
        weekly_quests = await self.bot.quest_system.get_weekly_quests(user_id)
        
        embed = self._create_weekly_quests_embed(character, weekly_quests)
        view = WeeklyQuestsView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    def _create_quests_embed(self, character, quests):
        """Create quests embed"""
        embed = create_embed(
            title=f"📋 {character['username']}'s Quests",
            description="Track your progress and earn rewards!",
            color=discord.Color.blue()
        )
        
        if not quests:
            embed.add_field(name="📋 No Quests", value="Complete activities to unlock quests!", inline=False)
            return embed
        
        # Group quests by type
        daily_quests = [q for q in quests if q.get("type") == "daily"]
        weekly_quests = [q for q in quests if q.get("type") == "weekly"]
        achievement_quests = [q for q in quests if q.get("type") == "achievement"]
        
        # Daily quests
        if daily_quests:
            daily_text = ""
            for quest in daily_quests[:3]:  # Show first 3
                status = "✅" if quest.get("completed", False) else "⏳"
                progress = quest.get("progress", 0)
                target = quest.get("target", 1)
                daily_text += f"{status} **{quest['name']}** - {progress}/{target}\n"
                daily_text += f"   {quest.get('description', 'No description')}\n\n"
            embed.add_field(name="📅 Daily Quests", value=daily_text, inline=False)
        
        # Weekly quests
        if weekly_quests:
            weekly_text = ""
            for quest in weekly_quests[:3]:  # Show first 3
                status = "✅" if quest.get("completed", False) else "⏳"
                progress = quest.get("progress", 0)
                target = quest.get("target", 1)
                weekly_text += f"{status} **{quest['name']}** - {progress}/{target}\n"
                weekly_text += f"   {quest.get('description', 'No description')}\n\n"
            embed.add_field(name="📆 Weekly Quests", value=weekly_text, inline=False)
        
        # Achievement quests
        if achievement_quests:
            achievement_text = ""
            for quest in achievement_quests[:3]:  # Show first 3
                status = "✅" if quest.get("completed", False) else "⏳"
                progress = quest.get("progress", 0)
                target = quest.get("target", 1)
                achievement_text += f"{status} **{quest['name']}** - {progress}/{target}\n"
                achievement_text += f"   {quest.get('description', 'No description')}\n\n"
            embed.add_field(name="🏆 Achievement Quests", value=achievement_text, inline=False)
        
        # Add stats
        total_quests = len(quests)
        completed_quests = len([q for q in quests if q.get("completed", False)])
        completion_rate = (completed_quests / total_quests * 100) if total_quests > 0 else 0
        
        stats_text = f"📊 **Progress:** {completed_quests}/{total_quests} ({completion_rate:.1f}%)\n"
        stats_text += f"🎁 **Rewards Earned:** {sum(q.get('reward_gold', 0) for q in quests if q.get('completed', False))} gold"
        
        embed.add_field(name="📈 Stats", value=stats_text, inline=False)
        
        return embed

    def _create_daily_quests_embed(self, character, daily_quests):
        """Create daily quests embed"""
        embed = create_embed(
            title=f"📅 {character['username']}'s Daily Quests",
            description="Complete daily challenges for rewards!",
            color=discord.Color.green()
        )
        
        if not daily_quests:
            embed.add_field(name="📅 No Daily Quests", value="Daily quests will appear here!", inline=False)
            return embed
        
        for quest in daily_quests:
            status = "✅" if quest.get("completed", False) else "⏳"
            progress = quest.get("progress", 0)
            target = quest.get("target", 1)
            reward_gold = quest.get("reward_gold", 0)
            reward_xp = quest.get("reward_xp", 0)
            
            quest_text = f"{status} **{quest['name']}**\n"
            quest_text += f"📝 {quest.get('description', 'No description')}\n"
            quest_text += f"📊 Progress: {progress}/{target}\n"
            quest_text += f"🎁 Reward: {format_number(reward_gold)} gold, {format_number(reward_xp)} XP\n\n"
            
            embed.add_field(name=f"📅 Daily Quest", value=quest_text, inline=False)
        
        return embed

    def _create_weekly_quests_embed(self, character, weekly_quests):
        """Create weekly quests embed"""
        embed = create_embed(
            title=f"📆 {character['username']}'s Weekly Quests",
            description="Complete weekly challenges for big rewards!",
            color=discord.Color.purple()
        )
        
        if not weekly_quests:
            embed.add_field(name="📆 No Weekly Quests", value="Weekly quests will appear here!", inline=False)
            return embed
        
        for quest in weekly_quests:
            status = "✅" if quest.get("completed", False) else "⏳"
            progress = quest.get("progress", 0)
            target = quest.get("target", 1)
            reward_gold = quest.get("reward_gold", 0)
            reward_xp = quest.get("reward_xp", 0)
            
            quest_text = f"{status} **{quest['name']}**\n"
            quest_text += f"📝 {quest.get('description', 'No description')}\n"
            quest_text += f"📊 Progress: {progress}/{target}\n"
            quest_text += f"🎁 Reward: {format_number(reward_gold)} gold, {format_number(reward_xp)} XP\n\n"
            
            embed.add_field(name=f"📆 Weekly Quest", value=quest_text, inline=False)
        
        return embed

class QuestsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📅 Daily", style=discord.ButtonStyle.primary, emoji="📅")
    async def daily_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        daily_quests = await self.bot.quest_system.get_daily_quests(self.user_id)
        embed = self._create_daily_quests_embed(daily_quests)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📆 Weekly", style=discord.ButtonStyle.success, emoji="📆")
    async def weekly_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        weekly_quests = await self.bot.quest_system.get_weekly_quests(self.user_id)
        embed = self._create_weekly_quests_embed(weekly_quests)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def achievement_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        achievement_quests = await self.bot.quest_system.get_achievement_quests(self.user_id)
        embed = self._create_achievement_quests_embed(achievement_quests)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎁 Claim Rewards", style=discord.ButtonStyle.danger, emoji="🎁")
    async def claim_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        result = await self.bot.quest_system.claim_completed_rewards(self.user_id)
        
        if result["success"]:
            rewards = result["rewards"]
            embed = create_embed(
                title="🎁 Quest Rewards Claimed!",
                description="You received:",
                color=discord.Color.gold()
            )
            
            rewards_text = ""
            if rewards.get("gold", 0) > 0:
                rewards_text += f"💰 **{format_number(rewards['gold'])} Gold**\n"
            if rewards.get("xp", 0) > 0:
                rewards_text += f"⭐ **{format_number(rewards['xp'])} XP**\n"
            if rewards.get("items"):
                for item in rewards["items"]:
                    rewards_text += f"📦 **{item['name']}** x{item['quantity']}\n"
            
            embed.add_field(name="🎁 Rewards", value=rewards_text, inline=False)
        else:
            embed = create_embed(
                title="❌ No Rewards",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _create_daily_quests_embed(self, daily_quests):
        """Create daily quests embed"""
        embed = create_embed(
            title="📅 Daily Quests",
            description="Complete daily challenges for rewards!",
            color=discord.Color.green()
        )
        
        if not daily_quests:
            embed.add_field(name="📅 No Daily Quests", value="Daily quests will appear here!", inline=False)
            return embed
        
        for quest in daily_quests:
            status = "✅" if quest.get("completed", False) else "⏳"
            progress = quest.get("progress", 0)
            target = quest.get("target", 1)
            
            quest_text = f"{status} **{quest['name']}**\n"
            quest_text += f"📝 {quest.get('description', 'No description')}\n"
            quest_text += f"📊 Progress: {progress}/{target}\n"
            
            embed.add_field(name=f"📅 Daily Quest", value=quest_text, inline=False)
        
        return embed

    def _create_weekly_quests_embed(self, weekly_quests):
        """Create weekly quests embed"""
        embed = create_embed(
            title="📆 Weekly Quests",
            description="Complete weekly challenges for big rewards!",
            color=discord.Color.purple()
        )
        
        if not weekly_quests:
            embed.add_field(name="📆 No Weekly Quests", value="Weekly quests will appear here!", inline=False)
            return embed
        
        for quest in weekly_quests:
            status = "✅" if quest.get("completed", False) else "⏳"
            progress = quest.get("progress", 0)
            target = quest.get("target", 1)
            
            quest_text = f"{status} **{quest['name']}**\n"
            quest_text += f"📝 {quest.get('description', 'No description')}\n"
            quest_text += f"📊 Progress: {progress}/{target}\n"
            
            embed.add_field(name=f"📆 Weekly Quest", value=quest_text, inline=False)
        
        return embed

    def _create_achievement_quests_embed(self, achievement_quests):
        """Create achievement quests embed"""
        embed = create_embed(
            title="🏆 Achievement Quests",
            description="Complete achievements for special rewards!",
            color=discord.Color.gold()
        )
        
        if not achievement_quests:
            embed.add_field(name="🏆 No Achievement Quests", value="Achievement quests will appear here!", inline=False)
            return embed
        
        for quest in achievement_quests:
            status = "✅" if quest.get("completed", False) else "⏳"
            progress = quest.get("progress", 0)
            target = quest.get("target", 1)
            
            quest_text = f"{status} **{quest['name']}**\n"
            quest_text += f"📝 {quest.get('description', 'No description')}\n"
            quest_text += f"📊 Progress: {progress}/{target}\n"
            
            embed.add_field(name=f"🏆 Achievement Quest", value=quest_text, inline=False)
        
        return embed

class DailyQuestsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🎁 Claim Rewards", style=discord.ButtonStyle.primary, emoji="🎁")
    async def claim_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        result = await self.bot.quest_system.claim_daily_rewards(self.user_id)
        
        if result["success"]:
            rewards = result["rewards"]
            embed = create_embed(
                title="🎁 Daily Quest Rewards Claimed!",
                description="You received:",
                color=discord.Color.gold()
            )
            
            rewards_text = ""
            if rewards.get("gold", 0) > 0:
                rewards_text += f"💰 **{format_number(rewards['gold'])} Gold**\n"
            if rewards.get("xp", 0) > 0:
                rewards_text += f"⭐ **{format_number(rewards['xp'])} XP**\n"
            if rewards.get("items"):
                for item in rewards["items"]:
                    rewards_text += f"📦 **{item['name']}** x{item['quantity']}\n"
            
            embed.add_field(name="🎁 Rewards", value=rewards_text, inline=False)
        else:
            embed = create_embed(
                title="❌ No Rewards",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class WeeklyQuestsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🎁 Claim Rewards", style=discord.ButtonStyle.primary, emoji="🎁")
    async def claim_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        result = await self.bot.quest_system.claim_weekly_rewards(self.user_id)
        
        if result["success"]:
            rewards = result["rewards"]
            embed = create_embed(
                title="🎁 Weekly Quest Rewards Claimed!",
                description="You received:",
                color=discord.Color.gold()
            )
            
            rewards_text = ""
            if rewards.get("gold", 0) > 0:
                rewards_text += f"💰 **{format_number(rewards['gold'])} Gold**\n"
            if rewards.get("xp", 0) > 0:
                rewards_text += f"⭐ **{format_number(rewards['xp'])} XP**\n"
            if rewards.get("items"):
                for item in rewards["items"]:
                    rewards_text += f"📦 **{item['name']}** x{item['quantity']}\n"
            
            embed.add_field(name="🎁 Rewards", value=rewards_text, inline=False)
        else:
            embed = create_embed(
                title="❌ No Rewards",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(QuestsCog(bot))
