"""
🏰 Interactive Guild System
Ultra-low latency guild management with visual interfaces
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List

from utils.helpers import create_embed
from utils.dropdowns import FactionDropdown

logger = logging.getLogger(__name__)

class GuildInteractiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="guild", description="🏰 Interactive Guild Management")
    async def guild(self, interaction: discord.Interaction):
        """Main guild command with interactive interface"""
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
        
        # Show guild interface
        embed = self._create_guild_embed(character)
        view = GuildInteractiveView(self.bot, user_id, in_faction=bool(character.get("faction")))
        await interaction.followup.send(embed=embed, view=view)

    def _create_guild_embed(self, character):
        """Create guild status embed"""
        faction_id = character.get("faction")
        
        if faction_id:
            # Player is in a faction
            faction = self.bot.faction_system.factions.get(faction_id, {})
            embed = create_embed(
                title=f"🏰 {faction.get('name', 'Unknown Faction')}",
                description=f"Welcome to your faction, **{character['username']}**!",
                color=discord.Color.blue()
            )
            # Paginated stats are handled in view; show quick glance here
            embed.add_field(
                name="📊 Faction Stats",
                value=f"**Level:** {faction.get('level', 1)}\n"
                      f"**XP:** {faction.get('xp', 0)}\n"
                      f"**Members:** {len(faction.get('members', []))}/{faction.get('member_cap', 50)}\n"
                      f"**Treasury:** {faction.get('gold', 0)} gold",
                inline=True
            )
            # Role info
            role = self._role_for_user(faction, character.get("user_id") or character.get("id") or 0)
            if role:
                embed.add_field(name="🎭 Your Role", value=role.title(), inline=True)
            
        else:
            # Player is not in a faction
            embed = create_embed(
                title="🏰 Guild System",
                description=f"Welcome to the guild system, **{character['username']}**! Choose a faction to join.",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📋 Available Factions",
                value="• **Knights of Valor** ⚔️ - Attack bonus\n"
                      "• **Arcane Circle** 🔮 - Intelligence bonus\n"
                      "• **Shadow Brotherhood** 🗡️ - Speed bonus\n"
                      "• **Golden Guild** 💰 - Gold multiplier",
                inline=False
            )
        
        return embed

    def _role_for_user(self, faction: dict, user_id: int) -> Optional[str]:
        if not faction:
            return None
        if faction.get("owner_id") == user_id:
            return "owner"
        if user_id in faction.get("officers", []):
            return "officer"
        if user_id in faction.get("members", []):
            return "member"
        return None

class GuildInteractiveView(discord.ui.View):
    def __init__(self, bot, user_id: int, in_faction: bool):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.in_faction = in_faction
        # Build state-aware controls
        if not in_faction:
            self.add_item(self._make_join_button())
        else:
            self.add_item(self._make_stats_button())
            self.add_item(self._make_contribute_button())
            self.add_item(self._make_invite_button())
            self.add_item(self._make_manage_button())
            self.add_item(self._make_start_raid_button())
            self.add_item(self._make_rankings_button())
            self.add_item(self._make_leave_button())

    # === Buttons ===
    def _make_join_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="🏰 Join Faction", style=discord.ButtonStyle.primary, emoji="🏰")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            character = await self.bot.character_system.get_character(self.user_id)
            if character.get("faction"):
                await interaction.response.send_message("You are already in a faction!", ephemeral=True)
                return
            factions = await self.bot.faction_system.get_all_factions()
            if not factions:
                await interaction.response.send_message("No factions available!", ephemeral=True)
                return
            options = []
            for faction_id, faction in factions.items():
                options.append(discord.SelectOption(
                    label=faction.get("name", faction_id),
                    description=f"{faction.get('description','')} • {len(faction.get('members',[]))}/{faction.get('member_cap',50)} members",
                    value=faction_id,
                    emoji=faction.get("emoji", "🏳️")
                ))
            select = discord.ui.Select(placeholder="Choose a faction to join...", min_values=1, max_values=1, options=options)
            async def select_cb(i: discord.Interaction):
                if i.user.id != self.user_id:
                    await i.response.send_message("This is not for you!", ephemeral=True)
                    return
                faction_id = select.values[0]
                result = await self.bot.faction_system.join_faction(self.user_id, faction_id)
                if result["success"]:
                    await i.response.edit_message(embed=create_embed(title="🎉 Faction Joined!", description=result["message"], color=discord.Color.green()), view=None)
                else:
                    await i.response.send_message(f"❌ Failed to join faction: {result['message']}", ephemeral=True)
            select.callback = select_cb
            view = discord.ui.View()
            view.add_item(select)
            await interaction.response.send_message("Select a faction to join:", view=view, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_stats_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="📊 Stats", style=discord.ButtonStyle.secondary, emoji="📊")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            character = await self.bot.character_system.get_character(self.user_id)
            faction_id = character.get("faction")
            faction = self.bot.faction_system.factions.get(faction_id, {})
            # Build paginated pages
            pages: List[discord.Embed] = []
            # Page 1: Overview
            e1 = create_embed(title=f"{faction.get('emoji','')} {faction.get('name','Faction')} — Overview",
                              description=faction.get("description",""),
                              color=discord.Color.blurple())
            e1.add_field(name="Level", value=str(faction.get("level", 1)))
            e1.add_field(name="XP", value=str(faction.get("xp", 0)))
            e1.add_field(name="Gold", value=str(faction.get("gold", 0)))
            e1.add_field(name="Members", value=f"{len(faction.get('members', []))}/{faction.get('member_cap',50)}", inline=True)
            owner_id = faction.get("owner_id")
            e1.add_field(name="Owner", value=f"<@{owner_id}>" if owner_id else "None", inline=True)
            pages.append(e1)
            # Page 2: Roster
            roster_lines = []
            for uid in faction.get("members", [])[:50]:
                role = "(Officer)" if uid in faction.get("officers", []) else ""
                if uid == owner_id:
                    role = "(Owner)"
                roster_lines.append(f"• <@{uid}> {role}")
            e2 = create_embed(title="Roster", description="\n".join(roster_lines) or "No members", color=discord.Color.green())
            pages.append(e2)
            # Page 3: Invites
            inv_lines = []
            inv = faction.get("invites", {})
            for uid, meta in list(inv.items())[:25]:
                inv_lines.append(f"• <@{uid}> — expires {meta.get('expires_at','soon')}")
            e3 = create_embed(title="Pending Invites", description="\n".join(inv_lines) or "None", color=discord.Color.orange())
            pages.append(e3)
            # Pagination controls
            idx = 0
            async def render(page_idx: int):
                v = discord.ui.View(timeout=120)
                prev_b = discord.ui.Button(label="Prev", style=discord.ButtonStyle.secondary, disabled=page_idx==0)
                next_b = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, disabled=page_idx>=len(pages)-1)
                async def prev_cb(ii: discord.Interaction):
                    if ii.user.id != self.user_id:
                        return await ii.response.send_message("Not for you", ephemeral=True)
                    await ii.response.edit_message(embed=pages[page_idx-1], view=await render(page_idx-1))
                async def next_cb(ii: discord.Interaction):
                    if ii.user.id != self.user_id:
                        return await ii.response.send_message("Not for you", ephemeral=True)
                    await ii.response.edit_message(embed=pages[page_idx+1], view=await render(page_idx+1))
                prev_b.callback = prev_cb
                next_b.callback = next_cb
                v.add_item(prev_b); v.add_item(next_b)
                return v
            await interaction.response.send_message(embed=pages[idx], view=await render(idx), ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_contribute_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="💰 Contribute", style=discord.ButtonStyle.success, emoji="💰")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            character = await self.bot.character_system.get_character(self.user_id)
            if not character.get("faction"):
                await interaction.response.send_message("You must be in a faction to contribute!", ephemeral=True)
                return
            gold_amounts = [10, 25, 50, 100, 250, 500]
            current_gold = character.get("gold", 0)
            available_amounts = [amt for amt in gold_amounts if amt <= current_gold]
            if not available_amounts:
                await interaction.response.send_message("You don't have enough gold to contribute!", ephemeral=True)
                return
            options = [discord.SelectOption(label=f"{amt} gold", description=f"Contribute {amt} gold to your faction", value=str(amt), emoji="💰") for amt in available_amounts]
            select = discord.ui.Select(placeholder="Select contribution amount...", min_values=1, max_values=1, options=options)
            async def select_cb(i: discord.Interaction):
                if i.user.id != self.user_id:
                    await i.response.send_message("This is not for you!", ephemeral=True)
                    return
                amount = int(select.values[0])
                result = await self.bot.faction_system.contribute_to_faction(self.user_id, amount)
                if result["success"]:
                    await i.response.edit_message(embed=create_embed(title="💰 Contribution Successful!", description=result["message"], color=discord.Color.green()), view=None)
                else:
                    await i.response.send_message(f"❌ Contribution failed: {result['message']}", ephemeral=True)
            select.callback = select_cb
            view = discord.ui.View(); view.add_item(select)
            await interaction.response.send_message("Select contribution amount:", view=view, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_invite_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="📨 Invite", style=discord.ButtonStyle.primary, emoji="📨")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This is not for you!", ephemeral=True)
            character = await self.bot.character_system.get_character(self.user_id)
            faction_id = character.get("faction")
            faction = self.bot.faction_system.factions.get(faction_id, {})
            role = "owner" if faction.get("owner_id") == self.user_id else ("officer" if self.user_id in faction.get("officers", []) else "member")
            if role not in ("owner", "officer"):
                return await interaction.response.send_message("Only owner/officers can invite.", ephemeral=True)
            # Modal to input target user ID (minimal viable); future: dropdown of guild members
            class InviteModal(discord.ui.Modal, title="Invite Member"):
                target_id = discord.ui.TextInput(label="Target User ID", placeholder="123456789012345678")
                async def on_submit(modal_self, ii: discord.Interaction):
                    try:
                        target = int(str(modal_self.target_id.value).strip())
                    except Exception:
                        return await ii.response.send_message("Invalid ID.", ephemeral=True)
                    res = await self.bot.faction_system.invite_member(self.user_id, target, faction_id)
                    if res["success"]:
                        await ii.response.send_message("Invite sent.", ephemeral=True)
                    else:
                        await ii.response.send_message(f"❌ {res['message']}", ephemeral=True)
            await interaction.response.send_modal(InviteModal())
        btn.callback = on_click
        return btn

    def _make_manage_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="🛡️ Manage", style=discord.ButtonStyle.secondary, emoji="🛡️")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This is not for you!", ephemeral=True)
            character = await self.bot.character_system.get_character(self.user_id)
            faction_id = character.get("faction")
            faction = self.bot.faction_system.factions.get(faction_id, {})
            role = "owner" if faction.get("owner_id") == self.user_id else ("officer" if self.user_id in faction.get("officers", []) else "member")
            # Management panel: kick, transfer (owner only), promote/demote (owner only)
            members = [m for m in faction.get("members", []) if m != self.user_id]
            if not members:
                return await interaction.response.send_message("No members to manage.", ephemeral=True)
            options = [discord.SelectOption(label=f"{('⭐ ' if m==faction.get('owner_id') else ' ')}Member {m}", value=str(m)) for m in members[:25]]
            select = discord.ui.Select(placeholder="Select member...", min_values=1, max_values=1, options=options)
            action_opts = [
                discord.SelectOption(label="Kick", value="kick"),
            ]
            if role == "owner":
                action_opts.extend([
                    discord.SelectOption(label="Transfer Ownership", value="transfer"),
                    discord.SelectOption(label="Promote to Officer", value="promote"),
                    discord.SelectOption(label="Demote Officer", value="demote"),
                ])
            action_select = discord.ui.Select(placeholder="Choose action...", min_values=1, max_values=1, options=action_opts)
            async def go(ii: discord.Interaction):
                if ii.user.id != self.user_id:
                    return await ii.response.send_message("Not for you", ephemeral=True)
                target_id = int(select.values[0])
                action = action_select.values[0]
                if action == "kick":
                    res = await self.bot.faction_system.kick_member(self.user_id, target_id, faction_id)
                elif action == "transfer":
                    res = await self.bot.faction_system.transfer_ownership(self.user_id, target_id, faction_id)
                elif action == "promote":
                    res = await self.bot.faction_system.promote_officer(self.user_id, target_id, faction_id)
                elif action == "demote":
                    res = await self.bot.faction_system.demote_officer(self.user_id, target_id, faction_id)
                else:
                    res = {"success": False, "message": "Unknown action"}
                if res["success"]:
                    await ii.response.edit_message(embed=create_embed(title="✅ Success", description=res["message"], color=discord.Color.green()), view=None)
                else:
                    await ii.response.send_message(f"❌ {res['message']}", ephemeral=True)
            go_btn = discord.ui.Button(label="Apply", style=discord.ButtonStyle.success)
            go_btn.callback = go
            v = discord.ui.View(timeout=120)
            v.add_item(select); v.add_item(action_select); v.add_item(go_btn)
            await interaction.response.send_message("Member management:", view=v, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_start_raid_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="⚔️ Start Raid", style=discord.ButtonStyle.danger, emoji="⚔️")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            character = await self.bot.character_system.get_character(self.user_id)
            if not character.get("faction"):
                await interaction.response.send_message("You must be in a faction to start raids!", ephemeral=True)
                return
            raid_types = [("normal", "Normal Raid", "Standard faction raid with moderate rewards"), ("elite", "Elite Raid", "Challenging raid with better rewards"), ("boss", "Boss Raid", "Epic boss raid with rare rewards")]
            options = [discord.SelectOption(label=name, description=desc, value=rid, emoji="⚔️") for rid, name, desc in raid_types]
            select = discord.ui.Select(placeholder="Select raid type...", min_values=1, max_values=1, options=options)
            async def select_cb(i: discord.Interaction):
                if i.user.id != self.user_id:
                    await i.response.send_message("This is not for you!", ephemeral=True)
                    return
                raid_type = select.values[0]
                result = await self.bot.faction_system.start_faction_raid(self.user_id, raid_type)
                if result["success"]:
                    emb = create_embed(title="⚔️ Raid Started!", description=result["message"], color=discord.Color.red())
                    emb.add_field(name="Raid ID", value=result["raid_id"], inline=False)
                    await i.response.edit_message(embed=emb, view=None)
                else:
                    await i.response.send_message(f"❌ Failed to start raid: {result['message']}", ephemeral=True)
            select.callback = select_cb
            view = discord.ui.View(); view.add_item(select)
            await interaction.response.send_message("Select raid type:", view=view, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_rankings_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="📊 Rankings", style=discord.ButtonStyle.secondary, emoji="📊")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            rankings = await self.bot.faction_system.get_faction_rankings()
            if not rankings:
                await interaction.response.send_message("No factions found!", ephemeral=True)
                return
            embed = create_embed(title="🏆 Faction Rankings", description="Top factions by level and XP", color=discord.Color.gold())
            for i, faction in enumerate(rankings[:10], 1):
                embed.add_field(name=f"#{i} {faction['emoji']} {faction['name']}", value=f"**Level:** {faction['level']} • **XP:** {faction['xp']}\n**Members:** {faction['members']} • **Gold:** {faction['gold']}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        btn.callback = on_click
        return btn

    def _make_leave_button(self) -> discord.ui.Button:
        btn = discord.ui.Button(label="❌ Leave Faction", style=discord.ButtonStyle.danger, emoji="❌")
        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            character = await self.bot.character_system.get_character(self.user_id)
            if not character.get("faction"):
                await interaction.response.send_message("You are not in a faction!", ephemeral=True)
                return
            confirm = discord.ui.Button(label="✅ Confirm Leave", style=discord.ButtonStyle.danger, emoji="✅")
            async def confirm_cb(i: discord.Interaction):
                if i.user.id != self.user_id:
                    await i.response.send_message("This is not for you!", ephemeral=True)
                    return
                result = await self.bot.faction_system.leave_faction(self.user_id)
                if result["success"]:
                    await i.response.edit_message(embed=create_embed(title="👋 Faction Left", description=result["message"], color=discord.Color.orange()), view=None)
                else:
                    await i.response.send_message(f"❌ Failed to leave faction: {result['message']}", ephemeral=True)
            confirm.callback = confirm_cb
            v = discord.ui.View(); v.add_item(confirm)
            await interaction.response.send_message("Are you sure you want to leave your faction?", view=v, ephemeral=True)
        btn.callback = on_click
        return btn

async def setup(bot):
    await bot.add_cog(GuildInteractiveCog(bot))
