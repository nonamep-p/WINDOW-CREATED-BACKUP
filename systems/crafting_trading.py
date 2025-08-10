import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from enum import Enum
import discord

logger = logging.getLogger(__name__)

class ItemRarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"

class CraftingDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    MASTER = "master"

class CraftingTradingSystem:
    def __init__(self, db, character_system=None, inventory_system=None):
        self.db = db
        self.character_system = character_system
        self.inventory_system = inventory_system
        self.active_crafts: Dict[str, Dict] = {}
        self.market_listings: Dict[str, Dict] = {}
        self.crafting_recipes: Dict[str, Dict] = {}
        
        # Initialize recipes
        self._initialize_recipes()
        
        # Market dynamics
        self.market_multipliers = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 1.2,
            ItemRarity.RARE: 1.5,
            ItemRarity.EPIC: 2.0,
            ItemRarity.LEGENDARY: 3.0
        }

    def _initialize_recipes(self):
        """Initialize crafting recipes"""
        self.crafting_recipes = {
            "iron_sword": {
                "name": "Iron Sword",
                "difficulty": CraftingDifficulty.EASY.value,
                "materials": {
                    "iron_ingot": 2,
                    "wood": 1,
                    "leather": 1
                },
                "tools_required": ["forge"],
                "skill_required": "blacksmithing",
                "skill_level": 1,
                "crafting_time": 30,  # seconds
                "xp_reward": 10,
                "failure_chance": 0.1
            },
            "steel_armor": {
                "name": "Steel Armor",
                "difficulty": CraftingDifficulty.MEDIUM.value,
                "materials": {
                    "steel_ingot": 3,
                    "leather": 2,
                    "cloth": 1
                },
                "tools_required": ["forge", "anvil"],
                "skill_required": "blacksmithing",
                "skill_level": 3,
                "crafting_time": 60,
                "xp_reward": 25,
                "failure_chance": 0.15
            },
            "magic_potion": {
                "name": "Magic Potion",
                "difficulty": CraftingDifficulty.EASY.value,
                "materials": {
                    "herbs": 2,
                    "water": 1,
                    "crystal_dust": 1
                },
                "tools_required": ["alchemy_lab"],
                "skill_required": "alchemy",
                "skill_level": 1,
                "crafting_time": 45,
                "xp_reward": 15,
                "failure_chance": 0.12
            },
            "enchanted_ring": {
                "name": "Enchanted Ring",
                "difficulty": CraftingDifficulty.HARD.value,
                "materials": {
                    "gold_ingot": 1,
                    "gemstone": 1,
                    "magic_essence": 2
                },
                "tools_required": ["jewelry_bench", "enchanting_table"],
                "skill_required": "jewelcrafting",
                "skill_level": 5,
                "crafting_time": 120,
                "xp_reward": 50,
                "failure_chance": 0.25
            },
            "legendary_blade": {
                "name": "Legendary Blade",
                "difficulty": CraftingDifficulty.MASTER.value,
                "materials": {
                    "mythril_ingot": 3,
                    "dragon_scale": 1,
                    "ancient_core": 1,
                    "enchanted_gem": 2
                },
                "tools_required": ["master_forge", "enchanting_table"],
                "skill_required": "blacksmithing",
                "skill_level": 10,
                "crafting_time": 300,
                "xp_reward": 200,
                "failure_chance": 0.4
            }
        }

    async def start_crafting(self, user_id: int, recipe_id: str, quantity: int = 1) -> Dict:
        """Start crafting an item"""
        # Check if recipe exists
        recipe = self.crafting_recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "message": "Recipe not found!"}

        # Check if user has required materials
        character = await self.character_system.get_character(user_id)
        inventory = character.get("inventory", {})
        
        for material, required_amount in recipe["materials"].items():
            total_required = required_amount * quantity
            available = inventory.get(material, {}).get("quantity", 0)
            if available < total_required:
                return {"success": False, "message": f"Not enough {material}! Need {total_required}, have {available}"}

        # Check if user has required tools
        tools = character.get("tools", [])
        for tool in recipe["tools_required"]:
            if tool not in tools:
                return {"success": False, "message": f"Missing required tool: {tool}"}

        # Check skill level
        skills = character.get("skills", {})
        skill_level = skills.get(recipe["skill_required"], 0)
        if skill_level < recipe["skill_level"]:
            return {"success": False, "message": f"Skill level too low! Need {recipe['skill_required']} level {recipe['skill_level']}"}

        # Consume materials
        for material, required_amount in recipe["materials"].items():
            total_required = required_amount * quantity
            inventory[material]["quantity"] -= total_required
            if inventory[material]["quantity"] <= 0:
                del inventory[material]

        # Start crafting
        craft_id = f"craft_{user_id}_{recipe_id}_{int(datetime.utcnow().timestamp())}"
        craft_data = {
            "craft_id": craft_id,
            "user_id": user_id,
            "recipe_id": recipe_id,
            "recipe": recipe,
            "quantity": quantity,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(seconds=recipe["crafting_time"] * quantity),
            "status": "active",
            "progress": 0,
            "skill_level": skill_level
        }

        self.active_crafts[craft_id] = craft_data
        await self.db.save_player(character)

        return {"success": True, "craft_id": craft_id, "craft": craft_data}

    async def check_crafting_progress(self, craft_id: str) -> Dict:
        """Check the progress of a crafting job"""
        craft = self.active_crafts.get(craft_id)
        if not craft:
            return {"success": False, "message": "Crafting job not found!"}

        now = datetime.utcnow()
        if now >= craft["end_time"]:
            return await self._complete_crafting(craft_id)
        
        # Calculate progress percentage
        total_time = (craft["end_time"] - craft["start_time"]).total_seconds()
        elapsed_time = (now - craft["start_time"]).total_seconds()
        progress = min(100, (elapsed_time / total_time) * 100)
        
        craft["progress"] = progress
        return {"success": True, "craft": craft, "progress": progress}

    async def _complete_crafting(self, craft_id: str) -> Dict:
        """Complete a crafting job and award the item"""
        craft = self.active_crafts[craft_id]
        recipe = craft["recipe"]
        
        # Calculate success chance based on skill level
        base_failure_chance = recipe["failure_chance"]
        skill_bonus = min(0.3, craft["skill_level"] * 0.02)  # Max 30% bonus from skill
        final_failure_chance = max(0.05, base_failure_chance - skill_bonus)
        
        success = random.random() > final_failure_chance
        
        if success:
            # Award the crafted item
            character = await self.character_system.get_character(craft["user_id"])
            inventory = character.get("inventory", {})
            
            item_id = craft["recipe_id"]
            if item_id in inventory:
                inventory[item_id]["quantity"] += craft["quantity"]
            else:
                inventory[item_id] = {
                    "name": recipe["name"],
                    "quantity": craft["quantity"],
                    "crafted_by": craft["user_id"],
                    "crafted_at": datetime.utcnow().isoformat()
                }
            
            # Award XP
            xp_gain = recipe["xp_reward"] * craft["quantity"]
            character["xp"] += xp_gain
            
            # Increase skill level
            skills = character.get("skills", {})
            skill_name = recipe["skill_required"]
            current_skill_xp = skills.get(f"{skill_name}_xp", 0)
            skills[f"{skill_name}_xp"] = current_skill_xp + xp_gain
            
            # Check for skill level up
            skill_level = skills.get(skill_name, 0)
            xp_for_next_level = skill_level * 100  # Simple progression
            if skills[f"{skill_name}_xp"] >= xp_for_next_level:
                skills[skill_name] = skill_level + 1
                skills[f"{skill_name}_xp"] = 0
            
            await self.db.save_player(character)
            
            craft["status"] = "completed"
            craft["result"] = "success"
            craft["items_created"] = craft["quantity"]
            
            return {"success": True, "craft": craft, "message": f"Successfully crafted {craft['quantity']} {recipe['name']}!"}
        else:
            # Crafting failed
            craft["status"] = "failed"
            craft["result"] = "failure"
            
            return {"success": True, "craft": craft, "message": f"Crafting failed! You lost the materials."}

    async def list_item_on_market(self, user_id: int, item_id: str, quantity: int, price: int) -> Dict:
        """List an item on the market"""
        # Check if user has the item
        character = await self.character_system.get_character(user_id)
        inventory = character.get("inventory", {})
        
        if item_id not in inventory or inventory[item_id]["quantity"] < quantity:
            return {"success": False, "message": "You don't have enough of this item!"}

        # Remove item from inventory
        inventory[item_id]["quantity"] -= quantity
        if inventory[item_id]["quantity"] <= 0:
            del inventory[item_id]

        # Create market listing
        listing_id = f"listing_{user_id}_{item_id}_{int(datetime.utcnow().timestamp())}"
        listing_data = {
            "listing_id": listing_id,
            "seller_id": user_id,
            "seller_name": character["username"],
            "item_id": item_id,
            "item_name": inventory.get(item_id, {}).get("name", item_id),
            "quantity": quantity,
            "price_per_unit": price,
            "total_price": price * quantity,
            "listed_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "status": "active"
        }

        self.market_listings[listing_id] = listing_data
        await self.db.save_player(character)

        return {"success": True, "listing": listing_data, "message": f"Listed {quantity} {listing_data['item_name']} for {price} gold each!"}

    async def buy_from_market(self, buyer_id: int, listing_id: str, quantity: int = None) -> Dict:
        """Buy an item from the market"""
        listing = self.market_listings.get(listing_id)
        if not listing or listing["status"] != "active":
            return {"success": False, "message": "Listing not found or expired!"}

        if listing["expires_at"] < datetime.utcnow():
            listing["status"] = "expired"
            return {"success": False, "message": "Listing has expired!"}

        # Determine quantity to buy
        buy_quantity = quantity if quantity else listing["quantity"]
        if buy_quantity > listing["quantity"]:
            return {"success": False, "message": "Not enough items available!"}

        # Check if buyer has enough gold
        buyer = await self.character_system.get_character(buyer_id)
        total_cost = listing["price_per_unit"] * buy_quantity
        
        if buyer["gold"] < total_cost:
            return {"success": False, "message": "Not enough gold!"}

        # Process transaction
        buyer["gold"] -= total_cost
        seller = await self.character_system.get_character(listing["seller_id"])
        seller["gold"] += total_cost

        # Transfer items
        buyer_inventory = buyer.get("inventory", {})
        if listing["item_id"] in buyer_inventory:
            buyer_inventory[listing["item_id"]]["quantity"] += buy_quantity
        else:
            buyer_inventory[listing["item_id"]] = {
                "name": listing["item_name"],
                "quantity": buy_quantity,
                "purchased_from": listing["seller_id"]
            }

        # Update listing
        listing["quantity"] -= buy_quantity
        if listing["quantity"] <= 0:
            listing["status"] = "sold"

        # Save changes
        await self.db.save_player(buyer)
        await self.db.save_player(seller)

        return {"success": True, "message": f"Purchased {buy_quantity} {listing['item_name']} for {total_cost} gold!"}

    async def cancel_market_listing(self, user_id: int, listing_id: str) -> Dict:
        """Cancel a market listing and return items"""
        listing = self.market_listings.get(listing_id)
        if not listing:
            return {"success": False, "message": "Listing not found!"}

        if listing["seller_id"] != user_id:
            return {"success": False, "message": "You can only cancel your own listings!"}

        if listing["status"] != "active":
            return {"success": False, "message": "Listing is not active!"}

        # Return items to seller
        seller = await self.character_system.get_character(user_id)
        inventory = seller.get("inventory", {})
        
        if listing["item_id"] in inventory:
            inventory[listing["item_id"]]["quantity"] += listing["quantity"]
        else:
            inventory[listing["item_id"]] = {
                "name": listing["item_name"],
                "quantity": listing["quantity"]
            }

        listing["status"] = "cancelled"
        await self.db.save_player(seller)

        return {"success": True, "message": f"Cancelled listing and returned {listing['quantity']} {listing['item_name']}!"}

    def get_market_listings(self, item_type: str = None, max_price: int = None, seller_id: int = None) -> List[Dict]:
        """Get market listings with optional filters"""
        listings = []
        
        for listing in self.market_listings.values():
            if listing["status"] != "active":
                continue
                
            if listing["expires_at"] < datetime.utcnow():
                listing["status"] = "expired"
                continue
            
            # Apply filters
            if item_type and item_type not in listing["item_name"].lower():
                continue
            if max_price and listing["price_per_unit"] > max_price:
                continue
            if seller_id and listing["seller_id"] != seller_id:
                continue
            
            listings.append(listing)
        
        # Sort by price (lowest first)
        listings.sort(key=lambda x: x["price_per_unit"])
        return listings

    def get_crafting_recipes(self, skill_name: str = None, difficulty: str = None) -> List[Dict]:
        """Get available crafting recipes with optional filters"""
        recipes = []
        
        for recipe_id, recipe in self.crafting_recipes.items():
            # Apply filters
            if skill_name and recipe["skill_required"] != skill_name:
                continue
            if difficulty and recipe["difficulty"] != difficulty:
                continue
            
            recipes.append({
                "recipe_id": recipe_id,
                **recipe
            })
        
        return recipes

    def get_player_crafting_progress(self, user_id: int) -> List[Dict]:
        """Get all active crafting jobs for a player"""
        active_crafts = []
        
        for craft in self.active_crafts.values():
            if craft["user_id"] == user_id and craft["status"] == "active":
                active_crafts.append(craft)
        
        return active_crafts

    def calculate_market_price(self, item_data: Dict, base_price: int) -> int:
        """Calculate market price based on rarity and demand"""
        rarity = item_data.get("rarity", ItemRarity.COMMON.value)
        rarity_multiplier = self.market_multipliers.get(ItemRarity(rarity), 1.0)
        
        # Add some randomness to simulate market fluctuations
        market_variance = random.uniform(0.8, 1.2)
        
        return int(base_price * rarity_multiplier * market_variance)

    def get_crafting_embed(self, craft: Dict) -> Dict:
        """Generate crafting progress embed"""
        recipe = craft["recipe"]
        progress = craft.get("progress", 0)
        
        embed_data = {
            "title": f"🔨 Crafting: {recipe['name']}",
            "description": f"Progress: {progress:.1f}% | Quantity: {craft['quantity']}",
            "color": discord.Color.blue(),
            "fields": [
                {
                    "name": "📋 Recipe Details",
                    "value": f"Difficulty: {recipe['difficulty'].title()}\n"
                            f"Skill: {recipe['skill_required'].title()} (Level {recipe['skill_level']})\n"
                            f"Time: {recipe['crafting_time']} seconds\n"
                            f"XP Reward: {recipe['xp_reward']}",
                    "inline": True
                },
                {
                    "name": "📦 Materials Required",
                    "value": "\n".join([f"• {material}: {amount * craft['quantity']}" 
                                       for material, amount in recipe["materials"].items()]),
                    "inline": True
                }
            ]
        }

        if progress >= 100:
            embed_data["color"] = discord.Color.green()
            embed_data["description"] += " | ✅ Complete!"

        return embed_data

    async def cancel_crafting(self, user_id: int, craft_id: str) -> Dict:
        """Cancel a specific crafting job"""
        try:
            if craft_id not in self.active_crafts:
                return {"success": False, "message": "Crafting job not found"}
            
            craft = self.active_crafts[craft_id]
            if craft["user_id"] != user_id:
                return {"success": False, "message": "This is not your crafting job"}
            
            # Return materials to inventory
            recipe = craft["recipe"]
            materials = recipe["materials"]
            quantity = craft["quantity"]
            
            for material, amount in materials.items():
                total_amount = amount * quantity
                await self.inventory_system.add_item(user_id, material, total_amount)
            
            # Remove from active crafts
            del self.active_crafts[craft_id]
            
            return {
                "success": True, 
                "message": f"Crafting job cancelled. Materials returned to inventory.",
                "materials_returned": {mat: amt * quantity for mat, amt in materials.items()}
            }
            
        except Exception as e:
            logger.error(f"Error cancelling craft: {e}")
            return {"success": False, "message": "Failed to cancel crafting job"}

    def get_crafting_recipes(self, skill_filter: str = None, difficulty_filter: str = None) -> List[Dict]:
        """Get available crafting recipes with optional filters"""
        recipes = []
        
        for recipe_id, recipe in self.crafting_recipes.items():
            # Apply filters
            if skill_filter and recipe.get("skill_required") != skill_filter.lower():
                continue
            if difficulty_filter and recipe.get("difficulty") != difficulty_filter.lower():
                continue
            
            recipe_copy = recipe.copy()
            recipe_copy["id"] = recipe_id
            recipes.append(recipe_copy)
        
        return recipes

    def get_player_crafting_progress(self, user_id: int) -> List[Dict]:
        """Get all active crafting jobs for a player"""
        player_crafts = []
        
        for craft_id, craft in self.active_crafts.items():
            if craft["user_id"] == user_id:
                player_crafts.append(craft)
        
        return player_crafts

    async def check_crafting_progress(self, craft_id: str) -> Dict:
        """Check the progress of a specific crafting job"""
        try:
            if craft_id not in self.active_crafts:
                return {"success": False, "message": "Crafting job not found"}
            
            craft = self.active_crafts[craft_id]
            start_time = datetime.fromisoformat(craft["start_time"])
            current_time = datetime.utcnow()
            elapsed_time = (current_time - start_time).total_seconds()
            
            total_time = craft["recipe"]["crafting_time"] * craft["quantity"]
            
            if elapsed_time >= total_time:
                # Crafting completed
                result = await self._complete_crafting(craft_id)
                return {
                    "success": True,
                    "craft": result,
                    "progress": None  # None indicates completion
                }
            else:
                # Still in progress
                progress = (elapsed_time / total_time) * 100
                craft["time_remaining"] = int(total_time - elapsed_time)
                
                return {
                    "success": True,
                    "progress": min(100.0, progress),
                    "time_remaining": int(total_time - elapsed_time)
                }
                
        except Exception as e:
            logger.error(f"Error checking craft progress: {e}")
            return {"success": False, "message": "Failed to check crafting progress"}

    async def get_market_listings(self) -> List[Dict]:
        """Get all active market listings"""
        active_listings = []
        current_time = datetime.utcnow()
        
        # Clean up expired listings
        expired_listings = []
        for listing_id, listing in self.market_listings.items():
            expires_at = datetime.fromisoformat(listing["expires_at"])
            if current_time > expires_at:
                expired_listings.append(listing_id)
            else:
                active_listings.append(listing)
        
        # Remove expired listings
        for listing_id in expired_listings:
            del self.market_listings[listing_id]
        
        return active_listings

    def get_market_embed(self, listings: List[Dict]) -> Dict:
        """Create market embed data"""
        if not listings:
            return {
                "title": "🏪 Market",
                "description": "No active listings found.",
                "color": discord.Color.greyple(),
                "fields": []
            }
        
        # Group by item type
        grouped_listings = {}
        for listing in listings:
            item_name = listing["item_name"]
            if item_name not in grouped_listings:
                grouped_listings[item_name] = []
            grouped_listings[item_name].append(listing)
        
        fields = []
        for item_name, item_listings in grouped_listings.items():
            # Find best price
            best_price = min([listing["price_per_unit"] for listing in item_listings])
            total_quantity = sum([listing["quantity"] for listing in item_listings])
            
            value = f"**Available:** {total_quantity}\n"
            value += f"**Best Price:** {best_price} gold each\n"
            value += f"**Listings:** {len(item_listings)}"
            
            fields.append({
                "name": f"📦 {item_name}",
                "value": value,
                "inline": True
            })
        
        return {
            "title": "🏪 Market Listings",
            "description": f"Showing {len(grouped_listings)} different items",
            "color": discord.Color.gold(),
            "fields": fields
        }
