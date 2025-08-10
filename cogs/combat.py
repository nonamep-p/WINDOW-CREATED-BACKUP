import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List
import random
import asyncio

from utils.helpers import create_embed, format_number
from utils.dropdowns import CombatDropdownView, SkillDropdown, ItemDropdown, ElementDropdown, LearnableSkillDropdown
from systems.combat import CombatSystem
from systems.advanced_combat import AdvancedCombatSystem

logger = logging.getLogger(__name__)

# Owner ID for special privileges
OWNER_ID = 1297013439125917766

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hunt", description="Hunt monsters for XP and loot")
    async def hunt(self, interaction: discord.Interaction):
        """Hunt monsters for XP and loot"""
        user_id = interaction.user.id
        
        # Get or create character
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character create`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already in battle
        existing_battle = await self.bot.combat_system.get_user_battle(user_id)
        if existing_battle:
            embed = create_embed(
                title="⚔️ Battle In Progress",
                description="You're already in a battle! Finish it first or flee.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get a random monster for hunting
        monsters_data = await self.bot.db.load_monsters()
        if not monsters_data:
            await interaction.response.send_message("No monsters available for hunting!", ephemeral=True)
            return
        
        # Select a random monster
        monster_name = random.choice(list(monsters_data.keys()))
        monster = monsters_data[monster_name]
        
        # Start hunting session
        result = await self.bot.combat_system.start_battle(user_id, monster)
        
        if result["success"]:
            battle = result["battle"]
            embed = self._create_enhanced_battle_embed(battle, character)
            view = EnhancedHuntView(self.bot, battle["battle_id"], user_id)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            embed = create_embed(
                title="❌ Hunt Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="equip", description="Equip weapons, armor, or accessories")
    @app_commands.describe(item_name="Name of the item to equip")
    async def equip(self, interaction: discord.Interaction, item_name: str):
        """Equip an item from inventory"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character create`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get player's inventory
        inventory = await self.bot.inventory_system.get_inventory(user_id)
        if not inventory:
            await interaction.response.send_message("Your inventory is empty!", ephemeral=True)
            return
        
        # Find the item
        item_to_equip = None
        for item in inventory:
            if item['name'].lower() == item_name.lower():
                item_to_equip = item
                break
        
        if not item_to_equip:
            await interaction.response.send_message(f"Item '{item_name}' not found in your inventory!", ephemeral=True)
            return
        
        # Check if item is equippable
        if item_to_equip.get('type') not in ['Weapon', 'Armor', 'Accessory']:
            await interaction.response.send_message("This item cannot be equipped!", ephemeral=True)
            return
        
        # Equip the item
        result = await self.bot.character_system.equip_item(user_id, item_to_equip)
        
        if result["success"]:
            embed = create_embed(
                title="✅ Item Equipped!",
                description=f"You equipped **{item_to_equip['name']}**!\n\n{result['message']}",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Equip Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="equipment", description="View your equipped items and stats")
    async def equipment(self, interaction: discord.Interaction):
        """View equipped items"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character create`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = self._create_equipment_embed(character)
        view = EquipmentView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="giveowner", description="Owner command to give resources")
    @app_commands.describe(
        target="Target user",
        resource_type="Type of resource (gold, xp, item, setup)",
        resource_name="Name/ID of resource (for items)",
        amount="Amount to give"
    )
    async def give_owner(self, interaction: discord.Interaction, target: discord.User, resource_type: str, amount: int = 1, resource_name: str = None):
        """Owner command to give resources"""
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        target_id = target.id
        result = None
        
        if resource_type.lower() == "setup":
            # Give owner full setup for testing
            character = await self.bot.character_system.get_character(target_id)
            if character:
                # Max resources
                character["gold"] = 999999
                character["xp"] = 50000
                character["level"] = 25
                
                # Add all skills
                character["skills"] = ["slash", "guard_break", "fire_bolt", "smite", "ice_lance", "shock", "heal", "shield"]
                character["skill_cooldowns"] = {}
                
                # Max ultimate
                character["ultimate_charge"] = 100
                
                # Add crafting skills
                character["crafting_skills"] = {
                    "blacksmithing": 10,
                    "alchemy": 10,
                    "enchanting": 10,
                    "cooking": 10,
                    "tailoring": 10
                }
                
                await self.bot.db.save_player(target_id, character)
                
                # Add starter items
                starter_items = [
                    ("health_potion", 50),
                    ("mana_potion", 50),
                    ("power_elixir", 20),
                    ("barrier_potion", 20),
                    ("smoke_bomb", 10),
                    ("steel_sword", 1),
                    ("guardian_plate", 1),
                    ("mystic_ring", 1)
                ]
                
                for item_id, quantity in starter_items:
                    await self.bot.inventory_system.add_item(target_id, item_id, quantity)
                
                result = {"success": True, "message": "Full owner setup completed! Gold, XP, skills, items, and equipment added."}
            else:
                result = {"success": False, "message": "Character not found. Create a character first."}
        
        elif resource_type.lower() == "gold":
            character = await self.bot.character_system.get_character(target_id)
            if character:
                character["gold"] = character.get("gold", 0) + amount
                await self.bot.db.save_player(target_id, character)
                result = {"success": True, "message": f"Added {amount} gold"}
            else:
                result = {"success": False, "message": "Character not found"}
        
        elif resource_type.lower() == "xp":
            character = await self.bot.character_system.get_character(target_id)
            if character:
                character["xp"] = character.get("xp", 0) + amount
                await self.bot.character_system._check_level_up(target_id, character)
                await self.bot.db.save_player(target_id, character)
                result = {"success": True, "message": f"Added {amount} XP"}
            else:
                result = {"success": False, "message": "Character not found"}
        
        elif resource_type.lower() == "item" and resource_name:
            items_data = await self.bot.db.load_items()
            if resource_name in items_data:
                await self.bot.inventory_system.add_item(target_id, resource_name, amount)
                result = {"success": True, "message": f"Added {amount}x {items_data[resource_name]['name']}"}
            else:
                result = {"success": False, "message": "Item not found"}
        
        else:
            result = {"success": False, "message": "Invalid resource type. Use: gold, xp, item, setup"}
        
        if result["success"]:
            embed = create_embed(
                title="✅ Owner Command Executed",
                description=f"Successfully gave {target.mention} {result['message']}",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Owner Command Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _create_enhanced_battle_embed(self, battle, character):
        """Create an enhanced battle embed with clean formatting and equipment integration"""
        player = battle["player"]
        monster = battle["monster"]
        
        # Get equipped items for stat bonuses
        equipment = character.get("equipment", {})
        weapon = equipment.get("weapon")
        armor = equipment.get("armor")
        accessory = equipment.get("accessory")
        
        # Combat log in a clean box format - MUCH cleaner
        battle_log = battle.get("battle_log", [])
        recent_actions = battle_log[-3:] if len(battle_log) > 3 else battle_log
        
        log_text = "```yaml\n"
        log_text += "=== COMBAT LOG ===\n"
        for i, action in enumerate(recent_actions, 1):
            # Clean up the action text
            clean_action = action.replace("**", "").replace("*", "")
            if "CRITICAL" in clean_action:
                log_text += f"{i}. [CRIT] {clean_action}\n"
            elif "MISS" in clean_action:
                log_text += f"{i}. [MISS] {clean_action}\n"
            elif "heal" in clean_action.lower():
                log_text += f"{i}. [HEAL] {clean_action}\n"
            elif "skill" in clean_action.lower() or "used" in clean_action.lower():
                log_text += f"{i}. [SKILL] {clean_action}\n"
            elif "item" in clean_action.lower():
                log_text += f"{i}. [ITEM] {clean_action}\n"
            else:
                log_text += f"{i}. [ATK] {clean_action}\n"
        
        if not recent_actions:
            log_text += "1. [START] Battle initiated!\n"
        
        log_text += "==================\n```"
        
        # Enhanced stats with equipment bonuses - CLEANER FORMAT
        player_max_hp = player.get('max_hp') or player.get('hp') or 1
        player_max_sp = player.get('max_sp') or player.get('sp') or 1
        monster_max_hp = monster.get('max_hp') or monster.get('hp') or 1

        hp_percent = (player.get('current_hp', 0) / max(1, player_max_hp)) * 100
        sp_percent = (player.get('current_sp', 0) / max(1, player_max_sp)) * 100
        monster_hp_percent = (monster.get('current_hp', 0) / max(1, monster_max_hp)) * 100
        
        # Create clean progress bars
        hp_bar = self._create_clean_progress_bar(hp_percent)
        sp_bar = self._create_clean_progress_bar(sp_percent)
        monster_hp_bar = self._create_clean_progress_bar(monster_hp_percent)
        
        # Status effects with enhanced formatting
        player_statuses = player.get("statuses", [])
        monster_statuses = monster.get("statuses", [])
        
        # Player stats - MUCH cleaner
        player_stats = f"**❤️ HP:** {player.get('current_hp',0)}/{player_max_hp} {hp_bar}\n"
        player_stats += f"**⚡ SP:** {player.get('current_sp',0)}/{player_max_sp} {sp_bar}\n"
        
        if player.get('shield', 0) > 0:
            player_stats += f"**🛡️ Shield:** {player.get('shield', 0)}\n"
        
        player_stats += f"**⚔️ ATK:** {player.get('attack',0)} | **🛡️ DEF:** {player.get('defense',0)}\n"
        
        # Add status effects if any (enhanced display)
        if player_statuses:
            status_list = []
            for status in player_statuses[:3]:  # Show max 3 effects
                if isinstance(status, dict):
                    status_id = status.get('id', status.get('status', 'unknown'))
                    duration = status.get('duration', 0)
                    # Get status definition from combat system
                    status_def = self.bot.combat_system.status_effects.get(status_id, {})
                    status_name = status_def.get('name', status_id.title())
                    status_list.append(f"{status_name}({duration})")
                else:
                    # Legacy format
                    status_list.append(f"✨{status}")
            if status_list:
                player_stats += f"**🔮 Effects:** {', '.join(status_list)}\n"
        
        # Monster stats - MUCH cleaner
        monster_stats = f"**❤️ HP:** {monster.get('current_hp',0)}/{monster_max_hp} {monster_hp_bar}\n"
        
        if monster.get('shield', 0) > 0:
            monster_stats += f"**🛡️ Shield:** {monster.get('shield', 0)}\n"
        
        monster_stats += f"**⚔️ ATK:** {monster.get('attack',0)} | **🛡️ DEF:** {monster.get('defense',0)}\n"
        
        # Add monster status effects (enhanced display)
        if monster_statuses:
            status_list = []
            for status in monster_statuses[:3]:  # Show max 3 effects
                if isinstance(status, dict):
                    status_id = status.get('id', status.get('status', 'unknown'))
                    duration = status.get('duration', 0)
                    # Get status definition from combat system
                    status_def = self.bot.combat_system.status_effects.get(status_id, {})
                    status_name = status_def.get('name', status_id.title())
                    status_list.append(f"{status_name}({duration})")
                else:
                    # Legacy format
                    status_list.append(f"✨{status}")
            if status_list:
                monster_stats += f"**🔮 Effects:** {', '.join(status_list)}\n"
        
        # Equipment display - CLEANER
        equipment_text = ""
        if weapon:
            equipment_text += f"⚔️ {weapon.get('name', 'None')}\n"
        if armor:
            equipment_text += f"🛡️ {armor.get('name', 'None')}\n"
        if accessory:
            equipment_text += f"💍 {accessory.get('name', 'None')}\n"
        
        if not equipment_text:
            equipment_text = "No equipment equipped"
        
        # Battle info
        combo_count = battle.get("combo_count", 0)
        battle_info = f"**🎯 Turn:** {battle['turn']} | **⚡ Round:** {battle.get('round', 1)}\n"
        if combo_count > 0:
            battle_info += f"**🔥 Combo:** {combo_count}x\n"
        
        # Create the embed with cleaner layout
        embed = create_embed(
            title=f"⚔️ {character['username']} vs {monster['name']}",
            description=battle_info,
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👤 Player", value=player_stats, inline=True)
        embed.add_field(name="👹 Monster", value=monster_stats, inline=True)
        embed.add_field(name="🎒 Equipment", value=equipment_text, inline=True)
        embed.add_field(name="📜 Combat Log", value=log_text, inline=False)
        
        # Add instruction footer
        embed.set_footer(text="Use the buttons below to take actions in combat!")
        
        return embed
    
    def _create_clean_progress_bar(self, percentage: float) -> str:
        """Create a clean progress bar"""
        if percentage >= 75:
            return "🟩🟩🟩🟩"
        elif percentage >= 50:
            return "🟨🟨🟨⬜"
        elif percentage >= 25:
            return "🟧🟧⬜⬜"
        else:
            return "🟥⬜⬜⬜"

    def _create_equipment_embed(self, character):
        """Create equipment display embed"""
        equipment = character.get("equipment", {})
        stats = character.get("stats", {})
        
        # Base stats
        base_attack = stats.get("base_attack", stats.get("attack", 0))
        base_defense = stats.get("base_defense", stats.get("defense", 0))
        base_hp = stats.get("base_max_hp", stats.get("max_hp", 0))
        base_sp = stats.get("base_max_sp", stats.get("max_sp", 0))
        
        # Calculate equipment bonuses
        weapon_bonus = {"attack": 0, "crit": 0}
        armor_bonus = {"defense": 0, "hp": 0}
        accessory_bonus = {"sp": 0, "luck": 0}
        
        weapon = equipment.get("weapon")
        armor = equipment.get("armor")
        accessory = equipment.get("accessory")
        
        if weapon and weapon.get("effects"):
            effects = weapon["effects"]
            weapon_bonus["attack"] = effects.get("atk", 0)
            weapon_bonus["crit"] = effects.get("crit_base", 0) * 100
        
        if armor and armor.get("effects"):
            effects = armor["effects"]
            armor_bonus["defense"] = effects.get("defense", 0)
            armor_bonus["hp"] = effects.get("hp%", 0) * base_hp if "hp%" in effects else effects.get("hp", 0)
        
        if accessory and accessory.get("effects"):
            effects = accessory["effects"]
            accessory_bonus["sp"] = effects.get("sp%", 0) * base_sp if "sp%" in effects else effects.get("sp", 0)
            accessory_bonus["luck"] = effects.get("luck", 0)
        
        embed = create_embed(
            title=f"🎒 {character['username']}'s Equipment",
            description="Current equipped items and stat bonuses",
            color=discord.Color.gold()
        )
        
        # Equipment slots
        weapon_text = weapon["name"] if weapon else "None"
        armor_text = armor["name"] if armor else "None"
        accessory_text = accessory["name"] if accessory else "None"
        
        equipment_display = f"⚔️ **Weapon:** {weapon_text}\n"
        equipment_display += f"🛡️ **Armor:** {armor_text}\n"
        equipment_display += f"💍 **Accessory:** {accessory_text}"
        
        # Stat bonuses
        bonus_display = f"⚔️ **Attack Bonus:** +{weapon_bonus['attack']}\n"
        bonus_display += f"🛡️ **Defense Bonus:** +{armor_bonus['defense']}\n"
        bonus_display += f"❤️ **HP Bonus:** +{armor_bonus['hp']:.0f}\n"
        bonus_display += f"⚡ **SP Bonus:** +{accessory_bonus['sp']:.0f}\n"
        bonus_display += f"💥 **Crit Bonus:** +{weapon_bonus['crit']:.1f}%\n"
        bonus_display += f"🍀 **Luck Bonus:** +{accessory_bonus['luck']}"
        
        # Total stats
        total_attack = base_attack + weapon_bonus["attack"]
        total_defense = base_defense + armor_bonus["defense"]
        total_hp = base_hp + armor_bonus["hp"]
        total_sp = base_sp + accessory_bonus["sp"]
        
        total_display = f"⚔️ **Total Attack:** {total_attack}\n"
        total_display += f"🛡️ **Total Defense:** {total_defense}\n"
        total_display += f"❤️ **Total HP:** {total_hp:.0f}\n"
        total_display += f"⚡ **Total SP:** {total_sp:.0f}"
        
        embed.add_field(name="🎒 Equipped Items", value=equipment_display, inline=True)
        embed.add_field(name="📈 Bonuses", value=bonus_display, inline=True)
        embed.add_field(name="📊 Total Stats", value=total_display, inline=True)
        
        return embed

class EnhancedHuntView(discord.ui.View):
    def __init__(self, bot, battle_id: str, user_id: int):
        super().__init__(timeout=120.0)
        self.bot = bot
        self.battle_id = battle_id
        self.user_id = user_id
        self.cog = bot.get_cog("CombatCog")

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, emoji="⚔️", row=0)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        result = await self.bot.combat_system.perform_action(self.battle_id, "attack")
        await self._update_battle_message(interaction, result)

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.primary, emoji="🛡️", row=0)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        result = await self.bot.combat_system.perform_action(self.battle_id, "defend")
        await self._update_battle_message(interaction, result)

    @discord.ui.button(label="🎯 Skills", style=discord.ButtonStyle.success, emoji="🎯", row=0)
    async def skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        # Show skills selection
        character = await self.bot.character_system.get_character(self.user_id)
        if not character or not character.get("skills"):
            await interaction.response.send_message("❌ You don't have any skills yet!", ephemeral=True)
            return
        
        # Create skills dropdown
        skills_data = await self.bot.db.load_json_data("skills.json")
        skill_options = []
        
        for skill_id in character["skills"][:25]:  # Discord limit
            if skill_id in skills_data:
                skill = skills_data[skill_id]
                cooldown = character.get("skill_cooldowns", {}).get(skill_id, 0)
                sp_cost = skill.get('sp_cost', 0)
                
                # Check if skill is available
                current_sp = await self._get_battle_sp()
                can_use = cooldown == 0 and current_sp >= sp_cost
                
                status = "✅" if can_use else "❌" if cooldown > 0 else "⚡"
                cooldown_text = f" (CD: {cooldown})" if cooldown > 0 else ""
                sp_text = f" (SP: {sp_cost})"
                
                skill_options.append(discord.SelectOption(
                    label=f"{status} {skill['name']}{cooldown_text}",
                    description=f"{skill['description'][:47]}{sp_text}",
                    value=skill_id,
                    emoji="🎯"
                ))
        
        if skill_options:
            embed = create_embed(
                title="🎯 Select Skill",
                description="Choose a skill to use in battle:",
                color=discord.Color.blue()
            )
            
            view = SkillSelectionView(self.bot, self.battle_id, self.user_id, skill_options)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message("❌ No skills available!", ephemeral=True)

    @discord.ui.button(label="🧪 Items", style=discord.ButtonStyle.success, emoji="🧪", row=0)
    async def items(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        # Show items selection
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        if not inventory:
            await interaction.response.send_message("❌ Your inventory is empty!", ephemeral=True)
            return
        
        usable_items = [item for item in inventory if item.get("type") in ["Consumable", "consumable", "potion", "scroll"]]
        if not usable_items:
            await interaction.response.send_message("❌ You don't have any usable items!", ephemeral=True)
            return
        
        # Create items dropdown
        item_options = []
        for item in usable_items[:25]:  # Discord limit
            quantity = item.get('quantity', 1)
            status = "✅" if quantity > 0 else "❌"
            
            item_options.append(discord.SelectOption(
                label=f"{status} {item['name']} (x{quantity})",
                description=item.get("description", "Use this item")[:50],
                value=item.get("id", item.get("name")),
                emoji="🧪"
            ))
        
        embed = create_embed(
            title="🧪 Select Item",
            description="Choose an item to use in battle:",
            color=discord.Color.green()
        )
        
        view = ItemSelectionView(self.bot, self.battle_id, self.user_id, item_options)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🏃 Flee", style=discord.ButtonStyle.secondary, emoji="🏃", row=1)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        result = await self.bot.combat_system.perform_action(self.battle_id, "flee")
        await self._update_battle_message(interaction, result)

    @discord.ui.button(label="🔥 Ultimate", style=discord.ButtonStyle.danger, emoji="🔥", row=1)
    async def ultimate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This battle is not for you!", ephemeral=True)
            return
        
        # Check if ultimate is ready
        ultimate_ready = await self.bot.character_system.is_ultimate_ready(self.user_id)
        if ultimate_ready:
            result = await self.bot.combat_system.use_ultimate(self.battle_id, self.user_id)
            await self._update_battle_message(interaction, result)
        else:
            character = await self.bot.character_system.get_character(self.user_id)
            charge = character.get("ultimate_charge", 0)
            await interaction.response.send_message(f"🔥 Ultimate not ready! Current charge: {charge}%\nContinue fighting to charge it.", ephemeral=True)

    async def _get_battle_sp(self):
        """Get current SP from battle"""
        try:
            battle = self.bot.combat_system.active_battles.get(self.battle_id)
            if battle:
                return battle["player"].get("current_sp", 0)
            return 0
        except:
            return 0

    async def _update_battle_message(self, interaction: discord.Interaction, result: dict):
        """Update the battle message with new state"""
        if result["success"]:
            battle = result["battle"]
            character = await self.bot.character_system.get_character(self.user_id)
            
            if battle["status"] == "completed":
                # Battle completed
                winner = battle.get("winner", "unknown")
                if winner == "player":
                    result_msg = "Victory! You defeated the enemy!"
                elif winner == "monster":
                    result_msg = "Defeat! The enemy has defeated you!"
                else:
                    result_msg = result.get('message', 'Battle completed!')
                
                embed = create_embed(
                    title="🏁 Battle Complete!",
                    description=f"**Result:** {result_msg}",
                    color=discord.Color.green() if winner == "player" else discord.Color.red()
                )
                
                # Add rewards info if available
                if "rewards" in result:
                    rewards = result["rewards"]
                    reward_text = ""
                    if rewards.get("xp"):
                        reward_text += f"🌟 **XP:** +{rewards['xp']}\n"
                    if rewards.get("gold"):
                        reward_text += f"💰 **Gold:** +{rewards['gold']}\n"
                    if rewards.get("items"):
                        for item in rewards["items"]:
                            reward_text += f"📦 **Item:** {item['name']} x{item.get('quantity', 1)}\n"
                    
                    if reward_text:
                        embed.add_field(name="🎁 Rewards", value=reward_text, inline=False)
                
                # Disable all buttons
                for child in self.children:
                    child.disabled = True
            else:
                embed = self.cog._create_enhanced_battle_embed(battle, character)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(f"❌ Action failed: {result['message']}", ephemeral=True)

class SkillSelectionView(discord.ui.View):
    def __init__(self, bot, battle_id: str, user_id: int, skill_options: list):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.battle_id = battle_id
        self.user_id = user_id

        # Add skill selection dropdown
        skill_select = discord.ui.Select(
            placeholder="🎯 Choose a skill to use...",
            options=skill_options,
            custom_id="skill_select"
        )
        skill_select.callback = self._skill_callback
        self.add_item(skill_select)

    async def _skill_callback(self, interaction: discord.Interaction):
        """Handle skill selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        skill_id = interaction.data["values"][0]
        result = await self.bot.combat_system.use_skill(self.battle_id, self.user_id, skill_id)
        
        if result["success"]:
            # Get updated battle state
            battle = await self.bot.combat_system.get_battle_status(self.battle_id)
            if battle:
                # Get character for embed creation
                character = await self.bot.character_system.get_character(self.user_id)
                if character:
                    # Create updated battle embed
                    embed = self.bot.get_cog("CombatCog")._create_enhanced_battle_embed(battle, character)
                    # Update the main battle message
                    await interaction.message.edit(embed=embed)
                    
                    # Show skill success message
                    success_embed = create_embed(
                        title="🎯 Skill Used!",
                        description=f"✅ {result['message']}",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=success_embed, ephemeral=True)
                else:
                    await interaction.response.send_message("✅ Skill used! Battle updated.", ephemeral=True)
            else:
                await interaction.response.send_message("✅ Skill used! Battle updated.", ephemeral=True)
        else:
            embed = create_embed(
                title="❌ Skill Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

class ItemSelectionView(discord.ui.View):
    def __init__(self, bot, battle_id: str, user_id: int, item_options: list):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.battle_id = battle_id
        self.user_id = user_id
        
        # Add item selection dropdown
        item_select = discord.ui.Select(
            placeholder="🧪 Choose an item to use...",
            options=item_options,
            custom_id="item_select"
        )
        item_select.callback = self._item_callback
        self.add_item(item_select)

    async def _item_callback(self, interaction: discord.Interaction):
        """Handle item selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        item_id = interaction.data["values"][0]
        result = await self.bot.combat_system.use_item_in_battle(self.battle_id, self.user_id, item_id)
        
        if result["success"]:
            # Get updated battle state
            battle = await self.bot.combat_system.get_battle_status(self.battle_id)
            if battle:
                # Get character for embed creation
                character = await self.bot.character_system.get_character(self.user_id)
                if character:
                    # Create updated battle embed
                    embed = self.bot.get_cog("CombatCog")._create_enhanced_battle_embed(battle, character)
                    # Update the main battle message
                    await interaction.message.edit(embed=embed)
                    
                    # Show item success message
                    success_embed = create_embed(
                        title="🧪 Item Used!",
                        description=f"✅ {result['message']}",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=success_embed, ephemeral=True)
                else:
                    await interaction.response.send_message("✅ Item used! Battle updated.", ephemeral=True)
            else:
                await interaction.response.send_message("✅ Item used! Battle updated.", ephemeral=True)
        else:
            embed = create_embed(
                title="❌ Item Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

class EquipmentView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id
    
    @discord.ui.button(label="⚔️ Change Weapon", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def change_weapon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get equippable weapons from inventory
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        weapons = [item for item in inventory if item.get("type") == "Weapon"]
        
        if not weapons:
            await interaction.response.send_message("You have no weapons to equip!", ephemeral=True)
            return
        
        options = []
        for weapon in weapons[:25]:
            effects = weapon.get("effects", {})
            atk_bonus = effects.get("atk", 0)
            options.append(discord.SelectOption(
                label=weapon["name"],
                description=f"ATK: +{atk_bonus} | {weapon.get('rarity', 'Common')}",
                value=weapon.get("id", weapon["name"]),
                emoji="⚔️"
            ))
        
        select = discord.ui.Select(
            placeholder="Select a weapon to equip...",
            options=options
        )
        
        async def weapon_callback(interaction: discord.Interaction):
            weapon_id = select.values[0]
            weapon_item = next((w for w in weapons if w.get("id", w["name"]) == weapon_id), None)
            
            if weapon_item:
                result = await self.bot.character_system.equip_item(self.user_id, weapon_item)
                if result["success"]:
                    await interaction.response.send_message(f"✅ Equipped {weapon_item['name']}!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {result['message']}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Weapon not found!", ephemeral=True)
        
        select.callback = weapon_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Choose a weapon to equip:", view=view, ephemeral=True)

    @discord.ui.button(label="🛡️ Change Armor", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def change_armor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get equippable armor from inventory
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        armor = [item for item in inventory if item.get("type") == "Armor"]
        
        if not armor:
            await interaction.response.send_message("You have no armor to equip!", ephemeral=True)
            return
        
        options = []
        for armor_item in armor[:25]:
            effects = armor_item.get("effects", {})
            def_bonus = effects.get("defense", 0)
            options.append(discord.SelectOption(
                label=armor_item["name"],
                description=f"DEF: +{def_bonus} | {armor_item.get('rarity', 'Common')}",
                value=armor_item.get("id", armor_item["name"]),
                emoji="🛡️"
            ))
        
        select = discord.ui.Select(
            placeholder="Select armor to equip...",
            options=options
        )
        
        async def armor_callback(interaction: discord.Interaction):
            armor_id = select.values[0]
            armor_item = next((a for a in armor if a.get("id", a["name"]) == armor_id), None)
            
            if armor_item:
                result = await self.bot.character_system.equip_item(self.user_id, armor_item)
                if result["success"]:
                    await interaction.response.send_message(f"✅ Equipped {armor_item['name']}!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {result['message']}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Armor not found!", ephemeral=True)
        
        select.callback = armor_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Choose armor to equip:", view=view, ephemeral=True)

    @discord.ui.button(label="💍 Change Accessory", style=discord.ButtonStyle.primary, emoji="💍")
    async def change_accessory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get equippable accessories from inventory
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        accessories = [item for item in inventory if item.get("type") == "Accessory"]
        
        if not accessories:
            await interaction.response.send_message("You have no accessories to equip!", ephemeral=True)
            return
        
        options = []
        for accessory in accessories[:25]:
            effects = accessory.get("effects", {})
            bonus_text = ""
            if effects.get("luck"):
                bonus_text += f"LUCK: +{effects['luck']} "
            if effects.get("sp%"):
                bonus_text += f"SP: +{effects['sp%']*100:.0f}% "
            
            options.append(discord.SelectOption(
                label=accessory["name"],
                description=f"{bonus_text}| {accessory.get('rarity', 'Common')}",
                value=accessory.get("id", accessory["name"]),
                emoji="💍"
            ))
        
        select = discord.ui.Select(
            placeholder="Select accessory to equip...",
            options=options
        )
        
        async def accessory_callback(interaction: discord.Interaction):
            accessory_id = select.values[0]
            accessory_item = next((a for a in accessories if a.get("id", a["name"]) == accessory_id), None)
            
            if accessory_item:
                result = await self.bot.character_system.equip_item(self.user_id, accessory_item)
                if result["success"]:
                    await interaction.response.send_message(f"✅ Equipped {accessory_item['name']}!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {result['message']}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Accessory not found!", ephemeral=True)
        
        select.callback = accessory_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Choose accessory to equip:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CombatCog(bot))
