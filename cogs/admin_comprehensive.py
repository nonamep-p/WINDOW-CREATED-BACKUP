"""
🔧 Comprehensive Admin Panel
Ultra-low latency server management with full administrative controls
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.helpers import create_embed

logger = logging.getLogger(__name__)

class AdminComprehensiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin_panel", description="🔧 Comprehensive Admin Panel")
    @app_commands.default_permissions(administrator=True)
    async def admin(self, interaction: discord.Interaction):
        """Main admin command with comprehensive management tools"""
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command!", ephemeral=True)
            return
        
        # Show admin interface
        embed = self._create_admin_embed()
        view = AdminComprehensiveView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def _create_admin_embed(self):
        """Create admin status embed"""
        embed = create_embed(
            title="🔧 Admin Panel",
            description="Comprehensive server management tools",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="👥 Player Management",
            value="• View all players\n• Give items/gold/XP\n• Reset characters\n• Ban/unban players",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ System Management",
            value="• Server statistics\n• Economy settings\n• Combat balance\n• Database backup",
            inline=True
        )
        
        embed.add_field(
            name="🏰 Content Management",
            value="• Manage factions\n• Create events\n• Set announcements\n• Monitor activity",
            inline=True
        )
        
        return embed

class AdminComprehensiveView(discord.ui.View):
    def __init__(self, bot, admin_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.admin_id = admin_id

    @discord.ui.button(label="👥 Player Management", style=discord.ButtonStyle.primary, emoji="👥")
    async def player_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="👥 Player Management",
            description="Manage players and their data",
            color=discord.Color.blue()
        )
        
        view = PlayerManagementView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="⚙️ System Settings", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def system_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="⚙️ System Settings",
            description="Configure server settings and balance",
            color=discord.Color.green()
        )
        
        view = SystemSettingsView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 Server Stats", style=discord.ButtonStyle.success, emoji="📊")
    async def server_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get server statistics from players.json map
        players_map = await self.bot.db.load_json_data("players.json")
        all_players = list(players_map.values())
        total_players = len(all_players)
        
        # Calculate stats
        total_level = sum(player.get("level", 1) for player in all_players)
        total_gold = sum(player.get("gold", 0) for player in all_players)
        total_battles = sum(player.get("total_battles", 0) for player in all_players)
        
        embed = create_embed(
            title="📊 Server Statistics",
            description=f"Comprehensive server overview",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="👥 Players",
            value=f"**Total Players:** {total_players}\n"
                  f"**Active Today:** {len([p for p in all_players if p.get('last_active')])}\n"
                  f"**New This Week:** {len([p for p in all_players if p.get('created_at')])}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Progress",
            value=f"**Total Levels:** {total_level}\n"
                  f"**Total Gold:** {total_gold:,}\n"
                  f"**Total Battles:** {total_battles}",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Top Players",
            value="• Highest Level\n• Most Gold\n• Most Battles\n• Most Achievements",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔧 Database Tools", style=discord.ButtonStyle.danger, emoji="🔧")
    async def database_tools(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🔧 Database Tools",
            description="Database management and maintenance",
            color=discord.Color.red()
        )
        
        view = DatabaseToolsView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

class PlayerManagementView(discord.ui.View):
    def __init__(self, bot, admin_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.admin_id = admin_id

    @discord.ui.button(label="👤 View All Players", style=discord.ButtonStyle.primary, emoji="👤")
    async def view_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        players_map = await self.bot.db.load_json_data("players.json")
        
        if not players_map:
            await interaction.response.send_message("No players found!", ephemeral=True)
            return
        
        # Create player selection dropdown
        options = []
        for player_id, player_data in list(players_map.items())[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=f"{player_data.get('username', 'Unknown')} (Level {player_data.get('level', 1)})",
                description=f"Gold: {player_data.get('gold', 0)} • Battles: {player_data.get('total_battles', 0)}",
                value=str(player_id),
                emoji="👤"
            ))
        
        select = discord.ui.Select(
            placeholder="Select a player to manage...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def player_select_callback(interaction: discord.Interaction):
            if interaction.user.id != self.admin_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            player_id = str(select.values[0])
            player_data = players_map.get(player_id, {})
            
            embed = create_embed(
                title=f"👤 {player_data.get('username', 'Unknown')}",
                description="Player management options",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📊 Player Info",
                value=f"**Level:** {player_data.get('level', 1)}\n"
                      f"**Gold:** {player_data.get('gold', 0)}\n"
                      f"**XP:** {player_data.get('xp', 0)}\n"
                      f"**Battles:** {player_data.get('total_battles', 0)}",
                inline=True
            )
            
            try:
                numeric_id = int(player_id)
            except Exception:
                numeric_id = 0
            view = PlayerActionView(self.bot, self.admin_id, numeric_id)
            await interaction.response.edit_message(embed=embed, view=view)
        
        select.callback = player_select_callback
        
        # Create temporary view with dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select a player to manage:", view=view, ephemeral=True)

    @discord.ui.button(label="💰 Give Resources", style=discord.ButtonStyle.success, emoji="💰")
    async def give_resources(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Create resource type selection
        resource_types = [
            ("gold", "Gold", "Give gold to players"),
            ("xp", "Experience", "Give XP to players"),
            ("item", "Items", "Give items to players"),
            ("skill", "Skills", "Give skills to players")
        ]
        
        options = []
        for resource_id, name, description in resource_types:
            options.append(discord.SelectOption(
                label=name,
                description=description,
                value=resource_id,
                emoji="💰"
            ))
        
        select = discord.ui.Select(
            placeholder="Select resource type...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def resource_callback(interaction: discord.Interaction):
            if interaction.user.id != self.admin_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            resource_type = select.values[0]
            # This would open another interface for selecting players and amounts
            await interaction.response.send_message(f"Resource type selected: {resource_type}. Player selection coming soon!", ephemeral=True)
        
        select.callback = resource_callback
        
        # Create temporary view with dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select resource type:", view=view, ephemeral=True)

    @discord.ui.button(label="🔄 Reset Player", style=discord.ButtonStyle.danger, emoji="🔄")
    async def reset_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Confirmation + action: wipe players.json safely
        confirm_button = discord.ui.Button(label="✅ Confirm Reset All Players", style=discord.ButtonStyle.danger, emoji="⚠️")
        async def confirm_cb(i: discord.Interaction):
            if i.user.id != self.admin_id:
                await i.response.send_message("This is not for you!", ephemeral=True)
                return
            # Reset players
            await self.bot.db.save_json_data("players.json", {})
            await i.response.edit_message(content="✅ All player data has been reset.", embed=None, view=None)
        confirm_button.callback = confirm_cb
        view = discord.ui.View()
        view.add_item(confirm_button)
        await interaction.response.send_message("This will erase ALL player profiles. Proceed?", view=view, ephemeral=True)

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🔧 Admin Panel",
            description="Comprehensive server management tools",
            color=discord.Color.red()
        )
        
        view = AdminComprehensiveView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

class PlayerActionView(discord.ui.View):
    def __init__(self, bot, admin_id: int, target_player_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.admin_id = admin_id
        self.target_player_id = target_player_id

    @discord.ui.button(label="💰 Give Gold", style=discord.ButtonStyle.success, emoji="💰")
    async def give_gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Create gold amount selection
        gold_amounts = [10, 25, 50, 100, 250, 500, 1000, 5000]
        
        options = []
        for amount in gold_amounts:
            options.append(discord.SelectOption(
                label=f"{amount} gold",
                description=f"Give {amount} gold to player",
                value=str(amount),
                emoji="💰"
            ))
        
        select = discord.ui.Select(
            placeholder="Select gold amount...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def gold_callback(interaction: discord.Interaction):
            if interaction.user.id != self.admin_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            amount = int(select.values[0])
            result = await self.bot.character_system.add_gold(self.target_player_id, amount)
            
            if result["success"]:
                await interaction.response.send_message(f"✅ Gave {amount} gold to player!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to give gold: {result['message']}", ephemeral=True)
        
        select.callback = gold_callback
        
        # Create temporary view with dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select gold amount:", view=view, ephemeral=True)

    @discord.ui.button(label="📈 Give XP", style=discord.ButtonStyle.primary, emoji="📈")
    async def give_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Create XP amount selection
        xp_amounts = [10, 25, 50, 100, 250, 500, 1000, 5000]
        
        options = []
        for amount in xp_amounts:
            options.append(discord.SelectOption(
                label=f"{amount} XP",
                description=f"Give {amount} XP to player",
                value=str(amount),
                emoji="📈"
            ))
        
        select = discord.ui.Select(
            placeholder="Select XP amount...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def xp_callback(interaction: discord.Interaction):
            if interaction.user.id != self.admin_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            amount = int(select.values[0])
            result = await self.bot.character_system.add_xp(self.target_player_id, amount)
            
            if result["success"]:
                await interaction.response.send_message(f"✅ Gave {amount} XP to player!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to give XP: {result['message']}", ephemeral=True)
        
        select.callback = xp_callback
        
        # Create temporary view with dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select XP amount:", view=view, ephemeral=True)

    @discord.ui.button(label="📦 Give Item", style=discord.ButtonStyle.secondary, emoji="📦")
    async def give_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get available items
        items_data = await self.bot.db.load_items()
        
        if not items_data:
            await interaction.response.send_message("No items available!", ephemeral=True)
            return
        
        # Create item selection dropdown
        options = []
        for item_id, item_data in list(items_data.items())[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=item_data.get("name", "Unknown Item"),
                description=f"{item_data.get('type', 'Unknown')} • {item_data.get('price', 0)} gold",
                value=item_id,
                emoji="📦"
            ))
        
        select = discord.ui.Select(
            placeholder="Select item to give...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def item_callback(interaction: discord.Interaction):
            if interaction.user.id != self.admin_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            item_id = select.values[0]
            result = await self.bot.inventory_system.add_item(self.target_player_id, item_id, 1)
            
            if result["success"]:
                await interaction.response.send_message(f"✅ Gave item to player!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to give item: {result['message']}", ephemeral=True)
        
        select.callback = item_callback
        
        # Create temporary view with dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select item to give:", view=view, ephemeral=True)

class SystemSettingsView(discord.ui.View):
    def __init__(self, bot, admin_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.admin_id = admin_id

    @discord.ui.button(label="⚖️ Balance Settings", style=discord.ButtonStyle.primary, emoji="⚖️")
    async def balance_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        await interaction.response.send_message("⚖️ Balance settings coming soon!", ephemeral=True)

    @discord.ui.button(label="🎮 Game Settings", style=discord.ButtonStyle.secondary, emoji="🎮")
    async def game_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        await interaction.response.send_message("🎮 Game settings coming soon!", ephemeral=True)

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🔧 Admin Panel",
            description="Comprehensive server management tools",
            color=discord.Color.red()
        )
        
        view = AdminComprehensiveView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

class DatabaseToolsView(discord.ui.View):
    def __init__(self, bot, admin_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.admin_id = admin_id

    @discord.ui.button(label="💾 Backup Data", style=discord.ButtonStyle.primary, emoji="💾")
    async def backup_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        await interaction.response.send_message("💾 Database backup functionality coming soon!", ephemeral=True)

    @discord.ui.button(label="🧹 Clean Data", style=discord.ButtonStyle.danger, emoji="🧹")
    async def clean_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        await interaction.response.send_message("🧹 Data cleaning functionality coming soon!", ephemeral=True)

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🔧 Admin Panel",
            description="Comprehensive server management tools",
            color=discord.Color.red()
        )
        
        view = AdminComprehensiveView(self.bot, self.admin_id)
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(AdminComprehensiveCog(bot))
