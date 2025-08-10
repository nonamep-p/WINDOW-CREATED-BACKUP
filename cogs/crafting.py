import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List, Dict
from datetime import datetime
import asyncio

from utils.helpers import create_embed, format_number

logger = logging.getLogger(__name__)

class CraftingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="craft", description="Interactive crafting system with recipe browser and real-time crafting")
    async def craft(self, interaction: discord.Interaction):
        """Interactive crafting system main command"""
        user_id = interaction.user.id
        
        # Check if user has a character
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character create`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already crafting
        active_crafts = self.bot.crafting_system.get_player_crafting_progress(user_id)
        if active_crafts:
            embed = create_embed(
                title="🔨 Crafting In Progress",
                description="You're already crafting! Finish your current project first or use `/craftstatus` to check progress.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create main crafting interface
        embed = self._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, user_id)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="craftstatus", description="Check active crafting progress with interactive controls")
    async def craft_status(self, interaction: discord.Interaction):
        """Check the status of active crafting jobs with interactive controls"""
        user_id = interaction.user.id
        
        # Get active crafts
        active_crafts = self.bot.crafting_system.get_player_crafting_progress(user_id)
        
        if not active_crafts:
            embed = create_embed(
                title="🔨 Crafting Status",
                description="You have no active crafting jobs.\n\nUse `/craft` to start crafting!",
                color=discord.Color.greyple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create status embed with interactive controls
        embed = await self._create_crafting_status_embed(user_id, active_crafts)
        view = CraftingStatusView(self.bot, user_id, active_crafts)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="craftingskills", description="View and upgrade your crafting skills")
    async def crafting_skills(self, interaction: discord.Interaction):
        """View and upgrade crafting skills"""
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
        
        embed = self._create_crafting_skills_embed(character)
        view = CraftingSkillsView(self.bot, user_id)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="workshop", description="Manage your crafting stations and tools")
    async def workshop(self, interaction: discord.Interaction):
        """Manage crafting stations and tools"""
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
        
        embed = self._create_workshop_embed(character)
        view = WorkshopView(self.bot, user_id)
        
        await interaction.response.send_message(embed=embed, view=view)

    def _create_main_crafting_embed(self, character: Dict) -> discord.Embed:
        """Create the main crafting interface embed"""
        crafting_level = character.get("crafting_skills", {}).get("general", 1)
        
        # Get player's tools and stations
        inventory = character.get("inventory", [])
        tools = [item for item in inventory if item.get("type") == "Tool"]
        stations = character.get("crafting_stations", [])
        
        embed = create_embed(
            title=f"🔨 {character['username']}'s Crafting Workshop",
            description="Welcome to your crafting workshop! Choose what you'd like to do:",
            color=discord.Color.gold()
        )
        
        # Player info
        player_info = f"**Crafting Level:** {crafting_level}\n"
        player_info += f"**Available Tools:** {len(tools)}\n"
        player_info += f"**Crafting Stations:** {len(stations)}"
        
        embed.add_field(name="👤 Crafter Info", value=player_info, inline=True)
        
        # Quick stats
        skills = character.get("crafting_skills", {})
        skill_info = ""
        for skill, level in skills.items():
            skill_emoji = {"blacksmithing": "⚒️", "alchemy": "🧪", "enchanting": "✨", "cooking": "🍳", "tailoring": "🧵"}.get(skill, "🔧")
            skill_info += f"{skill_emoji} {skill.title()}: {level}\n"
        
        if not skill_info:
            skill_info = "No crafting skills learned yet!"
        
        embed.add_field(name="🎯 Skills", value=skill_info, inline=True)
        
        # Recent activity
        recent_crafts = character.get("recent_crafts", [])
        if recent_crafts:
            recent_info = "\n".join([f"• {craft['name']}" for craft in recent_crafts[-3:]])
        else:
            recent_info = "No recent crafting activity"
        
        embed.add_field(name="📜 Recent Crafts", value=recent_info, inline=True)
        
        embed.set_footer(text="Use the buttons below to navigate the crafting system")
        
        return embed

    async def _create_crafting_status_embed(self, user_id: int, active_crafts: List) -> discord.Embed:
        """Create crafting status embed with progress"""
        embed = create_embed(
            title="🔨 Active Crafting Projects",
            description="Your current crafting progress:",
            color=discord.Color.blue()
        )
        
        for i, craft in enumerate(active_crafts, 1):
            progress_result = await self.bot.crafting_system.check_crafting_progress(craft["craft_id"])
            
            if progress_result["success"]:
                recipe = craft["recipe"]
                if progress_result.get("progress") is not None:
                    # Still in progress
                    progress = progress_result["progress"]
                    progress_bar = self._create_progress_bar(progress)
                    
                    time_left = craft.get("time_remaining", 0)
                    time_text = f"{time_left//60}m {time_left%60}s" if time_left > 0 else "Almost done!"
                    
                    craft_info = f"{progress_bar} {progress:.1f}%\n"
                    craft_info += f"**Quantity:** {craft['quantity']}\n"
                    craft_info += f"**Time Left:** {time_text}\n"
                    craft_info += f"**Difficulty:** {recipe['difficulty'].title()}"
                    
                    embed.add_field(
                        name=f"🔨 {recipe['name']}",
                        value=craft_info,
                        inline=False
                    )
                else:
                    # Completed
                    craft_data = progress_result["craft"]
                    if craft_data["result"] == "success":
                        result_text = f"✅ **Completed Successfully!**\n"
                        result_text += f"**Items Created:** {craft_data['items_created']}\n"
                        result_text += f"**XP Gained:** {craft_data.get('xp_gained', 0)}"
                    else:
                        result_text = f"❌ **Crafting Failed!**\n"
                        result_text += f"**Reason:** {craft_data.get('failure_reason', 'Unknown')}"
                    
                    embed.add_field(
                        name=f"📦 {recipe['name']}",
                        value=result_text,
                        inline=False
                    )
        
        return embed

    def _create_crafting_skills_embed(self, character: Dict) -> discord.Embed:
        """Create crafting skills overview embed"""
        skills = character.get("crafting_skills", {})
        skill_xp = character.get("crafting_skill_xp", {})
        
        embed = create_embed(
            title=f"🎯 {character['username']}'s Crafting Skills",
            description="Your crafting skill levels and progression:",
            color=discord.Color.purple()
        )
        
        skill_data = {
            "blacksmithing": {"emoji": "⚒️", "desc": "Forge weapons and armor"},
            "alchemy": {"emoji": "🧪", "desc": "Brew potions and elixirs"},
            "enchanting": {"emoji": "✨", "desc": "Enchant items with magic"},
            "cooking": {"emoji": "🍳", "desc": "Prepare food and buffs"},
            "tailoring": {"emoji": "🧵", "desc": "Craft clothing and accessories"},
            "jewelcrafting": {"emoji": "💎", "desc": "Create rings and amulets"},
            "engineering": {"emoji": "🔧", "desc": "Build tools and gadgets"}
        }
        
        for skill, data in skill_data.items():
            level = skills.get(skill, 0)
            xp = skill_xp.get(skill, 0)
            xp_needed = self._calculate_xp_for_next_level(level)
            
            if level > 0:
                progress_bar = self._create_xp_progress_bar(xp, xp_needed)
                skill_text = f"**Level {level}**\n{progress_bar}\n{data['desc']}\n**XP:** {xp}/{xp_needed}"
            else:
                skill_text = f"**Not learned**\n{data['desc']}\nStart crafting to unlock!"
            
            embed.add_field(
                name=f"{data['emoji']} {skill.title()}",
                value=skill_text,
                inline=True
            )
        
        return embed

    def _create_workshop_embed(self, character: Dict) -> discord.Embed:
        """Create workshop management embed"""
        stations = character.get("crafting_stations", [])
        inventory = character.get("inventory", [])
        tools = [item for item in inventory if item.get("type") == "Tool"]
        
        embed = create_embed(
            title=f"🏭 {character['username']}'s Workshop",
            description="Manage your crafting stations and tools:",
            color=discord.Color.dark_gold()
        )
        
        # Crafting stations
        if stations:
            station_list = []
            for station in stations:
                condition = station.get("condition", 100)
                condition_emoji = "🟢" if condition > 75 else "🟡" if condition > 25 else "🔴"
                station_list.append(f"{condition_emoji} **{station['name']}** (Condition: {condition}%)")
            station_text = "\n".join(station_list)
        else:
            station_text = "No crafting stations owned.\nPurchase stations to unlock advanced recipes!"
        
        embed.add_field(name="🏭 Crafting Stations", value=station_text, inline=False)
        
        # Tools
        if tools:
            tool_list = []
            for tool in tools:
                durability = tool.get("durability", 100)
                durability_emoji = "🟢" if durability > 75 else "🟡" if durability > 25 else "🔴"
                tool_list.append(f"{durability_emoji} **{tool['name']}** (Durability: {durability}%)")
            tool_text = "\n".join(tool_list)
        else:
            tool_text = "No tools owned.\nBasic tools are required for most recipes!"
        
        embed.add_field(name="🔨 Tools", value=tool_text, inline=False)
        
        # Workshop stats
        total_value = sum([station.get("value", 0) for station in stations]) + sum([tool.get("value", 0) for tool in tools])
        workshop_stats = f"**Total Stations:** {len(stations)}\n"
        workshop_stats += f"**Total Tools:** {len(tools)}\n"
        workshop_stats += f"**Workshop Value:** {total_value:,} gold"
        
        embed.add_field(name="📊 Workshop Stats", value=workshop_stats, inline=True)
        
        return embed

    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"{'🟩' * filled}{'⬜' * empty}"

    def _create_xp_progress_bar(self, current_xp: int, needed_xp: int) -> str:
        """Create XP progress bar"""
        if needed_xp == 0:
            return "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"
        
        percentage = (current_xp / needed_xp) * 100
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"{'🟦' * filled}{'⬜' * empty}"

    def _calculate_xp_for_next_level(self, level: int) -> int:
        """Calculate XP needed for next level"""
        return (level + 1) * 100

class MainCraftingView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📋 Browse Recipes", style=discord.ButtonStyle.primary, emoji="📋")
    async def browse_recipes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get available recipes
        recipes = self.bot.crafting_system.get_crafting_recipes()
        
        embed = create_embed(
            title="📋 Recipe Browser",
            description="Choose a crafting skill to view recipes:",
            color=discord.Color.green()
        )
        
        view = RecipeBrowserView(self.bot, self.user_id, recipes)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎒 Check Materials", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def check_materials(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get player's inventory
        inventory = await self.bot.inventory_system.get_inventory(self.user_id)
        materials = [item for item in inventory if item.get("type") in ["Material", "material"]]
        
        embed = create_embed(
            title="🎒 Crafting Materials",
            description="Your available crafting materials:",
            color=discord.Color.blue()
        )
        
        if materials:
            material_list = []
            for material in materials:
                quantity = material.get("quantity", 1)
                material_list.append(f"• **{material['name']}** x{quantity}")
            
            embed.add_field(
                name="Available Materials",
                value="\n".join(material_list[:20]),  # Limit to 20 items
                inline=False
            )
            
            if len(materials) > 20:
                embed.set_footer(text=f"Showing 20 of {len(materials)} materials")
        else:
            embed.add_field(
                name="No Materials",
                value="You don't have any crafting materials yet.\nGather materials from hunting, mining, or the market!",
                inline=False
            )
        
        # Add back button
        view = MaterialsView(self.bot, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔨 Quick Craft", style=discord.ButtonStyle.success, emoji="🔨")
    async def quick_craft(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Show quick craft options (simple recipes player can make)
        character = await self.bot.character_system.get_character(self.user_id)
        available_recipes = self._get_craftable_recipes(character)
        
        if not available_recipes:
            embed = create_embed(
                title="🔨 Quick Craft",
                description="No recipes available for quick crafting.\nYou need materials and the required crafting skill levels.",
                color=discord.Color.red()
            )
            view = BackToMainView(self.bot, self.user_id)
            await interaction.response.edit_message(embed=embed, view=view)
            return
        
        embed = create_embed(
            title="🔨 Quick Craft",
            description="Select a recipe to craft immediately:",
            color=discord.Color.green()
        )
        
        view = QuickCraftView(self.bot, self.user_id, available_recipes)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🏭 Workshop", style=discord.ButtonStyle.secondary, emoji="🏭")
    async def workshop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_workshop_embed(character)
        view = WorkshopView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

    def _get_craftable_recipes(self, character: Dict) -> List[Dict]:
        """Get recipes that the player can currently craft"""
        # This would check materials, skills, tools, etc.
        # For now, return a simple list
        recipes = self.bot.crafting_system.get_crafting_recipes()
        craftable = []
        
        for recipe in recipes:
            # Check if player has required skill level
            skill_required = recipe.get("skill_required", "general")
            skill_level = character.get("crafting_skills", {}).get(skill_required, 0)
            
            if skill_level >= recipe.get("skill_level", 1):
                craftable.append(recipe)
        
        return craftable[:10]  # Limit to 10 for quick craft

class RecipeBrowserView(discord.ui.View):
    def __init__(self, bot, user_id: int, recipes: List[Dict]):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.recipes = recipes
        self.current_skill = None
        self.current_page = 0
        
        # Add skill selection dropdown
        self._add_skill_select()

    def _add_skill_select(self):
        """Add skill selection dropdown"""
        # Group recipes by skill
        skills = {}
        for recipe in self.recipes:
            skill = recipe.get("skill_required", "general")
            if skill not in skills:
                skills[skill] = []
            skills[skill].append(recipe)
        
        options = []
        for skill, skill_recipes in skills.items():
            skill_emoji = {"blacksmithing": "⚒️", "alchemy": "🧪", "enchanting": "✨", "cooking": "🍳", "tailoring": "🧵"}.get(skill, "🔧")
            options.append(discord.SelectOption(
                label=skill.title(),
                description=f"{len(skill_recipes)} recipes available",
                value=skill,
                emoji=skill_emoji
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choose a crafting skill...",
                options=options,
                custom_id="skill_select"
            )
            select.callback = self._skill_callback
            self.add_item(select)

    async def _skill_callback(self, interaction: discord.Interaction):
        """Handle skill selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        selected_skill = interaction.data["values"][0]
        self.current_skill = selected_skill
        self.current_page = 0
        
        # Filter recipes by skill
        skill_recipes = [r for r in self.recipes if r.get("skill_required") == selected_skill]
        
        embed = self._create_recipe_list_embed(skill_recipes)
        view = RecipeListView(self.bot, self.user_id, skill_recipes, selected_skill)
        
        await interaction.response.edit_message(embed=embed, view=view)

    def _create_recipe_list_embed(self, recipes: List[Dict]) -> discord.Embed:
        """Create recipe list embed"""
        embed = create_embed(
            title=f"📋 {self.current_skill.title()} Recipes",
            description=f"Available {self.current_skill} recipes:",
            color=discord.Color.green()
        )
        
        for i, recipe in enumerate(recipes[:10], 1):
            materials = ", ".join([f"{mat} x{amt}" for mat, amt in recipe["materials"].items()])
            recipe_info = f"**Difficulty:** {recipe['difficulty'].title()}\n"
            recipe_info += f"**Materials:** {materials}\n"
            recipe_info += f"**Time:** {recipe['crafting_time']}s\n"
            recipe_info += f"**Skill Level:** {recipe['skill_level']}"
            
            embed.add_field(
                name=f"{i}. {recipe['name']}",
                value=recipe_info,
                inline=True
            )
        
        if len(recipes) > 10:
            embed.set_footer(text=f"Showing 10 of {len(recipes)} recipes")
        
        return embed

    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class RecipeListView(discord.ui.View):
    def __init__(self, bot, user_id: int, recipes: List[Dict], skill: str):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.recipes = recipes
        self.skill = skill
        
        # Add recipe selection dropdown
        self._add_recipe_select()

    def _add_recipe_select(self):
        """Add recipe selection dropdown"""
        options = []
        for i, recipe in enumerate(self.recipes[:25], 1):
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🟠", "expert": "🔴", "master": "🟣"}.get(recipe["difficulty"], "⚪")
            options.append(discord.SelectOption(
                label=f"{i}. {recipe['name']}",
                description=f"{recipe['difficulty'].title()} • {recipe['crafting_time']}s",
                value=recipe.get("id", recipe["name"]),
                emoji=difficulty_emoji
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="Select a recipe to craft...",
                options=options,
                custom_id="recipe_select"
            )
            select.callback = self._recipe_callback
            self.add_item(select)

    async def _recipe_callback(self, interaction: discord.Interaction):
        """Handle recipe selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        recipe_id = interaction.data["values"][0]
        recipe = next((r for r in self.recipes if r.get("id", r["name"]) == recipe_id), None)
        
        if not recipe:
            await interaction.response.send_message("Recipe not found!", ephemeral=True)
            return
        
        # Show recipe details and crafting interface
        embed = self._create_recipe_details_embed(recipe)
        view = RecipeCraftView(self.bot, self.user_id, recipe)
        
        await interaction.response.edit_message(embed=embed, view=view)

    def _create_recipe_details_embed(self, recipe: Dict) -> discord.Embed:
        """Create detailed recipe embed"""
        embed = create_embed(
            title=f"📜 {recipe['name']} Recipe",
            description=recipe.get("description", "A crafting recipe"),
            color=discord.Color.gold()
        )
        
        # Materials
        materials = recipe["materials"]
        material_list = []
        for material, amount in materials.items():
            material_list.append(f"• **{material.replace('_', ' ').title()}** x{amount}")
        
        embed.add_field(
            name="📦 Required Materials",
            value="\n".join(material_list),
            inline=True
        )
        
        # Requirements
        requirements = f"**Skill:** {recipe['skill_required'].title()} (Level {recipe['skill_level']})\n"
        requirements += f"**Difficulty:** {recipe['difficulty'].title()}\n"
        requirements += f"**Crafting Time:** {recipe['crafting_time']} seconds\n"
        requirements += f"**XP Reward:** {recipe['xp_reward']}"
        
        embed.add_field(
            name="⚡ Requirements",
            value=requirements,
            inline=True
        )
        
        # Tools required
        if recipe.get("tools_required"):
            tools = "\n".join([f"• {tool.replace('_', ' ').title()}" for tool in recipe["tools_required"]])
            embed.add_field(
                name="🔨 Tools Required",
                value=tools,
                inline=False
            )
        
        # Success chance
        success_chance = (1.0 - recipe.get("failure_chance", 0)) * 100
        embed.add_field(
            name="📊 Success Rate",
            value=f"{success_chance:.1f}%",
            inline=True
        )
        
        return embed

    @discord.ui.button(label="🔙 Back to Recipes", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_recipes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="📋 Recipe Browser",
            description="Choose a crafting skill to view recipes:",
            color=discord.Color.green()
        )
        
        view = RecipeBrowserView(self.bot, self.user_id, self.bot.crafting_system.get_crafting_recipes())
        await interaction.response.edit_message(embed=embed, view=view)

class RecipeCraftView(discord.ui.View):
    def __init__(self, bot, user_id: int, recipe: Dict):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.recipe = recipe

    @discord.ui.button(label="🔨 Craft x1", style=discord.ButtonStyle.success, emoji="🔨")
    async def craft_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_crafting(interaction, 1)

    @discord.ui.button(label="🔨 Craft x5", style=discord.ButtonStyle.success, emoji="🔨")
    async def craft_five(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_crafting(interaction, 5)

    @discord.ui.button(label="🔨 Craft x10", style=discord.ButtonStyle.success, emoji="🔨")
    async def craft_ten(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_crafting(interaction, 10)

    @discord.ui.button(label="📝 Custom Amount", style=discord.ButtonStyle.primary, emoji="📝")
    async def craft_custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        modal = CraftAmountModal(self.bot, self.user_id, self.recipe)
        await interaction.response.send_modal(modal)

    async def _start_crafting(self, interaction: discord.Interaction, quantity: int):
        """Start crafting with specified quantity"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        recipe_id = self.recipe.get("id", self.recipe["name"])
        result = await self.bot.crafting_system.start_crafting(self.user_id, recipe_id, quantity)
        
        if result["success"]:
            craft = result["craft"]
            total_time = self.recipe["crafting_time"] * quantity
            
            embed = create_embed(
                title="🔨 Crafting Started!",
                description=f"**{self.recipe['name']}** crafting has begun!",
                color=discord.Color.green()
            )
            
            craft_info = f"**Quantity:** {quantity}\n"
            craft_info += f"**Total Time:** {total_time} seconds\n"
            craft_info += f"**Difficulty:** {self.recipe['difficulty'].title()}\n"
            craft_info += f"**Success Rate:** {(1.0 - self.recipe.get('failure_chance', 0)) * 100:.1f}%"
            
            embed.add_field(name="📊 Crafting Info", value=craft_info, inline=False)
            embed.set_footer(text="Use /craftstatus to check progress!")
            
            # Start real-time progress tracking
            view = CraftingProgressView(self.bot, self.user_id, craft["craft_id"], total_time)
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Start progress tracking task
            asyncio.create_task(self._track_crafting_progress(interaction, craft["craft_id"], total_time))
        else:
            embed = create_embed(
                title="❌ Crafting Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    async def _track_crafting_progress(self, interaction: discord.Interaction, craft_id: str, total_time: int):
        """Track crafting progress in real-time"""
        start_time = datetime.utcnow()
        
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Check if crafting is still active
            progress_result = await self.bot.crafting_system.check_crafting_progress(craft_id)
            if not progress_result["success"]:
                break
            
            if progress_result.get("progress") is None:
                # Crafting completed
                craft_data = progress_result["craft"]
                if craft_data["result"] == "success":
                    embed = create_embed(
                        title="✅ Crafting Completed!",
                        description=f"**{self.recipe['name']}** has been crafted successfully!",
                        color=discord.Color.green()
                    )
                    
                    result_info = f"**Items Created:** {craft_data['items_created']}\n"
                    result_info += f"**XP Gained:** {craft_data.get('xp_gained', 0)}\n"
                    result_info += f"**Quality:** {craft_data.get('quality', 'Standard')}"
                    
                    embed.add_field(name="🎁 Results", value=result_info, inline=False)
                else:
                    embed = create_embed(
                        title="❌ Crafting Failed!",
                        description=f"**{self.recipe['name']}** crafting failed.",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="💔 Failure Reason", 
                        value=craft_data.get('failure_reason', 'Unknown error occurred'),
                        inline=False
                    )
                
                try:
                    await interaction.edit_original_response(embed=embed, view=None)
                except:
                    pass  # Interaction might have expired
                break
            
            # Update progress
            progress = progress_result["progress"]
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            time_remaining = max(0, total_time - elapsed_time)
            
            embed = create_embed(
                title="🔨 Crafting In Progress",
                description=f"**{self.recipe['name']}** is being crafted...",
                color=discord.Color.blue()
            )
            
            progress_bar = self._create_progress_bar(progress)
            progress_info = f"{progress_bar} {progress:.1f}%\n"
            progress_info += f"**Time Remaining:** {int(time_remaining//60)}m {int(time_remaining%60)}s"
            
            embed.add_field(name="⏳ Progress", value=progress_info, inline=False)
            
            try:
                await interaction.edit_original_response(embed=embed)
            except:
                pass  # Interaction might have expired

    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return f"{'🟩' * filled}{'⬜' * empty}"

    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Go back to recipe list
        skill = self.recipe.get("skill_required", "general")
        recipes = [r for r in self.bot.crafting_system.get_crafting_recipes() if r.get("skill_required") == skill]
        
        embed = create_embed(
            title=f"📋 {skill.title()} Recipes",
            description=f"Available {skill} recipes:",
            color=discord.Color.green()
        )
        
        view = RecipeListView(self.bot, self.user_id, recipes, skill)
        await interaction.response.edit_message(embed=embed, view=view)

class CraftAmountModal(discord.ui.Modal, title="Craft Custom Amount"):
    def __init__(self, bot, user_id: int, recipe: Dict):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.recipe = recipe

    amount = discord.ui.TextInput(
        label="Quantity to Craft",
        placeholder="Enter the number of items to craft (1-100)",
        min_length=1,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantity = int(self.amount.value)
            if quantity < 1 or quantity > 100:
                await interaction.response.send_message("Quantity must be between 1 and 100!", ephemeral=True)
                return
            
            # Start crafting
            recipe_id = self.recipe.get("id", self.recipe["name"])
            result = await self.bot.crafting_system.start_crafting(self.user_id, recipe_id, quantity)
            
            if result["success"]:
                total_time = self.recipe["crafting_time"] * quantity
                
                embed = create_embed(
                    title="🔨 Crafting Started!",
                    description=f"**{self.recipe['name']}** x{quantity} crafting has begun!",
                    color=discord.Color.green()
                )
                
                craft_info = f"**Quantity:** {quantity}\n"
                craft_info += f"**Total Time:** {total_time} seconds\n"
                craft_info += f"**Estimated Cost:** {quantity * 10} materials"
                
                embed.add_field(name="📊 Crafting Info", value=craft_info, inline=False)
                embed.set_footer(text="Use /craftstatus to check progress!")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = create_embed(
                    title="❌ Crafting Failed",
                    description=result["message"],
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True)

class CraftingProgressView(discord.ui.View):
    def __init__(self, bot, user_id: int, craft_id: str, total_time: int):
        super().__init__(timeout=total_time + 60)
        self.bot = bot
        self.user_id = user_id
        self.craft_id = craft_id

    @discord.ui.button(label="❌ Cancel Crafting", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_crafting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Cancel the crafting job
        result = await self.bot.crafting_system.cancel_crafting(self.user_id, self.craft_id)
        
        if result["success"]:
            embed = create_embed(
                title="❌ Crafting Cancelled",
                description="Your crafting job has been cancelled.\nMaterials have been returned to your inventory.",
                color=discord.Color.orange()
            )
        else:
            embed = create_embed(
                title="❌ Cancel Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

class CraftingStatusView(discord.ui.View):
    def __init__(self, bot, user_id: int, active_crafts: List):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.active_crafts = active_crafts

    @discord.ui.button(label="🔄 Refresh Status", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get updated crafting status
        active_crafts = self.bot.crafting_system.get_player_crafting_progress(self.user_id)
        
        if not active_crafts:
            embed = create_embed(
                title="🔨 Crafting Status",
                description="You have no active crafting jobs.",
                color=discord.Color.greyple()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        cog = self.bot.get_cog("CraftingCog")
        embed = await cog._create_crafting_status_embed(self.user_id, active_crafts)
        view = CraftingStatusView(self.bot, self.user_id, active_crafts)
        
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="❌ Cancel All", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Confirm cancellation
        embed = create_embed(
            title="⚠️ Confirm Cancellation",
            description="Are you sure you want to cancel ALL active crafting jobs?\nThis action cannot be undone.",
            color=discord.Color.orange()
        )
        
        view = ConfirmCancelView(self.bot, self.user_id, self.active_crafts)
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmCancelView(discord.ui.View):
    def __init__(self, bot, user_id: int, active_crafts: List):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id
        self.active_crafts = active_crafts

    @discord.ui.button(label="✅ Yes, Cancel All", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        cancelled_count = 0
        for craft in self.active_crafts:
            result = await self.bot.crafting_system.cancel_crafting(self.user_id, craft["craft_id"])
            if result["success"]:
                cancelled_count += 1
        
        embed = create_embed(
            title="✅ Crafting Jobs Cancelled",
            description=f"Successfully cancelled {cancelled_count} crafting jobs.\nMaterials have been returned to your inventory.",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ No, Keep Crafting", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Go back to status view
        cog = self.bot.get_cog("CraftingCog")
        embed = await cog._create_crafting_status_embed(self.user_id, self.active_crafts)
        view = CraftingStatusView(self.bot, self.user_id, self.active_crafts)
        
        await interaction.response.edit_message(embed=embed, view=view)

class CraftingSkillsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📚 Learn New Skill", style=discord.ButtonStyle.success, emoji="📚")
    async def learn_skill(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        current_skills = character.get("crafting_skills", {})
        
        # Available skills to learn
        all_skills = ["blacksmithing", "alchemy", "enchanting", "cooking", "tailoring", "jewelcrafting", "engineering"]
        available_skills = [skill for skill in all_skills if skill not in current_skills]
        
        if not available_skills:
            embed = create_embed(
                title="📚 Learn New Skill",
                description="You have already learned all available crafting skills!",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = create_embed(
            title="📚 Learn New Crafting Skill",
            description="Choose a new crafting skill to learn:",
            color=discord.Color.blue()
        )
        
        view = LearnSkillView(self.bot, self.user_id, available_skills)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔙 Back to Crafting", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class LearnSkillView(discord.ui.View):
    def __init__(self, bot, user_id: int, available_skills: List[str]):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.available_skills = available_skills
        
        # Add skill selection dropdown
        self._add_skill_select()

    def _add_skill_select(self):
        """Add skill selection dropdown"""
        skill_data = {
            "blacksmithing": {"emoji": "⚒️", "desc": "Forge weapons and armor", "cost": 100},
            "alchemy": {"emoji": "🧪", "desc": "Brew potions and elixirs", "cost": 150},
            "enchanting": {"emoji": "✨", "desc": "Enchant items with magic", "cost": 200},
            "cooking": {"emoji": "🍳", "desc": "Prepare food and buffs", "cost": 75},
            "tailoring": {"emoji": "🧵", "desc": "Craft clothing and accessories", "cost": 100},
            "jewelcrafting": {"emoji": "💎", "desc": "Create rings and amulets", "cost": 250},
            "engineering": {"emoji": "🔧", "desc": "Build tools and gadgets", "cost": 300}
        }
        
        options = []
        for skill in self.available_skills:
            data = skill_data.get(skill, {"emoji": "🔧", "desc": "Unknown skill", "cost": 100})
            options.append(discord.SelectOption(
                label=skill.title(),
                description=f"{data['desc']} • Cost: {data['cost']} gold",
                value=skill,
                emoji=data['emoji']
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choose a skill to learn...",
                options=options,
                custom_id="skill_learn_select"
            )
            select.callback = self._learn_skill_callback
            self.add_item(select)

    async def _learn_skill_callback(self, interaction: discord.Interaction):
        """Handle skill learning"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        skill = interaction.data["values"][0]
        
        # Check if player has enough gold
        character = await self.bot.character_system.get_character(self.user_id)
        gold = character.get("gold", 0)
        
        skill_costs = {
            "blacksmithing": 100, "alchemy": 150, "enchanting": 200,
            "cooking": 75, "tailoring": 100, "jewelcrafting": 250, "engineering": 300
        }
        cost = skill_costs.get(skill, 100)
        
        if gold < cost:
            embed = create_embed(
                title="❌ Insufficient Gold",
                description=f"You need {cost} gold to learn {skill.title()}.\nYou currently have {gold} gold.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Learn the skill
        crafting_skills = character.get("crafting_skills", {})
        crafting_skills[skill] = 1
        character["crafting_skills"] = crafting_skills
        character["gold"] -= cost
        
        await self.bot.db.save_player(self.user_id, character)
        
        embed = create_embed(
            title="📚 Skill Learned!",
            description=f"You have successfully learned **{skill.title()}**!\n\nYou can now craft {skill} recipes and gain experience in this skill.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Cost",
            value=f"{cost} gold spent",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Current Level",
            value="Level 1",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

class WorkshopView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🏪 Buy Station", style=discord.ButtonStyle.success, emoji="🏪")
    async def buy_station(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        embed = create_embed(
            title="🏪 Crafting Station Shop",
            description="Purchase crafting stations to unlock advanced recipes:",
            color=discord.Color.green()
        )
        
        # Available stations
        stations = [
            {"name": "Basic Forge", "cost": 500, "desc": "Enables basic blacksmithing"},
            {"name": "Advanced Forge", "cost": 2000, "desc": "Enables advanced blacksmithing"},
            {"name": "Alchemy Lab", "cost": 1000, "desc": "Enables potion brewing"},
            {"name": "Enchanting Table", "cost": 3000, "desc": "Enables item enchanting"},
            {"name": "Cooking Station", "cost": 300, "desc": "Enables advanced cooking"},
            {"name": "Tailoring Bench", "cost": 800, "desc": "Enables clothing crafting"}
        ]
        
        station_list = []
        for station in stations:
            station_list.append(f"• **{station['name']}** - {station['cost']} gold\n  {station['desc']}")
        
        embed.add_field(
            name="Available Stations",
            value="\n".join(station_list),
            inline=False
        )
        
        view = StationShopView(self.bot, self.user_id, stations)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔧 Repair Equipment", style=discord.ButtonStyle.primary, emoji="🔧")
    async def repair_equipment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get damaged equipment
        character = await self.bot.character_system.get_character(self.user_id)
        stations = character.get("crafting_stations", [])
        inventory = character.get("inventory", [])
        tools = [item for item in inventory if item.get("type") == "Tool"]
        
        damaged_items = []
        for station in stations:
            if station.get("condition", 100) < 100:
                damaged_items.append(("station", station))
        
        for tool in tools:
            if tool.get("durability", 100) < 100:
                damaged_items.append(("tool", tool))
        
        if not damaged_items:
            embed = create_embed(
                title="🔧 Equipment Repair",
                description="All your crafting equipment is in perfect condition!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Calculate repair costs
        total_cost = 0
        repair_list = []
        
        for item_type, item in damaged_items:
            condition = item.get("condition" if item_type == "station" else "durability", 100)
            repair_cost = int((100 - condition) * 2)  # 2 gold per % to repair
            total_cost += repair_cost
            
            repair_list.append(f"• **{item['name']}** - {condition}% → 100% ({repair_cost} gold)")
        
        embed = create_embed(
            title="🔧 Equipment Repair",
            description="Repair your damaged crafting equipment:",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Damaged Equipment",
            value="\n".join(repair_list),
            inline=False
        )
        
        embed.add_field(
            name="💰 Total Cost",
            value=f"{total_cost} gold",
            inline=True
        )
        
        view = RepairEquipmentView(self.bot, self.user_id, damaged_items, total_cost)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔙 Back to Crafting", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class StationShopView(discord.ui.View):
    def __init__(self, bot, user_id: int, stations: List[Dict]):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.stations = stations
        
        # Add station selection dropdown
        self._add_station_select()

    def _add_station_select(self):
        """Add station selection dropdown"""
        options = []
        for station in self.stations:
            options.append(discord.SelectOption(
                label=station["name"],
                description=f"{station['desc']} • {station['cost']} gold",
                value=station["name"],
                emoji="🏭"
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choose a station to purchase...",
                options=options,
                custom_id="station_buy_select"
            )
            select.callback = self._buy_station_callback
            self.add_item(select)

    async def _buy_station_callback(self, interaction: discord.Interaction):
        """Handle station purchase"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        station_name = interaction.data["values"][0]
        station = next((s for s in self.stations if s["name"] == station_name), None)
        
        if not station:
            await interaction.response.send_message("Station not found!", ephemeral=True)
            return
        
        # Check if player has enough gold
        character = await self.bot.character_system.get_character(self.user_id)
        gold = character.get("gold", 0)
        cost = station["cost"]
        
        if gold < cost:
            embed = create_embed(
                title="❌ Insufficient Gold",
                description=f"You need {cost} gold to purchase {station_name}.\nYou currently have {gold} gold.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if player already owns this station
        existing_stations = character.get("crafting_stations", [])
        if any(s["name"] == station_name for s in existing_stations):
            embed = create_embed(
                title="❌ Already Owned",
                description=f"You already own a {station_name}!",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Purchase the station
        new_station = {
            "name": station_name,
            "condition": 100,
            "value": cost,
            "purchased_at": datetime.utcnow().isoformat()
        }
        
        existing_stations.append(new_station)
        character["crafting_stations"] = existing_stations
        character["gold"] -= cost
        
        await self.bot.db.save_player(self.user_id, character)
        
        embed = create_embed(
            title="🏭 Station Purchased!",
            description=f"You have successfully purchased a **{station_name}**!\n\n{station['desc']}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Cost",
            value=f"{cost} gold",
            inline=True
        )
        
        embed.add_field(
            name="🏭 Condition",
            value="100% (New)",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🔙 Back to Workshop", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_workshop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_workshop_embed(character)
        view = WorkshopView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class RepairEquipmentView(discord.ui.View):
    def __init__(self, bot, user_id: int, damaged_items: List, total_cost: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.damaged_items = damaged_items
        self.total_cost = total_cost

    @discord.ui.button(label="✅ Repair All", style=discord.ButtonStyle.success, emoji="✅")
    async def repair_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Check if player has enough gold
        character = await self.bot.character_system.get_character(self.user_id)
        gold = character.get("gold", 0)
        
        if gold < self.total_cost:
            embed = create_embed(
                title="❌ Insufficient Gold",
                description=f"You need {self.total_cost} gold to repair all equipment.\nYou currently have {gold} gold.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Repair all items
        repaired_count = 0
        
        for item_type, item in self.damaged_items:
            if item_type == "station":
                item["condition"] = 100
            else:  # tool
                item["durability"] = 100
            repaired_count += 1
        
        character["gold"] -= self.total_cost
        await self.bot.db.save_player(self.user_id, character)
        
        embed = create_embed(
            title="✅ Equipment Repaired!",
            description=f"Successfully repaired {repaired_count} pieces of equipment!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Total Cost",
            value=f"{self.total_cost} gold",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Items Repaired",
            value=f"{repaired_count} items",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_repair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_workshop_embed(character)
        view = WorkshopView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class QuickCraftView(discord.ui.View):
    def __init__(self, bot, user_id: int, recipes: List[Dict]):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id
        self.recipes = recipes
        
        # Add recipe selection dropdown
        self._add_recipe_select()

    def _add_recipe_select(self):
        """Add quick craft recipe selection dropdown"""
        options = []
        for recipe in self.recipes[:25]:  # Discord limit
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🟠", "expert": "🔴", "master": "🟣"}.get(recipe["difficulty"], "⚪")
            options.append(discord.SelectOption(
                label=recipe["name"],
                description=f"{recipe['difficulty'].title()} • {recipe['crafting_time']}s",
                value=recipe.get("id", recipe["name"]),
                emoji=difficulty_emoji
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choose a recipe to craft quickly...",
                options=options,
                custom_id="quick_craft_select"
            )
            select.callback = self._quick_craft_callback
            self.add_item(select)

    async def _quick_craft_callback(self, interaction: discord.Interaction):
        """Handle quick craft selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        recipe_id = interaction.data["values"][0]
        recipe = next((r for r in self.recipes if r.get("id", r["name"]) == recipe_id), None)
        
        if not recipe:
            await interaction.response.send_message("Recipe not found!", ephemeral=True)
            return
        
        # Start crafting with quantity 1
        result = await self.bot.crafting_system.start_crafting(self.user_id, recipe_id, 1)
        
        if result["success"]:
            embed = create_embed(
                title="🔨 Quick Craft Started!",
                description=f"**{recipe['name']}** is being crafted!",
                color=discord.Color.green()
            )
            
            craft_info = f"**Time:** {recipe['crafting_time']} seconds\n"
            craft_info += f"**Success Rate:** {(1.0 - recipe.get('failure_chance', 0)) * 100:.1f}%"
            
            embed.add_field(name="📊 Info", value=craft_info, inline=False)
            embed.set_footer(text="Use /craftstatus to check progress!")
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = create_embed(
                title="❌ Quick Craft Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class MaterialsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

class BackToMainView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        character = await self.bot.character_system.get_character(self.user_id)
        cog = self.bot.get_cog("CraftingCog")
        embed = cog._create_main_crafting_embed(character)
        view = MainCraftingView(self.bot, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CraftingCog(bot))

