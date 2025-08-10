"""
🎯 Interactive Dropdown Components
Ultra-low latency dropdown menus for seamless user experience
"""

import discord
from discord import app_commands
from typing import List, Dict, Any, Optional, Callable
import asyncio

class SkillDropdown(discord.ui.Select):
    """Dropdown for skill selection"""
    def __init__(self, skills: List[Dict], callback: Callable):
        options = []
        for skill in skills:
            options.append(discord.SelectOption(
                label=skill['name'],
                description=f"Level {skill.get('level', 1)} • {skill.get('type', 'Physical')} • {skill.get('power', 0)} power",
                value=skill['name'],
                emoji="⚔️"
            ))
        
        super().__init__(
            placeholder="Select a skill to use...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class ItemDropdown(discord.ui.Select):
    """Dropdown for item selection"""
    def __init__(self, items: List[Dict], callback: Callable):
        options = []
        for item in items:
            item_type = item.get('type', 'Unknown')
            emoji_map = {
                'consumable': '🧪',
                'weapon': '⚔️',
                'armor': '🛡️',
                'accessory': '💍',
                'potion': '🧪',
                'scroll': '📜',
                'artifact': '🔮'
            }
            emoji = emoji_map.get(item_type, '📦')
            
            options.append(discord.SelectOption(
                label=item['name'],
                description=f"{item_type.title()} • {item.get('description', 'No description')}",
                value=item['name'],
                emoji=emoji
            ))
        
        super().__init__(
            placeholder="Select an item to use...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class ElementDropdown(discord.ui.Select):
    """Dropdown for elemental attack selection"""
    def __init__(self, callback: Callable):
        options = [
            discord.SelectOption(label="Fire", description="Burns enemies over time", value="fire", emoji="🔥"),
            discord.SelectOption(label="Ice", description="Freezes and slows enemies", value="ice", emoji="❄️"),
            discord.SelectOption(label="Lightning", description="Shocks and stuns enemies", value="lightning", emoji="⚡"),
            discord.SelectOption(label="Poison", description="Poisons enemies over time", value="poison", emoji="☠️"),
            discord.SelectOption(label="Holy", description="Effective against undead", value="holy", emoji="✨"),
            discord.SelectOption(label="Shadow", description="Dark magic damage", value="shadow", emoji="🌑")
        ]
        
        super().__init__(
            placeholder="Select an element...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class LearnableSkillDropdown(discord.ui.Select):
    """Dropdown for learning new skills"""
    def __init__(self, available_skills: List[Dict], callback: Callable):
        options = []
        for skill in available_skills:
            cost = skill.get('sp_cost', 0)
            level_req = skill.get('level_requirement', 1)
            options.append(discord.SelectOption(
                label=skill['name'],
                description=f"Level {level_req} • {cost} SP • {skill.get('type', 'Physical')}",
                value=skill['name'],
                emoji="📚"
            ))
        
        super().__init__(
            placeholder="Select a skill to learn...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class MonsterDropdown(discord.ui.Select):
    """Dropdown for monster selection"""
    def __init__(self, monsters: List[Dict], callback: Callable):
        options = []
        for monster in monsters:
            level = monster.get('level', 1)
            difficulty = monster.get('difficulty', 'Normal')
            options.append(discord.SelectOption(
                label=monster['name'],
                description=f"Level {level} • {difficulty} • {monster.get('hp', 100)} HP",
                value=monster['name'],
                emoji="👹"
            ))
        
        super().__init__(
            placeholder="Select a monster to fight...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class DungeonDropdown(discord.ui.Select):
    """Dropdown for dungeon selection"""
    def __init__(self, dungeons: List[Dict], callback: Callable):
        options = []
        for dungeon in dungeons:
            floors = len(dungeon.get('floors', {})) if isinstance(dungeon.get('floors'), dict) else dungeon.get('floors', 1)
            difficulty = dungeon.get('difficulty', 'Normal')
            options.append(discord.SelectOption(
                label=dungeon['name'],
                description=f"{floors} floors • {difficulty} • {dungeon.get('description', 'No description')}",
                value=dungeon['id'],
                emoji="🏰"
            ))
        
        super().__init__(
            placeholder="Select a dungeon to explore...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class FactionDropdown(discord.ui.Select):
    """Dropdown for faction selection"""
    def __init__(self, factions: List[Dict], callback: Callable):
        options = []
        for faction in factions:
            members = len(faction.get('members', []))
            options.append(discord.SelectOption(
                label=faction['name'],
                description=f"{members} members • {faction.get('description', 'No description')}",
                value=faction['id'],
                emoji=faction.get('emoji', '🏳️')
            ))
        
        super().__init__(
            placeholder="Select a faction to join...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class QuantityDropdown(discord.ui.Select):
    """Dropdown for quantity selection"""
    def __init__(self, max_quantity: int, callback: Callable):
        options = []
        # Create options for quantities 1, 5, 10, 25, 50, 100, or max
        quantities = [1, 5, 10, 25, 50, 100]
        if max_quantity > 100:
            quantities.append(max_quantity)
        
        for qty in quantities:
            if qty <= max_quantity:
                options.append(discord.SelectOption(
                    label=f"{qty}",
                    description=f"Quantity: {qty}",
                    value=str(qty),
                    emoji="📦"
                ))
        
        super().__init__(
            placeholder="Select quantity...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, int(self.values[0]))

class EnhancedView(discord.ui.View):
    """Base class for views with dropdown support"""
    def __init__(self, timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.dropdowns = {}

    def add_dropdown(self, dropdown: discord.ui.Select):
        """Add a dropdown to the view"""
        self.add_item(dropdown)
        return dropdown

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Override to add custom interaction validation"""
        return True

class CombatDropdownView(EnhancedView):
    """Enhanced combat view with dropdowns"""
    def __init__(self, bot, battle_id: str, user_id: int):
        super().__init__()
        self.bot = bot
        self.battle_id = battle_id
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return False
        return True

    async def _skill_callback(self, interaction: discord.Interaction, skill_name: str):
        """Handle skill selection"""
        result = await self.bot.combat_system.use_skill(self.battle_id, self.user_id, skill_name)
        
        if result["success"]:
            await interaction.response.send_message(f"✅ Used skill: {skill_name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Skill failed: {result['message']}", ephemeral=True)

    async def _item_callback(self, interaction: discord.Interaction, item_name: str):
        """Handle item selection"""
        result = await self.bot.combat_system.use_item(self.battle_id, self.user_id, item_name)
        
        if result["success"]:
            await interaction.response.send_message(f"✅ Used item: {item_name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Item failed: {result['message']}", ephemeral=True)

    async def _element_callback(self, interaction: discord.Interaction, element: str):
        """Handle elemental attack selection"""
        result = await self.bot.advanced_combat_system.elemental_attack(self.battle_id, self.user_id, element)
        
        if result["success"]:
            await interaction.response.send_message(f"✨ Used {element} attack!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Elemental attack failed: {result['message']}", ephemeral=True)

    def add_skill_dropdown(self, skills: List[Dict]):
        """Add skill dropdown to view"""
        if skills:
            dropdown = SkillDropdown(skills, self._skill_callback)
            self.add_dropdown(dropdown)

    def add_item_dropdown(self, items: List[Dict]):
        """Add item dropdown to view"""
        if items:
            dropdown = ItemDropdown(items, self._item_callback)
            self.add_dropdown(dropdown)

    def add_element_dropdown(self):
        """Add element dropdown to view"""
        dropdown = ElementDropdown(self._element_callback)
        self.add_dropdown(dropdown)
