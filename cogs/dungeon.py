import discord
from discord.ext import commands
from discord import app_commands
import logging

from utils.helpers import create_embed, format_number, get_plagg_quote

logger = logging.getLogger(__name__)

class DungeonView(discord.ui.View):
    def __init__(self, bot, user_id: int, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id

    async def _refresh(self, interaction: discord.Interaction, session: dict, title: str, color: discord.Color):
        embed = create_embed(
            title=title,
            description=f"Exploring floor {session['current_floor']} of {session['max_floor']}",
            color=color,
            fields=[
                {
                    "name": "📊 Progress",
                    "value": f"**Current Floor:** {session['current_floor']}\n**Total Floors:** {session['max_floor']}\n**Progress:** {(session['current_floor'] / session['max_floor']) * 100:.1f}%",
                    "inline": True,
                },
                {
                    "name": "💰 Rewards",
                    "value": f"**Gold:** {format_number(session['rewards']['gold'])}\n**XP:** {format_number(session['rewards']['xp'])}\n**Items:** {len(session['rewards']['items'])}",
                    "inline": True,
                },
            ],
        )
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(create_embed(title="❌ Not your session", description="Only the dungeon owner can use these buttons.", color=discord.Color.red()), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Advance", style=discord.ButtonStyle.success, emoji="➡️")
    async def advance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            session = await self.bot.dungeon_system.advance_floor(self.user_id)
            await self._refresh(interaction, session, title=f"🏰 Floor {session['current_floor']} Complete!", color=discord.Color.green())
        except Exception as e:
            await interaction.response.send_message(create_embed(title="❌ Dungeon Error", description=str(e), color=discord.Color.red()), ephemeral=True)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.secondary, emoji="🏃")
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            result = await self.bot.dungeon_system.exit_dungeon(self.user_id)
            embed = create_embed(
                title="🏃 Exited Dungeon",
                description=result["message"],
                color=discord.Color.orange(),
                fields=[{"name": "💰 Partial Rewards", "value": f"**Gold:** {format_number(result['rewards']['gold'])}\n**XP:** {format_number(result['rewards']['xp'])}\n**Items:** {len(result['rewards']['items'])}", "inline": True}],
            )
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            await interaction.response.send_message(create_embed(title="❌ Dungeon Error", description=str(e), color=discord.Color.red()), ephemeral=True)

class DungeonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="dungeon", description="Explore dungeons")
    @app_commands.describe(action="What to do in the dungeon")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="start", value="start"),
            app_commands.Choice(name="advance", value="advance"),
            app_commands.Choice(name="status", value="status"),
            app_commands.Choice(name="exit", value="exit")
        ]
    )
    async def dungeon(self, interaction: discord.Interaction, action: str):
        """Dungeon commands"""
        user_id = interaction.user.id
        
        if action == "start":
            await self._start_dungeon(interaction, user_id)
        elif action == "advance":
            # Provide a guarded advance with encounter choices
            await self._advance_dungeon(interaction, user_id)
        elif action == "status":
            await self._dungeon_status(interaction, user_id)
        elif action == "exit":
            await self._exit_dungeon(interaction, user_id)
    
    async def _start_dungeon(self, interaction: discord.Interaction, user_id: int):
        """Start a dungeon"""
        # Check if user has a character
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character create`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        # Warn if already in a dungeon
        existing = await self.bot.dungeon_system.get_dungeon_session(user_id)
        if existing:
            view = discord.ui.View()
            cont = discord.ui.Button(label="Continue", style=discord.ButtonStyle.success, emoji="➡️")
            leave = discord.ui.Button(label="Exit Now", style=discord.ButtonStyle.danger, emoji="🏃")
            async def cont_cb(i: discord.Interaction):
                if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                await self._dungeon_status(i, user_id)
            async def leave_cb(i: discord.Interaction):
                if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                await self._exit_dungeon(i, user_id)
            cont.callback = cont_cb; leave.callback = leave_cb
            view.add_item(cont); view.add_item(leave)
            await interaction.response.send_message(create_embed(title="⚠️ Already Exploring", description="You are already in a dungeon. Finish or exit before starting a new one.", color=discord.Color.orange()), view=view)
            return
        
        # Get available dungeons
        dungeons_list = await self.bot.db.list_dungeons()
        if not dungeons_list:
            embed = create_embed(
                title="❌ No Dungeons Available",
                description="No dungeons are available right now.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Start with the first available dungeon (forest)
        dungeon_id = "forest"
        dungeon = await self.bot.db.get_dungeon(dungeon_id)
        
        if not dungeon:
            embed = create_embed(
                title="❌ Dungeon Not Found",
                description="The selected dungeon is not available.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        try:
            dungeon_session = await self.bot.dungeon_system.start_dungeon(user_id, dungeon_id)
            
            embed = create_embed(
                title=f"🏰 Entering {dungeon['name']}",
                description=f"**{character['username']}** enters the {dungeon['name']}!\n\n{dungeon['description']}\n\n{get_plagg_quote()}",
                color=discord.Color.purple(),
                fields=[
                    {
                        "name": "📊 Dungeon Info",
                        "value": f"**Floors:** {dungeon['floors']}\n**XP Multiplier:** {dungeon.get('xp_multiplier', 1.0)}x\n**Gold Multiplier:** {dungeon.get('gold_multiplier', 1.0)}x\n**Current Floor:** 1",
                        "inline": True
                    }
                ],
                footer=f"Session ID: {dungeon_session['session_id']}"
            )
            
            await interaction.response.send_message(embed=embed, view=DungeonView(self.bot, user_id))
            
        except Exception as e:
            logger.error(f"Error starting dungeon: {e}")
            embed = create_embed(
                title="❌ Dungeon Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
    
    async def _advance_dungeon(self, interaction: discord.Interaction, user_id: int):
        """Advance in dungeon"""
        try:
            # Generate next floor and expose encounter choices
            session = await self.bot.dungeon_system.advance_floor(user_id)
            enc = session.get("last_encounter", {"type": "empty"})
            if enc.get("type") in ("monster", "boss"):
                # Offer to fight now or skip (advance already moved floor, so this is a narrative hook)
                embed = create_embed(
                    title=f"{('👑 Boss' if enc['type']=='boss' else '👹 Monster')} Encounter",
                    description=f"A {enc['monster'].get('name','foe')} appears on floor {enc['floor']}!",
                    color=discord.Color.red() if enc['type']=='boss' else discord.Color.orange()
                )
                v = discord.ui.View()
                fight = discord.ui.Button(label="Fight Now", style=discord.ButtonStyle.danger, emoji="⚔️")
                skip = discord.ui.Button(label="Skip", style=discord.ButtonStyle.secondary, emoji="➡️")
                async def fight_cb(i: discord.Interaction):
                    if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                    res = await self.bot.combat_system.start_battle(user_id, enc["monster"])    
                    if res.get("success"):
                        battle = res["battle"]
                        data = self.bot.combat_system.get_battle_embed(battle)
                        await i.response.edit_message(embed=create_embed(**data), view=None)
                    else:
                        await i.response.send_message(res.get("message","Cannot start battle"), ephemeral=True)
                async def skip_cb(i: discord.Interaction):
                    if i.user.id != user_id: return await i.response.send_message("Not for you", ephemeral=True)
                    await i.response.edit_message(embed=create_embed(title="➡️ Skipped Encounter", description="You move onward...", color=discord.Color.blurple()), view=None)
                fight.callback = fight_cb; skip.callback = skip_cb
                v.add_item(fight); v.add_item(skip)
                await interaction.response.send_message(embed=embed, view=v)
                return
            # Non-combat floor: show progress
            embed = create_embed(
                title=f"🏰 Floor {session['current_floor']-1} Complete!",
                description=f"Advanced to floor {session['current_floor']-1} of {session['dungeon']['name']}",
                color=discord.Color.green(),
                fields=[
                    {"name": "💰 Rewards", "value": f"**Gold:** {format_number(session['rewards']['gold'])}\n**XP:** {format_number(session['rewards']['xp'])}\n**Items:** {len(session['rewards']['items'])}", "inline": True},
                    {"name": "📊 Progress", "value": f"**Current Floor:** {session['current_floor']}\n**Total Floors:** {session['max_floor']}", "inline": True}
                ]
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error advancing dungeon: {e}")
            embed = create_embed(
                title="❌ Dungeon Error",
                description=str(e),
                color=discord.Color.red()
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _dungeon_status(self, interaction: discord.Interaction, user_id: int):
        """Show dungeon status"""
        dungeon_session = await self.bot.dungeon_system.get_dungeon_session(user_id)
        
        if not dungeon_session:
            embed = create_embed(
                title="❌ Not in Dungeon",
                description="You're not currently in a dungeon. Use `/dungeon start` to begin exploring!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = create_embed(
            title=f"🏰 {dungeon_session['dungeon']['name']} Status",
            description=f"Exploring floor {dungeon_session['current_floor']} of {dungeon_session['max_floor']}",
            color=discord.Color.blue(),
            fields=[
                {
                    "name": "📊 Progress",
                    "value": f"**Current Floor:** {dungeon_session['current_floor']}\n**Total Floors:** {dungeon_session['max_floor']}\n**Progress:** {(dungeon_session['current_floor'] / dungeon_session['max_floor']) * 100:.1f}%",
                    "inline": True
                },
                {
                    "name": "💰 Rewards",
                    "value": f"**Gold:** {format_number(dungeon_session['rewards']['gold'])}\n**XP:** {format_number(dungeon_session['rewards']['xp'])}\n**Items:** {len(dungeon_session['rewards']['items'])}",
                    "inline": True
                }
            ],
            footer=f"Session ID: {dungeon_session['session_id']}"
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def _exit_dungeon(self, interaction: discord.Interaction, user_id: int):
        """Exit dungeon"""
        try:
            result = await self.bot.dungeon_system.exit_dungeon(user_id)
            
            embed = create_embed(
                title="🏃 Exited Dungeon",
                description=result["message"],
                color=discord.Color.orange(),
                fields=[
                    {
                        "name": "💰 Partial Rewards",
                        "value": f"**Gold:** {format_number(result['rewards']['gold'])}\n**XP:** {format_number(result['rewards']['xp'])}\n**Items:** {len(result['rewards']['items'])}",
                        "inline": True
                    }
                ]
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error exiting dungeon: {e}")
            embed = create_embed(
                title="❌ Dungeon Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DungeonCog(bot))
