import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.helpers import create_embed, format_number

logger = logging.getLogger(__name__)

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="character", description="Character management")
    async def character(self, interaction: discord.Interaction):
        """Main character management command"""
        user_id = interaction.user.id
        
        # Check if character exists
        character = await self.bot.character_system.get_character(user_id)
        
        if character:
            # Show character info with interactive buttons
            embed = self._create_character_embed(character)
            view = CharacterView(self.bot, user_id)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            # Show character creation interface
            embed = self._create_character_creation_embed()
            view = CharacterCreationView(self.bot, user_id)
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="cultivate", description="Cultivate a stat using Essence")
    @app_commands.describe(
        stat="Which stat to cultivate (hp, sp, attack, defense, speed, luck)"
    )
    async def cultivate(self, interaction: discord.Interaction, stat: str):
        """Cultivate a stat using Essence"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        
        # Get cultivation info
        cultivation_info = await self.bot.character_system.get_cultivation_info(user_id)
        if not cultivation_info["success"]:
            await interaction.followup.send(f"❌ {cultivation_info['message']}", ephemeral=True)
            return
        
        # Validate stat input
        stat = stat.lower()
        if stat not in cultivation_info["cultivation_info"]:
            valid_stats = ", ".join(cultivation_info["cultivation_info"].keys())
            await interaction.followup.send(f"❌ Invalid stat! Choose from: {valid_stats}", ephemeral=True)
            return
        
        stat_info = cultivation_info["cultivation_info"][stat]
        
        # Check if can cultivate
        if not stat_info["can_cultivate"]:
            await interaction.followup.send(
                f"❌ You need level {stat_info['min_level']} to cultivate {stat}", 
                ephemeral=True
            )
            return
        
        # Check Essence cost
        essence_cost = stat_info["essence_cost"]
        if cultivation_info["essence"] < essence_cost:
            await interaction.followup.send(
                f"❌ Not enough Essence! Need {essence_cost}, have {cultivation_info['essence']}", 
                ephemeral=True
            )
            return
        
        # Perform cultivation
        result = await self.bot.character_system.cultivate_stat(user_id, stat, essence_cost)
        if result["success"]:
            embed = create_embed(
                title="🌿 Cultivation Successful!",
                description=result["message"],
                color=discord.Color.green()
            )
            embed.add_field(
                name="New Stats",
                value=f"**{stat.title()}:** {stat_info['current_value']} → {result['new_value']}",
                inline=False
            )
            embed.add_field(
                name="Essence Remaining",
                value=f"🔮 {result['essence_remaining']}",
                inline=False
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)

    @app_commands.command(name="cultivation", description="View cultivation information and requirements")
    async def cultivation_info(self, interaction: discord.Interaction):
        """View cultivation information"""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        cultivation_info = await self.bot.character_system.get_cultivation_info(user_id)
        
        if not cultivation_info["success"]:
            await interaction.followup.send(f"❌ {cultivation_info['message']}", ephemeral=True)
            return
        
        embed = create_embed(
            title="🌿 Cultivation System",
            description="Use Essence to permanently improve your stats",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Essence Available",
            value=f"🔮 {cultivation_info['essence']}",
            inline=False
        )
        
        # Add stat information
        for stat, info in cultivation_info["cultivation_info"].items():
            status = "✅" if info["can_cultivate"] else "❌"
            level_req = f"Level {info['min_level']}" if not info["can_cultivate"] else "Ready"
            
            embed.add_field(
                name=f"{status} {stat.title()}",
                value=f"**Cost:** {info['essence_cost']} Essence\n"
                      f"**Bonus:** +{info['stat_increase']}\n"
                      f"**Current:** {info['current_value']}\n"
                      f"**Requirement:** {level_req}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

    def _create_character_embed(self, character):
        """Create character info embed"""
        embed = create_embed(
            title=f"{character['username']}'s Character",
            description=f"Level {character['level']} {character['character_class']}",
            color=discord.Color.blue()
        )
        
        # Basic stats
        stats_text = f"❤️ **HP:** {character['current_hp']}/{character['hp']}\n"
        stats_text += f"🔷 **SP:** {character['current_sp']}/{character['sp']}\n"
        stats_text += f"⚔️ **Attack:** {character['attack']}\n"
        stats_text += f"🛡️ **Defense:** {character['defense']}\n"
        stats_text += f"🏃 **Speed:** {character['speed']}\n"
        stats_text += f"🍀 **Luck:** {character['luck']}\n"
        stats_text += f"🔮 **Essence:** {character.get('essence', 0)}"
        
        embed.add_field(name="Stats", value=stats_text, inline=True)
        
        # Experience
        exp_text = f"📊 **Experience:** {character['experience']:,}\n"
        exp_text += f"🎯 **Next Level:** {character['next_level_exp']:,}\n"
        exp_text += f"📈 **Progress:** {character['level_progress']:.1f}%"
        
        embed.add_field(name="Experience", value=exp_text, inline=True)
        
        # Battle stats
        battles_won = character.get('battles_won', 0)
        battles_lost = character.get('battles_lost', 0)
        total_battles = battles_won + battles_lost
        win_rate = (battles_won / total_battles * 100) if total_battles > 0 else 0
        
        battle_text = f"⚔️ **Battles Won:** {battles_won}\n"
        battle_text += f"💀 **Battles Lost:** {battles_lost}\n"
        battle_text += f"🎖️ **Win Rate:** {win_rate:.1f}%"
        
        embed.add_field(name="Battle Record", value=battle_text, inline=True)
        
        return embed
    
    def _create_progress_bar(self, percentage: float, emoji: str) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"{emoji} {'█' * filled}{'░' * empty} {percentage:.0f}%"
    
    def _create_character_creation_embed(self):
        """Create character creation embed"""
        embed = create_embed(
            title="🎭 Create Your Character",
            description="Welcome to the RPG! Choose your character class and name to begin your adventure.",
            color=discord.Color.green()
        )
        
        # Class descriptions
        classes_text = "**Warrior** - High HP and Attack, perfect for frontline combat\n"
        classes_text += "**Mage** - High SP and Intelligence, master of magic\n"
        classes_text += "**Archer** - Balanced stats with high Speed and Agility\n"
        classes_text += "**Rogue** - High Speed and Luck, master of stealth"
        
        embed.add_field(name="🎯 Available Classes", value=classes_text, inline=False)
        
        return embed

class CharacterView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=600.0)  # Increased timeout to 10 minutes
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.primary, emoji="📊")
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        if character:
            embed = self._create_detailed_stats_embed(character)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Character not found!", ephemeral=True)

    @discord.ui.button(label="🌱 Cultivate", style=discord.ButtonStyle.success, emoji="🌱")
    async def cultivate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        if not character:
            await interaction.response.send_message("Character not found!", ephemeral=True)
            return
        
        # Show cultivation options
        embed = self._create_cultivation_embed(character)
        view = CultivationView(self.bot, self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📦 Inventory", style=discord.ButtonStyle.secondary, emoji="📦")
    async def view_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        embed = self._create_inventory_embed(inventory)
        view = InventoryView(self.bot, self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🎒 Equipment", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def view_equipment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        if character:
            equipment = character.get("equipment", {})
            embed = await self._create_equipment_embed(character, equipment)
            view = EquipmentView(self.bot, self.user_id)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("Character not found!", ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_character(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Refresh character data and update the main embed
        character = await self.bot.character_system.get_character(self.user_id)
        if character:
            embed = self._create_character_embed(character)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Character not found!", ephemeral=True)

    def _create_detailed_stats_embed(self, character):
        """Create detailed stats embed"""
        stats = character.get("stats", {})
        
        embed = create_embed(
            title=f"📊 {character['username']}'s Detailed Stats",
            description="Complete character statistics",
            color=discord.Color.blue()
        )
        
        # Core stats
        core_stats = f"❤️ **HP:** {stats.get('hp', 0)}/{stats.get('max_hp', 0)}\n"
        core_stats += f"⚡ **SP:** {stats.get('sp', 0)}/{stats.get('max_sp', 0)}\n"
        core_stats += f"⚔️ **Attack:** {stats.get('attack', 0)}\n"
        core_stats += f"🛡️ **Defense:** {stats.get('defense', 0)}\n"
        core_stats += f"🏃 **Speed:** {stats.get('speed', 0)}\n"
        core_stats += f"🧠 **Intelligence:** {stats.get('intelligence', 0)}\n"
        core_stats += f"🍀 **Luck:** {stats.get('luck', 0)}\n"
        core_stats += f"⚡ **Agility:** {stats.get('agility', 0)}"
        
        embed.add_field(name="📊 Core Stats", value=core_stats, inline=True)
        
        # Combat stats
        combat_stats = f"💰 **Gold:** {format_number(character.get('gold', 0))}\n"
        combat_stats += f"🏆 **Battles Won:** {character.get('battles_won', 0)}\n"
        combat_stats += f"💀 **Battles Lost:** {character.get('battles_lost', 0)}\n"
        combat_stats += f"🎯 **Total Battles:** {character.get('total_battles', 0)}\n"
        combat_stats += f"🏰 **Dungeons Completed:** {character.get('dungeons_completed', 0)}\n"
        combat_stats += f"👹 **Bosses Defeated:** {character.get('bosses_defeated', 0)}\n"
        combat_stats += f"🔄 **Rebirths:** {character.get('rebirths', 0)}"
        
        embed.add_field(name="🎮 Combat Stats", value=combat_stats, inline=True)
        
        return embed

    def _create_cultivation_embed(self, character):
        """Create cultivation embed"""
        essence = character.get("essence", 0)
        cultivation_levels = character.get("cultivation_levels", {})
        
        embed = create_embed(
            title="🌱 Cultivation System",
            description=f"Use your **{essence} Essence** to cultivate stats and become stronger!",
            color=discord.Color.green()
        )
        
        # Show current cultivation levels
        current_text = "**Current Cultivation Levels:**\n"
        for stat, level in cultivation_levels.items():
            current_text += f"🎯 {stat.title()}: {level}\n"
        
        embed.add_field(name="📊 Current Progress", value=current_text, inline=True)
        
        # Show cultivation costs
        costs_text = ""
        for stat in ["attack", "defense", "speed", "intelligence", "luck", "agility"]:
            current_level = cultivation_levels.get(stat, 0)
            if current_level < 10:  # Max cultivation level
                cost = self._calculate_cultivation_cost(current_level)
                costs_text += f"🎯 {stat.title()}: {cost} Essence\n"
            else:
                costs_text += f"🎯 {stat.title()}: MAX\n"
        
        embed.add_field(name="💰 Cultivation Costs", value=costs_text, inline=True)
        
        return embed
    
    def _calculate_cultivation_cost(self, current_level: int) -> int:
        """Calculate Essence cost for next cultivation level"""
        base_cost = 10
        level_multiplier = 1.5
        return int(base_cost * (level_multiplier ** current_level))

    def _create_skills_embed(self, skills):
        """Create skills embed"""
        if not skills:
            embed = create_embed(
                title="🎯 Skills",
                description="No skills learned yet. Level up to unlock skills!",
                color=discord.Color.orange()
            )
            return embed
        
        skills_text = ""
        for skill in skills:
            cooldown_text = f"⏳ {skill['cooldown']} turns" if skill['cooldown'] > 0 else "✅ Ready"
            skills_text += f"**{skill['name']}** - {skill['description']}\n"
            skills_text += f"💪 **Power:** {skill['power']} | ⚡ **SP Cost:** {skill['sp_cost']} | {cooldown_text}\n\n"
        
        embed = create_embed(
            title="🎯 Skills",
            description=skills_text,
            color=discord.Color.blue()
        )
        
        return embed

    def _create_inventory_embed(self, inventory):
        """Create inventory embed"""
        if not inventory:
            embed = create_embed(
                title="📦 Inventory",
                description="Your inventory is empty.",
                color=discord.Color.orange()
            )
            return embed
        
        items_text = ""
        for item in inventory[:10]:  # Show first 10 items
            items_text += f"📦 **{item['name']}** x{item['quantity']}\n"
            items_text += f"   {item.get('description', 'No description')}\n\n"
        
        if len(inventory) > 10:
            items_text += f"... and {len(inventory) - 10} more items"
        
        embed = create_embed(
            title="📦 Inventory",
            description=items_text,
            color=discord.Color.blue()
        )
        
        return embed

    async def _create_equipment_embed(self, character, equipment):
        """Create equipment embed with real-time stats"""
        # Get current stats including equipment bonuses
        current_stats = await self.bot.character_system.get_current_stats(character)
        
        embed = create_embed(
            title=f"{character['username']}'s Equipment",
            description="Current equipped items and stat bonuses",
            color=discord.Color.blue()
        )
        
        # Equipped items
        weapon = equipment.get("weapon", "None")
        armor = equipment.get("armor", "None")
        accessory = equipment.get("accessory", "None")
        
        equipped_text = f"⚔️ **Weapon:** {weapon}\n"
        equipped_text += f"🛡️ **Armor:** {armor}\n"
        equipped_text += f"💍 **Accessory:** {accessory}"
        
        embed.add_field(name="Equipped Items", value=equipped_text, inline=False)
        
        # Current stats with equipment bonuses
        stats_text = f"❤️ **HP:** {current_stats['current_hp']}/{current_stats['hp']}\n"
        stats_text += f"🔷 **SP:** {current_stats['current_sp']}/{current_stats['sp']}\n"
        stats_text += f"⚔️ **Attack:** {current_stats['attack']}\n"
        stats_text += f"🛡️ **Defense:** {current_stats['defense']}\n"
        stats_text += f"🏃 **Speed:** {current_stats['speed']}\n"
        stats_text += f"🍀 **Luck:** {current_stats['luck']}"
        
        embed.add_field(name="Current Stats (with equipment)", value=stats_text, inline=True)
        
        # Equipment bonuses
        bonuses_text = ""
        if equipment.get("weapon") and isinstance(equipment["weapon"], dict):
            for stat, bonus in equipment["weapon"].items():
                if stat in ["attack", "defense", "speed", "luck"] and isinstance(bonus, (int, float)) and bonus > 0:
                    bonuses_text += f"⚔️ **{stat.title()}:** +{bonus}\n"
        
        if equipment.get("armor") and isinstance(equipment["armor"], dict):
            for stat, bonus in equipment["armor"].items():
                if stat in ["attack", "defense", "speed", "luck"] and isinstance(bonus, (int, float)) and bonus > 0:
                    bonuses_text += f"🛡️ **{stat.title()}:** +{bonus}\n"
        
        if equipment.get("accessory") and isinstance(equipment["accessory"], dict):
            for stat, bonus in equipment["accessory"].items():
                if stat in ["attack", "defense", "speed", "luck"] and isinstance(bonus, (int, float)) and bonus > 0:
                    bonuses_text += f"💍 **{stat.title()}:** +{bonus}\n"
        
        if not bonuses_text:
            bonuses_text = "No stat bonuses from equipment"
        
        embed.add_field(name="Equipment Bonuses", value=bonuses_text, inline=True)
        
        return embed

class CharacterCreationView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id
        self._add_class_select()

    def _add_class_select(self):
        """Add class selection dropdown"""
        options = [
            discord.SelectOption(label="Warrior", description="High HP and Attack", value="Warrior"),
            discord.SelectOption(label="Mage", description="High SP and Intelligence", value="Mage"),
            discord.SelectOption(label="Archer", description="Balanced with high Speed", value="Archer"),
            discord.SelectOption(label="Rogue", description="High Speed and Luck", value="Rogue")
        ]
        
        select = discord.ui.Select(
            placeholder="🎯 Choose your class",
            options=options,
            custom_id="class_select"
        )
        select.callback = self._class_callback
        self.add_item(select)

    async def _class_callback(self, interaction: discord.Interaction):
        """Handle class selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        selected_class = interaction.data["values"][0]
        
        # Create character with selected class
        username = interaction.user.display_name
        character = await self.bot.character_system.create_character(self.user_id, username, selected_class)
        
        embed = create_embed(
            title="🎉 Character Created!",
            description=f"Welcome **{username}** the **{selected_class}**!\n\nYour adventure begins now!",
            color=discord.Color.green()
        )
        
        # Show character stats
        stats = character.get("stats", {})
        stats_text = f"❤️ **HP:** {stats.get('hp', 0)}/{stats.get('max_hp', 0)}\n"
        stats_text += f"⚡ **SP:** {stats.get('sp', 0)}/{stats.get('max_sp', 0)}\n"
        stats_text += f"⚔️ **Attack:** {stats.get('attack', 0)}\n"
        stats_text += f"🛡️ **Defense:** {stats.get('defense', 0)}\n"
        stats_text += f"🏃 **Speed:** {stats.get('speed', 0)}"
        
        embed.add_field(name="📊 Starting Stats", value=stats_text, inline=True)
        
        # Disable the view since character is created
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class SkillsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📚 Learn Skill", style=discord.ButtonStyle.primary, emoji="📚")
    async def learn_skill(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get available skills to learn
        character = await self.bot.character_system.get_character(self.user_id)
        if not character:
            await interaction.response.send_message("No character found!", ephemeral=True)
            return
        
        # Get all available skills
        all_skills = await self.bot.character_system.get_all_skills()
        learned_skills = character.get("skills", [])
        
        # Filter out already learned skills
        available_skills = []
        for skill in all_skills:
            if skill["name"] not in learned_skills:
                # Check level requirement
                if character.get("level", 1) >= skill.get("level_requirement", 1):
                    available_skills.append(skill)
        
        if not available_skills:
            await interaction.response.send_message("No new skills available to learn!", ephemeral=True)
            return
        
        # Create dropdown for skill selection
        options = []
        for skill in available_skills[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=skill["name"],
                description=f"Level {skill.get('level_requirement', 1)} • {skill.get('sp_cost', 0)} SP • {skill.get('type', 'Physical')}",
                value=skill["name"],
                emoji="📚"
            ))
        
        select = discord.ui.Select(
            placeholder="Select a skill to learn...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def skill_learn_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            skill_name = select.values[0]
            result = await self.bot.character_system.learn_skill(self.user_id, skill_name)
            
            if result["success"]:
                await interaction.response.send_message(f"📚 Learned skill: {skill_name}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Failed to learn skill: {result['message']}", ephemeral=True)
        
        select.callback = skill_learn_callback
        
        # Create a temporary view with the dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select a skill to learn:", view=view, ephemeral=True)

class InventoryView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📦 Use Item", style=discord.ButtonStyle.success, emoji="📦")
    async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get player's inventory
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        if not inventory:
            await interaction.response.send_message("Your inventory is empty!", ephemeral=True)
            return
        
        # Filter usable items
        usable_items = [item for item in inventory if item.get("type") in ["consumable", "potion", "scroll", "artifact"]]
        if not usable_items:
            await interaction.response.send_message("No usable items in your inventory!", ephemeral=True)
            return
        
        # Create dropdown for item selection
        options = []
        for item in usable_items[:25]:  # Discord limit
            item_type = item.get('type', 'Unknown')
            emoji_map = {
                'consumable': '🧪',
                'potion': '🧪',
                'scroll': '📜',
                'artifact': '🔮'
            }
            emoji = emoji_map.get(item_type, '📦')
            
            options.append(discord.SelectOption(
                label=f"{item['name']} x{item.get('quantity', 1)}",
                description=f"{item_type.title()} • {item.get('description', 'No description')}",
                value=item['name'],
                emoji=emoji
            ))
        
        select = discord.ui.Select(
            placeholder="Select an item to use...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def item_use_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            item_name = select.values[0]
            result = await self.bot.inventory_system.use_item(self.user_id, item_name)
            
            if result["success"]:
                await interaction.response.send_message(f"✅ Used item: {item_name}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Item usage failed: {result['message']}", ephemeral=True)
        
        select.callback = item_use_callback
        
        # Create a temporary view with the dropdown
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Select an item to use:", view=view, ephemeral=True)

class CultivationView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self._add_cultivation_dropdown()

    def _add_cultivation_dropdown(self):
        """Add cultivation stat selection dropdown"""
        options = [
            discord.SelectOption(label="Attack", description="Increase attack power", value="attack", emoji="⚔️"),
            discord.SelectOption(label="Defense", description="Increase defense", value="defense", emoji="🛡️"),
            discord.SelectOption(label="Speed", description="Increase speed", value="speed", emoji="🏃"),
            discord.SelectOption(label="Intelligence", description="Increase intelligence", value="intelligence", emoji="🧠"),
            discord.SelectOption(label="Luck", description="Increase luck", value="luck", emoji="🍀"),
            discord.SelectOption(label="Agility", description="Increase agility", value="agility", emoji="⚡")
        ]
        
        select = discord.ui.Select(
            placeholder="🌱 Choose stat to cultivate",
            options=options,
            custom_id="cultivation_select"
        )
        select.callback = self._cultivation_callback
        self.add_item(select)

    async def _cultivation_callback(self, interaction: discord.Interaction):
        """Handle cultivation selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        selected_stat = interaction.data["values"][0]
        
        # Attempt cultivation
        result = await self.bot.character_system.cultivate_stat(self.user_id, selected_stat)
        
        if result["success"]:
            # Update the cultivation embed
            character = await self.bot.character_system.get_character(self.user_id)
            embed = self._create_updated_cultivation_embed(character, result)
            
            # Disable the view after successful cultivation
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(f"❌ Cultivation failed: {result['message']}", ephemeral=True)
    
    def _create_updated_cultivation_embed(self, character, result):
        """Create updated cultivation embed after successful cultivation"""
        essence = character.get("essence", 0)
        cultivation_levels = character.get("cultivation_levels", {})
        
        embed = create_embed(
            title="🌱 Cultivation Successful!",
            description=f"**{result['message']}**\n\nYou now have **{essence} Essence** remaining!",
            color=discord.Color.green()
        )
        
        # Show updated cultivation levels
        current_text = "**Current Cultivation Levels:**\n"
        for stat, level in cultivation_levels.items():
            if level > 0:
                current_text += f"🎯 {stat.title()}: {level}\n"
        
        embed.add_field(name="📊 Updated Progress", value=current_text, inline=True)
        
        # Show next cultivation costs
        costs_text = ""
        for stat in ["attack", "defense", "speed", "intelligence", "luck", "agility"]:
            current_level = cultivation_levels.get(stat, 0)
            if current_level < 10:  # Max cultivation level
                cost = self._calculate_cultivation_cost(current_level)
                costs_text += f"🎯 {stat.title()}: {cost} Essence\n"
            else:
                costs_text += f"🎯 {stat.title()}: MAX\n"
        
        embed.add_field(name="💰 Next Cultivation Costs", value=costs_text, inline=True)
        
        return embed
    
    def _calculate_cultivation_cost(self, current_level: int) -> int:
        """Calculate Essence cost for next cultivation level"""
        base_cost = 10
        level_multiplier = 1.5
        return int(base_cost * (level_multiplier ** current_level))

class EquipmentView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="⚔️ Change Weapon", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def change_weapon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Show weapon selection
        embed = create_embed(title="⚔️ Select Weapon", description="Choose a weapon to equip", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=WeaponSelectView(self.bot, self.user_id))

    @discord.ui.button(label="🛡️ Change Armor", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def change_armor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Show armor selection
        embed = create_embed(title="🛡️ Select Armor", description="Choose armor to equip", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=ArmorSelectView(self.bot, self.user_id))

    @discord.ui.button(label="💍 Change Accessory", style=discord.ButtonStyle.primary, emoji="💍")
    async def change_accessory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Show accessory selection
        embed = create_embed(title="💍 Select Accessory", description="Choose an accessory to equip", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=AccessorySelectView(self.bot, self.user_id))

    @discord.ui.button(label="🔄 Refresh Stats", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Refresh and show updated equipment embed
        character = await self.bot.character_system.get_character(self.user_id)
        if character:
            equipment = character.get("equipment", {})
            embed = await self._create_updated_equipment_embed(character, equipment)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Character not found!", ephemeral=True)
    
    async def _create_updated_equipment_embed(self, character, equipment):
        """Create updated equipment embed with real-time stats"""
        # Get current stats including equipment bonuses
        current_stats = await self.bot.character_system.get_current_stats(character)
        
        embed = create_embed(
            title=f"{character['username']}'s Equipment",
            description="Current equipped items and stat bonuses",
            color=discord.Color.blue()
        )
        
        # Equipped items
        weapon = equipment.get("weapon", "None")
        armor = equipment.get("armor", "None")
        accessory = equipment.get("accessory", "None")
        
        equipped_text = f"⚔️ **Weapon:** {weapon}\n"
        equipped_text += f"🛡️ **Armor:** {armor}\n"
        equipped_text += f"💍 **Accessory:** {accessory}"
        
        embed.add_field(name="🎒 Equipped Items", value=equipped_text, inline=False)
        
        # Stat bonuses from equipment
        equipment_bonuses = character.get("equipment_bonuses", {})
        
        bonus_text = f"⚔️ **Attack Bonus:** +{equipment_bonuses.get('attack', 0)}\n"
        bonus_text += f"🛡️ **Defense Bonus:** +{equipment_bonuses.get('defense', 0)}\n"
        bonus_text += f"❤️ **HP Bonus:** +{equipment_bonuses.get('hp', 0)}\n"
        bonus_text += f"⚡ **SP Bonus:** +{equipment_bonuses.get('sp', 0)}\n"
        bonus_text += f"🎯 **Crit Bonus:** +{equipment_bonuses.get('crit', 0.0)}%\n"
        bonus_text += f"🍀 **Luck Bonus:** +{equipment_bonuses.get('luck', 0)}"
        
        embed.add_field(name="📊 Equipment Bonuses", value=bonus_text, inline=True)
        
        # Total stats (base + equipment + cultivation)
        total_text = f"⚔️ **Total Attack:** {current_stats.get('attack', 0)}\n"
        total_text += f"🛡️ **Total Defense:** {current_stats.get('defense', 0)}\n"
        total_text += f"❤️ **Total HP:** {current_stats.get('hp', 0)}/{current_stats.get('max_hp', 0)}\n"
        total_text += f"⚡ **Total SP:** {current_stats.get('sp', 0)}/{current_stats.get('max_sp', 0)}"
        
        embed.add_field(name="📈 Total Stats", value=total_text, inline=True)
        
        return embed

class WeaponSelectView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self._add_weapon_dropdown()

    def _add_weapon_dropdown(self):
        # This will be populated with actual weapons from inventory
        options = [
            discord.SelectOption(label="None", description="Unequip weapon", value="none"),
            discord.SelectOption(label="Steel Sword", description="Basic steel sword", value="steel_sword"),
            discord.SelectOption(label="Iron Axe", description="Heavy iron axe", value="iron_axe")
        ]
        select = discord.ui.Select(placeholder="Select weapon to equip", options=options)
        select.callback = self._weapon_selected
        self.add_item(select)

    async def _weapon_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Handle weapon equipping logic here
        await interaction.response.send_message("Weapon selection not fully implemented yet", ephemeral=True)

class ArmorSelectView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

class AccessorySelectView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

# Modals
class SkillLearningModal(discord.ui.Modal, title="Learn Skill"):
    skill_name = discord.ui.TextInput(label="Skill Name", placeholder="Enter skill name to learn")
    
    def __init__(self, bot, user_id: int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
    
    async def on_submit(self, interaction: discord.Interaction):
        skill_name = self.skill_name.value
        result = await self.bot.character_system.learn_skill(self.user_id, skill_name)
        
        if result["success"]:
            await interaction.response.send_message(f"📚 Learned skill: {skill_name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Skill learning failed: {result['message']}", ephemeral=True)

class ItemUsageModal(discord.ui.Modal, title="Use Item"):
    item_name = discord.ui.TextInput(label="Item Name", placeholder="Enter item name to use")
    
    def __init__(self, bot, user_id: int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
    
    async def on_submit(self, interaction: discord.Interaction):
        item_name = self.item_name.value
        result = await self.bot.inventory_system.use_item(self.user_id, item_name)
        
        if result["success"]:
            await interaction.response.send_message(f"✅ Used item: {item_name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Item usage failed: {result['message']}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))

