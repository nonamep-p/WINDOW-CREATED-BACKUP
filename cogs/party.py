"""
👥 Party System Commands
Ultra-low latency party management commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.helpers import create_embed

logger = logging.getLogger(__name__)

class PartyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="party", description="👥 Party Management")
    async def party(self, interaction: discord.Interaction):
        """Main party command"""
        user_id = interaction.user.id
        
        # Acknowledge early to avoid token expiry
        try:
            await interaction.response.defer(ephemeral=False)
        except Exception:
            pass
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            await interaction.followup.send("You need to create a character first! Use `/character`", ephemeral=True)
            return
        
        # Show party interface
        embed = self._create_party_embed(character)
        current_party = await self.bot.party_system.get_player_party(user_id)
        if current_party:
            # Offer quick actions
            v = discord.ui.View()
            info = discord.ui.Button(label="View Info", style=discord.ButtonStyle.secondary, emoji="📊")
            leave = discord.ui.Button(label="Leave Party", style=discord.ButtonStyle.danger, emoji="🚪")
            async def info_cb(i: discord.Interaction):
                if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                emb = create_embed(title=f"📊 {current_party['name']}", description="Party information and settings", color=discord.Color.blue())
                emb.add_field(name="👥 Members", value=f"**{len(current_party['members'])}/{current_party['max_members']}** members", inline=True)
                emb.add_field(name="⚙️ Settings", value=f"**XP Split:** {current_party['settings']['xp_split']}\n**Loot Split:** {current_party['settings']['loot_split']}", inline=True)
                await i.response.edit_message(embed=emb, view=None)
            async def leave_cb(i: discord.Interaction):
                if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                res = await self.bot.party_system.leave_party(user_id)
                if res.get("success"):
                    await i.response.edit_message(embed=create_embed(title="👋 Left Party", description=res.get("message",""), color=discord.Color.orange()), view=None)
                else:
                    await i.response.send_message(res.get("message","Failed"), ephemeral=True)
            info.callback = info_cb; leave.callback = leave_cb
            v.add_item(info); v.add_item(leave)
            await interaction.followup.send(create_embed(title="⚠️ Already in a Party", description="You are already in a party. Manage it below.", color=discord.Color.orange()), view=v)
            return
        view = PartyView(self.bot, user_id, in_party=False)
        await interaction.followup.send(embed=embed, view=view)

    def _create_party_embed(self, character):
        """Create party status embed"""
        embed = create_embed(
            title="👥 Party System",
            description=f"Welcome to the party system, **{character['username']}**!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎯 Party Features",
            value="• Create parties with up to 4 players\n• Shared XP and loot distribution\n• Cooperative combat with scaled monsters\n• Party settings and management",
            inline=False
        )
        
        return embed

class PartyView(discord.ui.View):
    def __init__(self, bot, user_id: int, in_party: bool):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.in_party = in_party
        if not in_party:
            self.add_item(self._make_create_button())
        else:
            self.add_item(self._make_invite_button())
            self.add_item(self._make_start_combat_button())
            self.add_item(self._make_info_button())

    def _make_create_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="🏗️ Create Party", style=discord.ButtonStyle.primary, emoji="🏗️")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            current_party = await self.bot.party_system.get_player_party(self.user_id)
            if current_party:
                await interaction.response.send_message("You are already in a party!", ephemeral=True)
                return
            result = await self.bot.party_system.create_party(self.user_id)
            if result["success"]:
                emb = create_embed(title="🎉 Party Created!", description=result["message"], color=discord.Color.green())
                emb.add_field(name="Party Name", value=result["party"]["name"], inline=False)
                emb.add_field(name="Members", value=f"1/{result['party']['max_members']}", inline=True)
                await interaction.response.edit_message(embed=emb, view=None)
            else:
                await interaction.response.send_message(f"❌ Failed to create party: {result['message']}", ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_invite_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="📨 Invite Player", style=discord.ButtonStyle.success, emoji="📨")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            current_party = await self.bot.party_system.get_player_party(self.user_id)
            if not current_party:
                await interaction.response.send_message("You must be in a party to invite players!", ephemeral=True)
                return
            if current_party["leader_id"] != self.user_id:
                await interaction.response.send_message("Only the party leader can invite players!", ephemeral=True)
                return
            # Build member select from guild
            if not interaction.guild:
                await interaction.response.send_message("Invites require a guild (server) context.", ephemeral=True)
                return
            options = []
            for m in interaction.guild.members[:25]:
                if m.bot or m.id == self.user_id: continue
                options.append(discord.SelectOption(label=m.display_name, value=str(m.id)))
            if not options:
                await interaction.response.send_message("No members to invite.", ephemeral=True)
                return
            select = discord.ui.Select(placeholder="Select a member to invite...", min_values=1, max_values=1, options=options)
            async def select_cb(i: discord.Interaction):
                if i.user.id != self.user_id:
                    await i.response.send_message("This is not for you!", ephemeral=True)
                    return
                target_id = int(select.values[0])
                res = await self.bot.party_system.invite_player(self.user_id, target_id)
                if res["success"]:
                    invite_id = res["invite_id"]
                    # Post accept button for target
                    accept_view = PartyInviteAcceptView(self.bot, invite_id, target_id)
                    await i.response.send_message(f"📨 Invite sent to <@{target_id}>.", ephemeral=True)
                    await interaction.followup.send(content=f"<@{target_id}> you have been invited to a party.", view=accept_view)
                else:
                    await i.response.send_message(f"❌ {res['message']}", ephemeral=True)
            select.callback = select_cb
            v = discord.ui.View(); v.add_item(select)
            await interaction.response.send_message("Pick a member:", view=v, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_start_combat_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="⚔️ Start Combat", style=discord.ButtonStyle.danger, emoji="⚔️")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            current_party = await self.bot.party_system.get_player_party(self.user_id)
            if not current_party:
                await interaction.response.send_message("You must be in a party to start combat!", ephemeral=True)
                return
            await interaction.response.send_message("⚔️ Party combat coming soon.", ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_info_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="📊 Party Info", style=discord.ButtonStyle.secondary, emoji="📊")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            current_party = await self.bot.party_system.get_player_party(self.user_id)
            if not current_party:
                await interaction.response.send_message("You are not in a party!", ephemeral=True)
                return
            emb = create_embed(title=f"📊 {current_party['name']}", description="Party information and settings", color=discord.Color.blue())
            emb.add_field(name="👥 Members", value=f"**{len(current_party['members'])}/{current_party['max_members']}** members", inline=True)
            emb.add_field(name="⚙️ Settings", value=f"**XP Split:** {current_party['settings']['xp_split']}\n**Loot Split:** {current_party['settings']['loot_split']}", inline=True)
            await interaction.response.send_message(embed=emb, ephemeral=True)
        btn.callback = on_click
        return btn

class PartyInviteAcceptView(discord.ui.View):
    def __init__(self, bot, invite_id: str, target_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.invite_id = invite_id
        self.target_id = target_id
        self.add_item(self._make_accept_button())

    def _make_accept_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="✅ Accept Invite", style=discord.ButtonStyle.success, emoji="✅")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.target_id:
                await interaction.response.send_message("This invite is not for you!", ephemeral=True)
                return
            res = await self.bot.party_system.accept_invite(self.target_id, self.invite_id)
            if res["success"]:
                await interaction.response.edit_message(content="🎉 Joined the party!", view=None)
            else:
                await interaction.response.send_message(f"❌ {res['message']}", ephemeral=True)
        btn.callback = on_click
        return btn

async def setup(bot):
    await bot.add_cog(PartyCog(bot))
