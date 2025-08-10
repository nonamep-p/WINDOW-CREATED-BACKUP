import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from datetime import datetime, timedelta
import random

from utils.helpers import create_embed, format_number

logger = logging.getLogger(__name__)

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Claim your daily rewards")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily rewards"""
        user_id = interaction.user.id
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Claim daily reward via economy system
        result = await self.bot.economy_system.get_daily_reward(user_id)
        
        if result.get("success"):
            gold = result.get("gold", 0)
            xp = result.get("xp", 0)
            streak = result.get("streak", 1)
            mult_text = result.get("message", "")
            embed = create_embed(
                title="🎁 Daily Reward Claimed!",
                description=f"**Day {streak} Streak!**\n{mult_text}",
                color=discord.Color.gold()
            )
            embed.add_field(name="Rewards", value=f"💰 {format_number(gold)} Gold\n⭐ {format_number(xp)} XP", inline=False)
            view = DailyRewardView(self.bot, user_id)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            msg = result.get("message", "Daily not ready yet")
            embed = create_embed(
                title="⏳ Daily Reward Not Ready",
                description=msg,
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Removed duplicate achievements/leaderboard commands; use profiles cog instead

    @app_commands.command(name="shop", description="Browse and buy items from the shop")
    async def shop(self, interaction: discord.Interaction):
        """Interactive shop system"""
        await interaction.response.defer()
        
        items_data = await self.bot.db.load_items()
        if not items_data:
            embed = create_embed(
                title="❌ Shop Unavailable",
                description="The shop is currently empty. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get player's current gold
        character = await self.bot.character_system.get_character(interaction.user.id)
        current_gold = character.get("gold", 0) if character else 0
        
        embed = create_embed(
            title="🛒 Adventurer's Shop",
            description=f"Welcome to the shop! **Your Gold:** {format_number(current_gold)}\nSelect a category to browse items:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="⚔️ Weapons",
            value="Swords, axes, staffs, and more",
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Armor",
            value="Protective gear and accessories",
            inline=True
        )
        
        embed.add_field(
            name="🧪 Consumables",
            value="Potions, scrolls, and utilities",
            inline=True
        )
        
        embed.add_field(
            name="🔨 Materials",
            value="Crafting components and resources",
            inline=True
        )
        
        embed.add_field(
            name="💎 Premium",
            value="Rare and legendary items",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Special",
            value="Limited time offers",
            inline=True
        )
        
        view = ShopMainView(self.bot, interaction.user.id, items_data, current_gold)
        await interaction.followup.send(embed=embed, view=view)

class DailyRewardView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id


    @discord.ui.button(label="🎁 Claim Again", style=discord.ButtonStyle.primary, emoji="🎁")
    async def claim_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Attempt claim again; will likely tell user to wait
        result = await self.bot.economy_system.get_daily_reward(self.user_id)
        if result.get("success"):
            await interaction.response.send_message("🎁 Daily reward claimed again!", ephemeral=True)
        else:
            await interaction.response.send_message(result.get("message", "Not ready yet"), ephemeral=True)

class ShopMainView(discord.ui.View):
    def __init__(self, bot, user_id: int, items_data: dict, current_gold: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.items_data = items_data
        self.current_gold = current_gold

    @discord.ui.button(label="⚔️ Weapons", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def weapons_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        weapons = [item for item in self.items_data.values() if item.get("type") in ["Weapon", "weapon"]]
        await self._show_category(interaction, "⚔️ Weapons", weapons, discord.Color.red())

    @discord.ui.button(label="🛡️ Armor", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def armor_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        armor = [item for item in self.items_data.values() if item.get("type") in ["Armor", "armor", "Accessory", "accessory"]]
        await self._show_category(interaction, "🛡️ Armor & Accessories", armor, discord.Color.blue())

    @discord.ui.button(label="🧪 Consumables", style=discord.ButtonStyle.success, emoji="🧪")
    async def consumables_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        consumables = [item for item in self.items_data.values() if item.get("type") in ["Consumable", "consumable", "potion", "scroll"]]
        await self._show_category(interaction, "🧪 Consumables", consumables, discord.Color.green())

    @discord.ui.button(label="🔨 Materials", style=discord.ButtonStyle.secondary, emoji="🔨")
    async def materials_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        materials = [item for item in self.items_data.values() if item.get("type") in ["Material", "material", "Component", "component"]]
        await self._show_category(interaction, "🔨 Crafting Materials", materials, discord.Color.orange())

    @discord.ui.button(label="💎 Premium", style=discord.ButtonStyle.danger, emoji="💎", row=1)
    async def premium_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        premium = [item for item in self.items_data.values() if item.get("rarity") in ["legendary", "epic", "rare"] or item.get("price", 0) > 1000]
        await self._show_category(interaction, "💎 Premium Items", premium, discord.Color.purple())

    @discord.ui.button(label="🎁 Special", style=discord.ButtonStyle.success, emoji="🎁", row=1)
    async def special_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        # Special items could be daily deals, limited time, etc.
        special = [item for item in self.items_data.values() if item.get("special", False) or "special" in item.get("tags", [])]
        if not special:
            # If no special items, show some random high-value items
            all_items = list(self.items_data.values())
            special = sorted(all_items, key=lambda x: x.get("price", 0), reverse=True)[:10]
        
        await self._show_category(interaction, "🎁 Special Offers", special, discord.Color.gold())

    @discord.ui.button(label="🔍 Search", style=discord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def search_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        modal = ShopSearchModal(self.bot, self.user_id, self.items_data, self.current_gold)
        await interaction.response.send_modal(modal)

    async def _show_category(self, interaction: discord.Interaction, category_name: str, items: list, color: discord.Color):
        """Show items in a specific category"""
        if not items:
            embed = create_embed(
                title=f"❌ {category_name}",
                description="No items available in this category.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Sort by price
        items.sort(key=lambda x: x.get("price", 0))
        
        embed = create_embed(
            title=f"{category_name}",
            description=f"**Your Gold:** {format_number(self.current_gold)}\n**Items Available:** {len(items)}",
            color=color
        )
        
        # Show first 8 items
        items_to_show = items[:8]
        for item in items_to_show:
            price = item.get("price", 0)
            can_afford = "✅" if self.current_gold >= price else "❌"
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.get("rarity", "common"), "⚪")
            
            embed.add_field(
                name=f"{can_afford} {rarity_emoji} {item['name']}",
                value=f"💰 {format_number(price)} gold\n{item.get('description', 'No description')[:50]}...",
                inline=True
            )
        
        if len(items) > 8:
            embed.set_footer(text=f"Showing 8 of {len(items)} items. Use the dropdown to see more.")
        
        view = ShopCategoryView(self.bot, self.user_id, items, self.current_gold, category_name)
        await interaction.response.edit_message(embed=embed, view=view)

class ShopCategoryView(discord.ui.View):
    def __init__(self, bot, user_id: int, items: list, current_gold: int, category_name: str):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.items = items
        self.current_gold = current_gold
        self.category_name = category_name
        self.page = 0
        self.items_per_page = 25
        
        # Add item selection dropdown
        self._add_item_dropdown()

    def _add_item_dropdown(self):
        """Add item selection dropdown for current page"""
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))
        page_items = self.items[start_idx:end_idx]
        
        if not page_items:
            return
        
        options = []
        for idx, item in enumerate(page_items):
            price = item.get("price", 0)
            can_afford = "✅" if self.current_gold >= price else "❌"
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.get("rarity", "common"), "⚪")
            
            options.append(discord.SelectOption(
                label=f"{can_afford} {item['name']} - {format_number(price)}g",
                description=f"{rarity_emoji} {item.get('description', 'No description')[:50]}",
                value=item.get("id", item.get("name", f"item_{idx}")),
                emoji="🛒"
            ))
        
        select = discord.ui.Select(
            placeholder=f"🛒 Select item to buy ({len(page_items)} items)",
            options=options,
            custom_id="item_select"
        )
        select.callback = self._item_selected
        self.add_item(select)

    async def _item_selected(self, interaction: discord.Interaction):
        """Handle item selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        item_id = interaction.data["values"][0]
        selected_item = None
        for item in self.items:
            if (item.get("id") == item_id or 
                item.get("name") == item_id or 
                f"item_{self.items.index(item)}" == item_id):
                selected_item = item
                break
        
        if not selected_item:
            await interaction.response.send_message("❌ Item not found!", ephemeral=True)
            return
        
        # Show item details and purchase options
        view = ShopItemDetailView(self.bot, self.user_id, selected_item, self.current_gold)
        embed = view.create_item_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🏠 Back to Shop", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def back_to_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This shop is not for you!", ephemeral=True)
            return
        
        # Return to main shop view
        items_data = await self.bot.db.load_items()
        embed = create_embed(
            title="🛒 Adventurer's Shop",
            description=f"Welcome to the shop! **Your Gold:** {format_number(self.current_gold)}\nSelect a category to browse items:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="⚔️ Weapons", value="Swords, axes, staffs, and more", inline=True)
        embed.add_field(name="🛡️ Armor", value="Protective gear and accessories", inline=True)
        embed.add_field(name="🧪 Consumables", value="Potions, scrolls, and utilities", inline=True)
        embed.add_field(name="🔨 Materials", value="Crafting components and resources", inline=True)
        embed.add_field(name="💎 Premium", value="Rare and legendary items", inline=True)
        embed.add_field(name="🎁 Special", value="Limited time offers", inline=True)
        
        view = ShopMainView(self.bot, self.user_id, items_data, self.current_gold)
        await interaction.response.edit_message(embed=embed, view=view)

class ShopItemDetailView(discord.ui.View):
    def __init__(self, bot, user_id: int, item: dict, current_gold: int):
        super().__init__(timeout=180.0)
        self.bot = bot
        self.user_id = user_id
        self.item = item
        self.current_gold = current_gold

    def create_item_embed(self):
        """Create detailed item embed"""
        price = self.item.get("price", 0)
        can_afford = self.current_gold >= price
        rarity_color = {"common": discord.Color.light_grey(), "uncommon": discord.Color.green(), 
                       "rare": discord.Color.blue(), "epic": discord.Color.purple(), 
                       "legendary": discord.Color.gold()}.get(self.item.get("rarity", "common"), discord.Color.light_grey())
        
        embed = create_embed(
            title=f"🛒 {self.item['name']}",
            description=self.item.get("description", "No description available."),
            color=rarity_color
        )
        
        embed.add_field(
            name="💰 Price",
            value=f"{format_number(price)} gold",
            inline=True
        )
        
        embed.add_field(
            name="📊 Rarity",
            value=self.item.get("rarity", "common").title(),
            inline=True
        )
        
        embed.add_field(
            name="📦 Type",
            value=self.item.get("type", "Unknown").title(),
            inline=True
        )
        
        # Show item effects if available
        effects = self.item.get("effects", {})
        if effects:
            effects_text = ""
            for effect, value in effects.items():
                if effect == "heal":
                    effects_text += f"❤️ Heals {value} HP\n"
                elif effect == "sp":
                    effects_text += f"⚡ Restores {value} SP\n"
                elif effect == "atk" or effect == "attack":
                    effects_text += f"⚔️ +{value} Attack\n"
                elif effect == "defense":
                    effects_text += f"🛡️ +{value} Defense\n"
                elif effect == "hp":
                    effects_text += f"❤️ +{value} HP\n"
                elif effect == "crit":
                    effects_text += f"💥 +{value*100:.1f}% Crit\n"
                else:
                    effects_text += f"✨ {effect}: {value}\n"
            
            if effects_text:
                embed.add_field(name="⚡ Effects", value=effects_text, inline=False)
        
        # Affordability status
        afford_status = "✅ You can afford this!" if can_afford else f"❌ You need {format_number(price - self.current_gold)} more gold"
        embed.add_field(
            name="💳 Affordability",
            value=afford_status,
            inline=False
        )
        
        return embed

    @discord.ui.button(label="💰 Buy 1x", style=discord.ButtonStyle.success, emoji="💰")
    async def buy_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase_item(interaction, 1)

    @discord.ui.button(label="📦 Buy 5x", style=discord.ButtonStyle.primary, emoji="📦")
    async def buy_five(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase_item(interaction, 5)

    @discord.ui.button(label="🛒 Buy 10x", style=discord.ButtonStyle.primary, emoji="🛒")
    async def buy_ten(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase_item(interaction, 10)

    @discord.ui.button(label="✏️ Custom", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def buy_custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        modal = ShopPurchaseModal(self.bot, self.user_id, self.item, self.current_gold)
        await interaction.response.send_modal(modal)

    async def _purchase_item(self, interaction: discord.Interaction, quantity: int):
        """Handle item purchase"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        total_cost = self.item.get("price", 0) * quantity
        
        if self.current_gold < total_cost:
            embed = create_embed(
                title="❌ Insufficient Funds",
                description=f"You need {format_number(total_cost - self.current_gold)} more gold to buy {quantity}x {self.item['name']}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Process purchase
        result = await self.bot.economy_system.buy_item(self.user_id, self.item["id"], quantity)
        
        if result.get("success"):
            embed = create_embed(
                title="✅ Purchase Successful!",
                description=f"You bought {quantity}x **{self.item['name']}** for {format_number(total_cost)} gold!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💰 Remaining Gold",
                value=f"{format_number(self.current_gold - total_cost)} gold",
                inline=True
            )
        else:
            embed = create_embed(
                title="❌ Purchase Failed",
                description=result.get("message", "An error occurred during purchase."),
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ShopSearchModal(discord.ui.Modal):
    def __init__(self, bot, user_id: int, items_data: dict, current_gold: int):
        super().__init__(title="🔍 Search Shop Items")
        self.bot = bot
        self.user_id = user_id
        self.items_data = items_data
        self.current_gold = current_gold

    search_term = discord.ui.TextInput(
        label="Search Term",
        placeholder="Enter item name, type, or description...",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        search = self.search_term.value.lower()
        
        # Search through items
        matching_items = []
        for item in self.items_data.values():
            if (search in item.get("name", "").lower() or 
                search in item.get("type", "").lower() or 
                search in item.get("description", "").lower() or
                search in " ".join(item.get("tags", [])).lower()):
                matching_items.append(item)
        
        if not matching_items:
            embed = create_embed(
                title="🔍 Search Results",
                description=f"No items found matching '{self.search_term.value}'.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Show search results
        view = ShopCategoryView(self.bot, self.user_id, matching_items, self.current_gold, f"Search: '{self.search_term.value}'")
        embed = create_embed(
            title=f"🔍 Search Results: '{self.search_term.value}'",
            description=f"Found {len(matching_items)} matching items",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ShopPurchaseModal(discord.ui.Modal):
    def __init__(self, bot, user_id: int, item: dict, current_gold: int):
        super().__init__(title=f"Purchase {item['name']}")
        self.bot = bot
        self.user_id = user_id
        self.item = item
        self.current_gold = current_gold

    quantity = discord.ui.TextInput(
        label="Quantity",
        placeholder="Enter amount to buy...",
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            embed = create_embed(
                title="❌ Invalid Quantity",
                description="Please enter a valid positive number.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        total_cost = self.item.get("price", 0) * qty
        
        if self.current_gold < total_cost:
            embed = create_embed(
                title="❌ Insufficient Funds",
                description=f"You need {format_number(total_cost - self.current_gold)} more gold to buy {qty}x {self.item['name']}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Process purchase
        result = await self.bot.economy_system.buy_item(self.user_id, self.item["id"], qty)
        
        if result.get("success"):
            embed = create_embed(
                title="✅ Purchase Successful!",
                description=f"You bought {qty}x **{self.item['name']}** for {format_number(total_cost)} gold!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Purchase Failed",
                description=result.get("message", "An error occurred during purchase."),
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
