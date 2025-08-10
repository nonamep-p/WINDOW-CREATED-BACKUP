import discord
from discord.ext import commands
from discord import app_commands
from utils.helpers import create_embed, format_number
import logging

logger = logging.getLogger(__name__)

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View and manage your inventory")
    async def inventory(self, interaction: discord.Interaction):
        """Interactive inventory system"""
        await interaction.response.defer()
        
        inventory = await self.bot.inventory_system.get_inventory(interaction.user.id)
        character = await self.bot.character_system.get_character(interaction.user.id)
        
        if not inventory:
            embed = create_embed(
                title="📦 Your Inventory",
                description="Your inventory is empty! Visit the `/shop` to buy some items.",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Calculate inventory stats
        total_items = len(inventory)
        total_value = sum(item.get("price", 0) * item.get("quantity", 1) for item in inventory)
        
        embed = create_embed(
            title="📦 Your Inventory",
            description=f"**Items:** {total_items} | **Total Value:** {format_number(total_value)} gold\n**Gold:** {format_number(character.get('gold', 0) if character else 0)}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Categories",
            value="Select a category to view your items:",
            inline=False
        )
        
        # Count items by category
        categories = {}
        for item in inventory:
            item_type = item.get("type", "Other")
            if item_type not in categories:
                categories[item_type] = 0
            categories[item_type] += item.get("quantity", 1)
        
        category_text = ""
        for category, count in categories.items():
            emoji = {"Weapon": "⚔️", "Armor": "🛡️", "Accessory": "💍", 
                    "Consumable": "🧪", "Material": "🔨", "consumable": "🧪", 
                    "weapon": "⚔️", "armor": "🛡️", "accessory": "💍",
                    "material": "🔨", "Component": "🔨"}.get(category, "📦")
            category_text += f"{emoji} **{category}:** {count} items\n"
        
        embed.add_field(
            name="📊 Your Items",
            value=category_text if category_text else "No items found",
            inline=False
        )
        
        view = InventoryMainView(self.bot, interaction.user.id, inventory, character)
        await interaction.followup.send(embed=embed, view=view)

class InventoryMainView(discord.ui.View):
    def __init__(self, bot, user_id: int, inventory: list, character: dict):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.inventory = inventory
        self.character = character

    @discord.ui.button(label="⚔️ Weapons", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def weapons_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        weapons = [item for item in self.inventory if item.get("type") in ["Weapon", "weapon"]]
        await self._show_category(interaction, "⚔️ Weapons", weapons, discord.Color.red())

    @discord.ui.button(label="🛡️ Armor", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def armor_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        armor = [item for item in self.inventory if item.get("type") in ["Armor", "armor", "Accessory", "accessory"]]
        await self._show_category(interaction, "🛡️ Armor & Accessories", armor, discord.Color.blue())

    @discord.ui.button(label="🧪 Consumables", style=discord.ButtonStyle.success, emoji="🧪")
    async def consumables_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        consumables = [item for item in self.inventory if item.get("type") in ["Consumable", "consumable", "potion", "scroll"]]
        await self._show_category(interaction, "🧪 Consumables", consumables, discord.Color.green())

    @discord.ui.button(label="🔨 Materials", style=discord.ButtonStyle.secondary, emoji="🔨")
    async def materials_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        materials = [item for item in self.inventory if item.get("type") in ["Material", "material", "Component", "component"]]
        await self._show_category(interaction, "🔨 Crafting Materials", materials, discord.Color.orange())

    @discord.ui.button(label="📊 All Items", style=discord.ButtonStyle.primary, emoji="📊", row=1)
    async def all_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        await self._show_category(interaction, "📊 All Items", self.inventory, discord.Color.blue())

    @discord.ui.button(label="💎 Valuable", style=discord.ButtonStyle.danger, emoji="💎", row=1)
    async def valuable_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        valuable = [item for item in self.inventory if item.get("price", 0) > 100 or item.get("rarity") in ["rare", "epic", "legendary"]]
        await self._show_category(interaction, "💎 Valuable Items", valuable, discord.Color.purple())

    @discord.ui.button(label="🔍 Search", style=discord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def search_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        modal = InventorySearchModal(self.bot, self.user_id, self.inventory, self.character)
        await interaction.response.send_modal(modal)

    async def _show_category(self, interaction: discord.Interaction, category_name: str, items: list, color: discord.Color):
        """Show items in a specific category"""
        if not items:
            embed = create_embed(
                title=f"❌ {category_name}",
                description="No items in this category.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Sort by value (price * quantity)
        items.sort(key=lambda x: x.get("price", 0) * x.get("quantity", 1), reverse=True)
        
        total_value = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
        
        embed = create_embed(
            title=f"{category_name}",
            description=f"**Items:** {len(items)} | **Category Value:** {format_number(total_value)} gold",
            color=color
        )
        
        # Show first 6 items
        items_to_show = items[:6]
        for item in items_to_show:
            quantity = item.get("quantity", 1)
            price = item.get("price", 0)
            total_item_value = price * quantity
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.get("rarity", "common"), "⚪")
            
            embed.add_field(
                name=f"{rarity_emoji} {item['name']} x{quantity}",
                value=f"💰 {format_number(total_item_value)} gold\n{item.get('description', 'No description')[:40]}...",
                inline=True
            )
        
        if len(items) > 6:
            embed.set_footer(text=f"Showing 6 of {len(items)} items. Use the dropdown to manage items.")
        
        view = InventoryCategoryView(self.bot, self.user_id, items, self.character, category_name)
        await interaction.response.edit_message(embed=embed, view=view)

class InventoryCategoryView(discord.ui.View):
    def __init__(self, bot, user_id: int, items: list, character: dict, category_name: str):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.items = items
        self.character = character
        self.category_name = category_name
        self.page = 0
        self.items_per_page = 25
        
        # Add item management dropdown
        self._add_item_dropdown()

    def _add_item_dropdown(self):
        """Add item management dropdown"""
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))
        page_items = self.items[start_idx:end_idx]
        
        if not page_items:
            return
        
        options = []
        for item in page_items:
            quantity = item.get("quantity", 1)
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.get("rarity", "common"), "⚪")
            
            options.append(discord.SelectOption(
                label=f"{item['name']} x{quantity}",
                description=f"{rarity_emoji} {item.get('description', 'No description')[:50]}",
                value=item.get("id", item.get("name")),
                emoji="📦"
            ))
        
        select = discord.ui.Select(
            placeholder=f"📦 Select item to manage ({len(page_items)} items)",
            options=options,
            custom_id="item_manage_select"
        )
        select.callback = self._item_selected
        self.add_item(select)

    async def _item_selected(self, interaction: discord.Interaction):
        """Handle item selection for management"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        item_id = interaction.data["values"][0]
        selected_item = next((item for item in self.items if item.get("id", item.get("name")) == item_id), None)
        
        if not selected_item:
            await interaction.response.send_message("❌ Item not found!", ephemeral=True)
            return
        
        # Show item management options
        view = InventoryItemDetailView(self.bot, self.user_id, selected_item, self.character)
        embed = view.create_item_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🏠 Back to Inventory", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def back_to_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This inventory is not yours!", ephemeral=True)
            return
        
        # Refresh inventory data
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        character = await self.bot.character_system.get_character(self.user_id)
        
        if not inventory:
            embed = create_embed(
                title="📦 Your Inventory",
                description="Your inventory is empty!",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        total_items = len(inventory)
        total_value = sum(item.get("price", 0) * item.get("quantity", 1) for item in inventory)
        
        embed = create_embed(
            title="📦 Your Inventory",
            description=f"**Items:** {total_items} | **Total Value:** {format_number(total_value)} gold\n**Gold:** {format_number(character.get('gold', 0) if character else 0)}",
            color=discord.Color.blue()
        )
        
        # Update categories
        categories = {}
        for item in inventory:
            item_type = item.get("type", "Other")
            if item_type not in categories:
                categories[item_type] = 0
            categories[item_type] += item.get("quantity", 1)
        
        category_text = ""
        for category, count in categories.items():
            emoji = {"Weapon": "⚔️", "Armor": "🛡️", "Accessory": "💍", 
                    "Consumable": "🧪", "Material": "🔨", "consumable": "🧪", 
                    "weapon": "⚔️", "armor": "🛡️", "accessory": "💍",
                    "material": "🔨", "Component": "🔨"}.get(category, "📦")
            category_text += f"{emoji} **{category}:** {count} items\n"
        
        embed.add_field(
            name="📊 Your Items",
            value=category_text if category_text else "No items found",
            inline=False
        )
        
        view = InventoryMainView(self.bot, self.user_id, inventory, character)
        await interaction.response.edit_message(embed=embed, view=view)

class InventoryItemDetailView(discord.ui.View):
    def __init__(self, bot, user_id: int, item: dict, character: dict):
        super().__init__(timeout=180.0)
        self.bot = bot
        self.user_id = user_id
        self.item = item
        self.character = character

    def create_item_embed(self):
        """Create detailed item embed"""
        quantity = self.item.get("quantity", 1)
        price = self.item.get("price", 0)
        total_value = price * quantity
        
        rarity_color = {"common": discord.Color.light_grey(), "uncommon": discord.Color.green(), 
                       "rare": discord.Color.blue(), "epic": discord.Color.purple(), 
                       "legendary": discord.Color.gold()}.get(self.item.get("rarity", "common"), discord.Color.light_grey())
        
        embed = create_embed(
            title=f"📦 {self.item['name']}",
            description=self.item.get("description", "No description available."),
            color=rarity_color
        )
        
        embed.add_field(
            name="📊 Quantity",
            value=f"{quantity} items",
            inline=True
        )
        
        embed.add_field(
            name="💰 Unit Value",
            value=f"{format_number(price)} gold",
            inline=True
        )
        
        embed.add_field(
            name="💎 Total Value",
            value=f"{format_number(total_value)} gold",
            inline=True
        )
        
        embed.add_field(
            name="📦 Type",
            value=self.item.get("type", "Unknown").title(),
            inline=True
        )
        
        embed.add_field(
            name="🌟 Rarity",
            value=self.item.get("rarity", "common").title(),
            inline=True
        )
        
        # Check if item is equipped
        equipment = self.character.get("equipment", {})
        is_equipped = False
        equipped_slot = None
        
        for slot, equipped_item in equipment.items():
            if equipped_item and equipped_item.get("id") == self.item.get("id"):
                is_equipped = True
                equipped_slot = slot
                break
        
        if is_equipped:
            embed.add_field(
                name="⚡ Status",
                value=f"✅ Equipped ({equipped_slot})",
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
        
        return embed

    @discord.ui.button(label="⚔️ Equip", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def equip_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your item!", ephemeral=True)
            return
        
        item_type = self.item.get("type", "").lower()
        if item_type not in ["weapon", "armor", "accessory"]:
            embed = create_embed(
                title="❌ Cannot Equip",
                description="This item cannot be equipped.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Try to equip the item
        result = await self.bot.character_system.equip_item(self.user_id, self.item.get("id", self.item.get("name")))
        
        if result.get("success"):
            embed = create_embed(
                title="✅ Item Equipped!",
                description=f"You equipped **{self.item['name']}**!",
                color=discord.Color.green()
            )
            if result.get("replaced_item"):
                embed.add_field(
                    name="🔄 Replaced Item",
                    value=f"**{result['replaced_item']['name']}** was moved to your inventory.",
                    inline=False
                )
        else:
            embed = create_embed(
                title="❌ Equip Failed",
                description=result.get("message", "Failed to equip item."),
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🧪 Use", style=discord.ButtonStyle.success, emoji="🧪")
    async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your item!", ephemeral=True)
            return
        
        item_type = self.item.get("type", "").lower()
        if item_type not in ["consumable", "potion", "scroll"]:
            embed = create_embed(
                title="❌ Cannot Use",
                description="This item cannot be used outside of combat.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Use the item (apply effects and consume)
        effects = self.item.get("effects", {})
        character = await self.bot.character_system.get_character(self.user_id)
        
        if not character:
            await interaction.response.send_message("❌ Character not found!", ephemeral=True)
            return
        
        # Apply effects
        effects_applied = []
        if "heal" in effects:
            heal_amount = effects["heal"]
            current_hp = character.get("hp", character.get("max_hp", 100))
            max_hp = character.get("max_hp", 100)
            new_hp = min(current_hp + heal_amount, max_hp)
            character["hp"] = new_hp
            effects_applied.append(f"❤️ Healed {new_hp - current_hp} HP")
        
        if "sp" in effects:
            sp_amount = effects["sp"]
            current_sp = character.get("sp", character.get("max_sp", 50))
            max_sp = character.get("max_sp", 50)
            new_sp = min(current_sp + sp_amount, max_sp)
            character["sp"] = new_sp
            effects_applied.append(f"⚡ Restored {new_sp - current_sp} SP")
        
        # Consume the item
        await self.bot.inventory_system.consume_item(self.user_id, self.item.get("id", self.item.get("name")), 1)
        await self.bot.db.save_player(self.user_id, character)
        
        embed = create_embed(
            title="✅ Item Used!",
            description=f"You used **{self.item['name']}**!",
            color=discord.Color.green()
        )
        
        if effects_applied:
            embed.add_field(
                name="⚡ Effects Applied",
                value="\n".join(effects_applied),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💰 Sell", style=discord.ButtonStyle.danger, emoji="💰")
    async def sell_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your item!", ephemeral=True)
            return
        
        modal = InventorySellModal(self.bot, self.user_id, self.item)
        await interaction.response.send_modal(modal)

class InventorySearchModal(discord.ui.Modal):
    def __init__(self, bot, user_id: int, inventory: list, character: dict):
        super().__init__(title="🔍 Search Inventory")
        self.bot = bot
        self.user_id = user_id
        self.inventory = inventory
        self.character = character

    search_term = discord.ui.TextInput(
        label="Search Term",
        placeholder="Enter item name, type, or description...",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        search = self.search_term.value.lower()
        
        # Search through inventory
        matching_items = []
        for item in self.inventory:
            if (search in item.get("name", "").lower() or 
                search in item.get("type", "").lower() or 
                search in item.get("description", "").lower()):
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
        view = InventoryCategoryView(self.bot, self.user_id, matching_items, self.character, f"Search: '{self.search_term.value}'")
        embed = create_embed(
            title=f"🔍 Search Results: '{self.search_term.value}'",
            description=f"Found {len(matching_items)} matching items",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class InventorySellModal(discord.ui.Modal):
    def __init__(self, bot, user_id: int, item: dict):
        super().__init__(title=f"Sell {item['name']}")
        self.bot = bot
        self.user_id = user_id
        self.item = item

    quantity = discord.ui.TextInput(
        label="Quantity to Sell",
        placeholder="Enter amount to sell...",
        required=True,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            
            available_qty = self.item.get("quantity", 1)
            if qty > available_qty:
                qty = available_qty
                
        except ValueError:
            embed = create_embed(
                title="❌ Invalid Quantity",
                description="Please enter a valid positive number.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Calculate sell price (50% of buy price)
        unit_price = self.item.get("price", 0)
        sell_price = max(1, unit_price // 2)
        total_gold = sell_price * qty
        
        # Process sale
        character = await self.bot.character_system.get_character(self.user_id)
        if character:
            character["gold"] = character.get("gold", 0) + total_gold
            await self.bot.db.save_player(self.user_id, character)
        
        # Remove items from inventory
        await self.bot.inventory_system.consume_item(self.user_id, self.item.get("id", self.item.get("name")), qty)
        
        embed = create_embed(
            title="✅ Items Sold!",
            description=f"You sold {qty}x **{self.item['name']}** for {format_number(total_gold)} gold!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="💰 Gold Earned",
            value=f"{format_number(total_gold)} gold",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
