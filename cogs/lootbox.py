import random
import discord
from discord.ext import commands
from discord import app_commands

from utils.helpers import create_embed, get_rarity_color, get_rarity_emoji

class LootboxView(discord.ui.View):
    def __init__(self, bot, user_id: int, box_item_id: str, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.box_item_id = box_item_id
        self.last_roll = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This lootbox isn’t yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Open", style=discord.ButtonStyle.success, emoji="🎁")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._roll(interaction)

    @discord.ui.button(label="Reroll (200g)", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Charge gold
        char = await self.bot.character_system.get_character(self.user_id)
        if char.get("gold", 0) < 200:
            await interaction.response.send_message("Not enough gold to reroll.", ephemeral=True)
            return
        await self.bot.character_system.spend_gold(self.user_id, 200)
        await self._roll(interaction)

    async def _roll(self, interaction: discord.Interaction):
        # Simple rarity distribution
        tiers = [
            ("Common", 0.6),
            ("Uncommon", 0.2),
            ("Rare", 0.12),
            ("Epic", 0.06),
            ("Legendary", 0.02),
        ]
        pick = random.random()
        acc = 0.0
        rarity = "Common"
        for r, p in tiers:
            acc += p
            if pick <= acc:
                rarity = r
                break
        # Pick a random item matching rarity from items.json (fallback to any)
        items_data = await self.bot.db.load_items()
        pool = [iid for iid, it in items_data.items() if isinstance(it, dict) and it.get("rarity", "Common").lower() == rarity.lower()]
        if not pool:
            pool = list(items_data.keys())
        item_id = random.choice(pool)
        item = items_data.get(item_id, {"name": item_id, "description": ""})
        # Grant the item
        await self.bot.inventory_system.add_item(self.user_id, item_id, 1)
        # Reveal embed
        emoji = get_rarity_emoji(rarity)
        color = get_rarity_color(rarity)
        embed = create_embed(
            title=f"{emoji} You received: {item.get('name', item_id)}",
            description=item.get("description", ""),
            color=color,
            fields=[{"name": "Rarity", "value": rarity, "inline": True}],
        )
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

class LootboxCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lootbox", description="Open a lootbox from your inventory")
    @app_commands.describe(box_item_id="The ID of the lootbox item to open (e.g., basic_lootbox)")
    async def lootbox(self, interaction: discord.Interaction, box_item_id: str):
        user_id = interaction.user.id
        char = await self.bot.character_system.get_character(user_id)
        if not char:
            await interaction.response.send_message(embed=create_embed(title="❌ No Character", description="Create a character first with /character create", color=discord.Color.red()))
            return
        # Ensure player has the lootbox item and consume one
        inv = await self.bot.inventory_system.get_inventory(user_id)
        count = sum(1 for it in inv if it.get("id") == box_item_id for _ in range(it.get("quantity", 0)))
        if count <= 0:
            await interaction.response.send_message(embed=create_embed(title="🎁 No Lootboxes", description=f"You don't have `{box_item_id}`.", color=discord.Color.orange()))
            return
        await self.bot.inventory_system.remove_item(user_id, box_item_id, 1)
        # Send interactive view
        await interaction.response.send_message(embed=create_embed(title="🎁 Lootbox", description="Press Open to reveal your reward!", color=discord.Color.gold()), view=LootboxView(self.bot, user_id, box_item_id))

async def setup(bot):
    await bot.add_cog(LootboxCog(bot))
