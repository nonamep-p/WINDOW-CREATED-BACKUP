import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
import random

from utils.helpers import create_embed, format_number

logger = logging.getLogger(__name__)

class PetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pets", description="Manage your pets and companions")
    async def pets(self, interaction: discord.Interaction):
        """Manage pets and companions"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get pets
        pets = await self.bot.pet_system.get_pets(user_id)
        
        embed = self._create_pets_embed(character, pets)
        view = PetsView(self.bot, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="adopt", description="Adopt a new pet")
    async def adopt(self, interaction: discord.Interaction):
        """Adopt a new pet"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get available pets for adoption
        available_pets = await self.bot.pet_system.get_available_pets()
        
        embed = self._create_adoption_embed(character, available_pets)
        view = AdoptionView(self.bot, user_id, available_pets)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="train", description="Train your active pet")
    async def train(self, interaction: discord.Interaction):
        """Train your active pet"""
        user_id = interaction.user.id
        
        character = await self.bot.character_system.get_character(user_id)
        if not character:
            embed = create_embed(
                title="❌ No Character Found",
                description="You need to create a character first! Use `/character`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get active pet
        active_pet = await self.bot.pet_system.get_active_pet(user_id)
        if not active_pet:
            embed = create_embed(
                title="❌ No Active Pet",
                description="You need to set an active pet first! Use `/pets`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get training options
        training_options = await self.bot.pet_system.get_training_options(active_pet)
        
        embed = self._create_training_embed(character, active_pet, training_options)
        view = TrainingView(self.bot, user_id, active_pet, training_options)
        await interaction.response.send_message(embed=embed, view=view)

    def _create_pets_embed(self, character, pets):
        """Create pets embed"""
        embed = create_embed(
            title=f"🐾 {character['username']}'s Pets",
            description="Manage your loyal companions!",
            color=discord.Color.green()
        )
        
        if not pets:
            embed.add_field(name="🐾 No Pets", value="Adopt a pet to get started!", inline=False)
            return embed
        
        # Group pets by status
        active_pets = [p for p in pets if p.get("active", False)]
        inactive_pets = [p for p in pets if not p.get("active", False)]
        
        # Active pets
        if active_pets:
            active_text = ""
            for pet in active_pets:
                level = pet.get("level", 1)
                exp = pet.get("exp", 0)
                exp_needed = pet.get("exp_needed", 100)
                exp_percent = (exp / exp_needed * 100) if exp_needed > 0 else 0
                
                active_text += f"🐾 **{pet['name']}** (Level {level})\n"
                active_text += f"   Type: {pet.get('type', 'Unknown')}\n"
                active_text += f"   EXP: {exp}/{exp_needed} ({exp_percent:.1f}%)\n"
                active_text += f"   Bonus: +{pet.get('bonus', 0)}% to stats\n\n"
            
            embed.add_field(name="🐾 Active Pets", value=active_text, inline=False)
        
        # Inactive pets
        if inactive_pets:
            inactive_text = ""
            for pet in inactive_pets[:5]:  # Show first 5
                level = pet.get("level", 1)
                inactive_text += f"🐾 **{pet['name']}** (Level {level})\n"
                inactive_text += f"   Type: {pet.get('type', 'Unknown')}\n\n"
            
            if len(inactive_pets) > 5:
                inactive_text += f"... and {len(inactive_pets) - 5} more pets"
            
            embed.add_field(name="🐾 Inactive Pets", value=inactive_text, inline=False)
        
        # Add stats
        total_pets = len(pets)
        total_levels = sum(p.get("level", 1) for p in pets)
        total_bonus = sum(p.get("bonus", 0) for p in active_pets)
        
        stats_text = f"📊 **Total Pets:** {total_pets}\n"
        stats_text += f"📈 **Total Levels:** {total_levels}\n"
        stats_text += f"🎯 **Active Bonus:** +{total_bonus}% to stats"
        
        embed.add_field(name="📈 Stats", value=stats_text, inline=False)
        
        return embed

    def _create_adoption_embed(self, character, available_pets):
        """Create adoption embed"""
        embed = create_embed(
            title=f"🏠 Pet Adoption Center",
            description=f"Welcome {character['username']}! Choose your new companion.",
            color=discord.Color.blue()
        )
        
        if not available_pets:
            embed.add_field(name="🏠 No Pets Available", value="Check back later for new pets!", inline=False)
            return embed
        
        for pet in available_pets[:5]:  # Show first 5
            cost = pet.get("cost", 0)
            rarity = pet.get("rarity", "Common")
            rarity_emoji = {
                "Common": "⚪",
                "Uncommon": "🟢", 
                "Rare": "🔵",
                "Epic": "🟣",
                "Legendary": "🟡"
            }.get(rarity, "⚪")
            
            pet_text = f"{rarity_emoji} **{pet['name']}** ({rarity})\n"
            pet_text += f"📝 {pet.get('description', 'No description')}\n"
            pet_text += f"💰 Cost: {format_number(cost)} gold\n"
            pet_text += f"🎯 Bonus: +{pet.get('bonus', 0)}% to stats\n\n"
            
            embed.add_field(name=f"🏠 Available Pet", value=pet_text, inline=False)
        
        return embed

    def _create_training_embed(self, character, active_pet, training_options):
        """Create training embed"""
        embed = create_embed(
            title=f"🎓 Training {active_pet['name']}",
            description=f"Train your pet to increase its power and bonuses!",
            color=discord.Color.purple()
        )
        
        # Pet info
        level = active_pet.get("level", 1)
        exp = active_pet.get("exp", 0)
        exp_needed = active_pet.get("exp_needed", 100)
        exp_percent = (exp / exp_needed * 100) if exp_needed > 0 else 0
        
        pet_info = f"🐾 **{active_pet['name']}** (Level {level})\n"
        pet_info += f"📊 EXP: {exp}/{exp_needed} ({exp_percent:.1f}%)\n"
        pet_info += f"🎯 Current Bonus: +{active_pet.get('bonus', 0)}% to stats\n"
        pet_info += f"💰 Training Cost: {format_number(active_pet.get('training_cost', 100))} gold"
        
        embed.add_field(name="🐾 Pet Info", value=pet_info, inline=False)
        
        # Training options
        if training_options:
            training_text = ""
            for option in training_options:
                cost = option.get("cost", 0)
                exp_gain = option.get("exp_gain", 0)
                success_rate = option.get("success_rate", 100)
                
                training_text += f"🎓 **{option['name']}**\n"
                training_text += f"   📝 {option.get('description', 'No description')}\n"
                training_text += f"   💰 Cost: {format_number(cost)} gold\n"
                training_text += f"   ⭐ EXP Gain: {exp_gain}\n"
                training_text += f"   🎯 Success Rate: {success_rate}%\n\n"
            
            embed.add_field(name="🎓 Training Options", value=training_text, inline=False)
        else:
            embed.add_field(name="🎓 No Training Available", value="Your pet is at max level!", inline=False)
        
        return embed

class PetsView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🐾 Set Active", style=discord.ButtonStyle.primary, emoji="🐾")
    async def set_active(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get user's pets
        pets = await self.bot.pet_system.get_pets(self.user_id)
        if not pets:
            await interaction.response.send_message("❌ You don't have any pets!", ephemeral=True)
            return
        
        # Create pet selection dropdown
        options = []
        for pet in pets[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=f"{pet['name']} (Level {pet.get('level', 1)})",
                description=f"Type: {pet.get('type', 'Unknown')}",
                value=pet["id"]
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="🐾 Select pet to set active",
                options=options,
                custom_id="pet_select"
            )
            select.callback = self._pet_callback
            self.add_item(select)
            
            await interaction.response.send_message("🐾 Select a pet to set as active:", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No pets available!", ephemeral=True)

    @discord.ui.button(label="🎓 Train", style=discord.ButtonStyle.success, emoji="🎓")
    async def train_pet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get active pet
        active_pet = await self.bot.pet_system.get_active_pet(self.user_id)
        if not active_pet:
            await interaction.response.send_message("❌ You don't have an active pet!", ephemeral=True)
            return
        
        # Get training options
        training_options = await self.bot.pet_system.get_training_options(active_pet)
        if not training_options:
            await interaction.response.send_message("❌ Your pet is at max level!", ephemeral=True)
            return
        
        # Create training selection dropdown
        options = []
        for option in training_options[:25]:  # Discord limit
            cost = option.get("cost", 0)
            exp_gain = option.get("exp_gain", 0)
            options.append(discord.SelectOption(
                label=f"{option['name']} - {format_number(cost)} gold",
                description=f"EXP Gain: {exp_gain}",
                value=option["id"]
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="🎓 Select training option",
                options=options,
                custom_id="training_select"
            )
            select.callback = self._training_callback
            self.add_item(select)
            
            await interaction.response.send_message("🎓 Select a training option:", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No training options available!", ephemeral=True)

    @discord.ui.button(label="🏠 Adopt", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def adopt_pet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        # Get available pets
        available_pets = await self.bot.pet_system.get_available_pets()
        if not available_pets:
            await interaction.response.send_message("❌ No pets available for adoption!", ephemeral=True)
            return
        
        # Create adoption selection dropdown
        options = []
        for pet in available_pets[:25]:  # Discord limit
            cost = pet.get("cost", 0)
            rarity = pet.get("rarity", "Common")
            options.append(discord.SelectOption(
                label=f"{pet['name']} ({rarity}) - {format_number(cost)} gold",
                description=pet.get("description", "No description"),
                value=pet["id"]
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="🏠 Select pet to adopt",
                options=options,
                custom_id="adoption_select"
            )
            select.callback = self._adoption_callback
            self.add_item(select)
            
            await interaction.response.send_message("🏠 Select a pet to adopt:", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No pets available for adoption!", ephemeral=True)

    async def _pet_callback(self, interaction: discord.Interaction):
        """Handle pet selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        pet_id = interaction.data["values"][0]
        result = await self.bot.pet_system.set_active_pet(self.user_id, pet_id)
        
        if result["success"]:
            embed = create_embed(
                title="✅ Pet Set Active!",
                description=f"**{result['pet_name']}** is now your active companion!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Failed to Set Active",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _training_callback(self, interaction: discord.Interaction):
        """Handle training selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        training_id = interaction.data["values"][0]
        result = await self.bot.pet_system.train_pet(self.user_id, training_id)
        
        if result["success"]:
            embed = create_embed(
                title="🎓 Training Successful!",
                description=f"**{result['pet_name']}** gained {result['exp_gained']} EXP!",
                color=discord.Color.green()
            )
            
            if result.get("leveled_up"):
                embed.add_field(name="🎉 Level Up!", value=f"**{result['pet_name']}** reached level {result['new_level']}!", inline=False)
        else:
            embed = create_embed(
                title="❌ Training Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _adoption_callback(self, interaction: discord.Interaction):
        """Handle adoption selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        pet_id = interaction.data["values"][0]
        result = await self.bot.pet_system.adopt_pet(self.user_id, pet_id)
        
        if result["success"]:
            embed = create_embed(
                title="🏠 Adoption Successful!",
                description=f"Welcome **{result['pet_name']}** to your family!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Adoption Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdoptionView(discord.ui.View):
    def __init__(self, bot, user_id: int, available_pets: list):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id
        self.available_pets = available_pets
        self._add_pet_select()

    def _add_pet_select(self):
        """Add pet selection dropdown"""
        options = []
        for pet in self.available_pets[:25]:  # Discord limit
            cost = pet.get("cost", 0)
            rarity = pet.get("rarity", "Common")
            options.append(discord.SelectOption(
                label=f"{pet['name']} ({rarity}) - {format_number(cost)} gold",
                description=pet.get("description", "No description"),
                value=pet["id"]
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="🏠 Select pet to adopt",
                options=options,
                custom_id="adoption_select"
            )
            select.callback = self._adoption_callback
            self.add_item(select)

    async def _adoption_callback(self, interaction: discord.Interaction):
        """Handle adoption selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        pet_id = interaction.data["values"][0]
        result = await self.bot.pet_system.adopt_pet(self.user_id, pet_id)
        
        if result["success"]:
            embed = create_embed(
                title="🏠 Adoption Successful!",
                description=f"Welcome **{result['pet_name']}** to your family!",
                color=discord.Color.green()
            )
        else:
            embed = create_embed(
                title="❌ Adoption Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TrainingView(discord.ui.View):
    def __init__(self, bot, user_id: int, active_pet: dict, training_options: list):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.user_id = user_id
        self.active_pet = active_pet
        self.training_options = training_options
        self._add_training_select()

    def _add_training_select(self):
        """Add training selection dropdown"""
        options = []
        for option in self.training_options[:25]:  # Discord limit
            cost = option.get("cost", 0)
            exp_gain = option.get("exp_gain", 0)
            options.append(discord.SelectOption(
                label=f"{option['name']} - {format_number(cost)} gold",
                description=f"EXP Gain: {exp_gain}",
                value=option["id"]
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder="🎓 Select training option",
                options=options,
                custom_id="training_select"
            )
            select.callback = self._training_callback
            self.add_item(select)

    async def _training_callback(self, interaction: discord.Interaction):
        """Handle training selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        training_id = interaction.data["values"][0]
        result = await self.bot.pet_system.train_pet(self.user_id, training_id)
        
        if result["success"]:
            embed = create_embed(
                title="🎓 Training Successful!",
                description=f"**{result['pet_name']}** gained {result['exp_gained']} EXP!",
                color=discord.Color.green()
            )
            
            if result.get("leveled_up"):
                embed.add_field(name="🎉 Level Up!", value=f"**{result['pet_name']}** reached level {result['new_level']}!", inline=False)
        else:
            embed = create_embed(
                title="❌ Training Failed",
                description=result["message"],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PetsCog(bot))
