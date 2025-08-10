import json
import asyncio
from typing import Dict, List, Optional
from .database import DatabaseManager

class PetSystem:
    def __init__(self, db: DatabaseManager, character_system=None):
        self.db = db
        self.character_system = character_system
        
    async def get_pets(self, user_id: int) -> List[Dict]:
        """Get all pets owned by user"""
        try:
            player = await self.db.load_player_data(user_id)
            return player.get("pets", [])
        except Exception as e:
            print(f"Error getting pets: {e}")
            return []
            
    async def get_active_pet(self, user_id: int) -> Optional[Dict]:
        """Get user's active pet"""
        try:
            player = await self.db.load_player_data(user_id)
            pets = player.get("pets", [])
            for pet in pets:
                if pet.get("active", False):
                    return pet
            return None
        except Exception as e:
            print(f"Error getting active pet: {e}")
            return None
            
    async def get_available_pets(self) -> List[Dict]:
        """Get list of pets available for adoption"""
        return [
            {
                "id": "wolf_pup",
                "name": "Wolf Pup",
                "description": "A loyal companion that grows stronger with training",
                "cost": 500,
                "stats": {"attack": 5, "defense": 3, "speed": 7},
                "rarity": "Common"
            },
            {
                "id": "fire_salamander", 
                "name": "Fire Salamander",
                "description": "A magical creature that can breathe small flames",
                "cost": 800,
                "stats": {"attack": 8, "defense": 4, "speed": 5},
                "rarity": "Uncommon"
            },
            {
                "id": "crystal_drake",
                "name": "Crystal Drake", 
                "description": "A rare dragon hatchling with crystalline scales",
                "cost": 1500,
                "stats": {"attack": 12, "defense": 8, "speed": 6},
                "rarity": "Rare"
            }
        ]
        
    async def get_training_options(self, pet: Dict) -> List[Dict]:
        """Get training options for a pet"""
        if not pet:
            return []
            
        return [
            {
                "id": "strength_training",
                "name": "Strength Training",
                "description": "Increases attack power",
                "cost": 100,
                "stat": "attack",
                "increase": 1
            },
            {
                "id": "defense_training", 
                "name": "Defense Training",
                "description": "Increases defense",
                "cost": 100,
                "stat": "defense", 
                "increase": 1
            },
            {
                "id": "agility_training",
                "name": "Agility Training", 
                "description": "Increases speed",
                "cost": 100,
                "stat": "speed",
                "increase": 1
            }
        ]
        
    async def set_active_pet(self, user_id: int, pet_id: str) -> Dict:
        """Set a pet as active"""
        try:
            player = await self.db.load_player_data(user_id)
            pets = player.get("pets", [])
            
            # Deactivate all pets
            for pet in pets:
                pet["active"] = False
                
            # Activate selected pet
            for pet in pets:
                if pet.get("id") == pet_id:
                    pet["active"] = True
                    player["pets"] = pets
                    await self.db.save_player(user_id, player)
                    return {"success": True, "message": f"Set {pet['name']} as active pet!"}
                    
            return {"success": False, "message": "Pet not found"}
        except Exception as e:
            print(f"Error setting active pet: {e}")
            return {"success": False, "message": "Failed to set active pet"}
            
    async def train_pet(self, user_id: int, training_id: str) -> Dict:
        """Train a pet"""
        try:
            player = await self.db.load_player_data(user_id)
            active_pet = None
            
            # Find active pet
            for pet in player.get("pets", []):
                if pet.get("active", False):
                    active_pet = pet
                    break
                    
            if not active_pet:
                return {"success": False, "message": "No active pet found"}
                
            training_options = await self.get_training_options(active_pet)
            training = None
            
            for option in training_options:
                if option["id"] == training_id:
                    training = option
                    break
                    
            if not training:
                return {"success": False, "message": "Training not found"}
                
            # Check if player has enough gold
            if player.get("gold", 0) < training["cost"]:
                return {"success": False, "message": "Not enough gold"}
                
            # Apply training
            player["gold"] -= training["cost"]
            stat = training["stat"]
            increase = training["increase"]
            
            if stat in active_pet.get("stats", {}):
                active_pet["stats"][stat] += increase
            else:
                active_pet["stats"][stat] = increase
                
            await self.db.save_player(user_id, player)
            return {"success": True, "message": f"Trained {active_pet['name']} in {training['name']}!"}
            
        except Exception as e:
            print(f"Error training pet: {e}")
            return {"success": False, "message": "Failed to train pet"}
            
    async def adopt_pet(self, user_id: int, pet_id: str) -> Dict:
        """Adopt a new pet"""
        try:
            player = await self.db.load_player_data(user_id)
            available_pets = await self.get_available_pets()
            
            pet_to_adopt = None
            for pet in available_pets:
                if pet["id"] == pet_id:
                    pet_to_adopt = pet
                    break
                    
            if not pet_to_adopt:
                return {"success": False, "message": "Pet not found"}
                
            # Check if player has enough gold
            if player.get("gold", 0) < pet_to_adopt["cost"]:
                return {"success": False, "message": "Not enough gold"}
                
            # Check if player already has this pet
            current_pets = player.get("pets", [])
            for pet in current_pets:
                if pet["id"] == pet_id:
                    return {"success": False, "message": "You already own this pet"}
                    
            # Adopt pet
            player["gold"] -= pet_to_adopt["cost"]
            new_pet = pet_to_adopt.copy()
            new_pet["active"] = len(current_pets) == 0  # First pet is automatically active
            new_pet["level"] = 1
            new_pet["experience"] = 0
            
            current_pets.append(new_pet)
            player["pets"] = current_pets
            
            await self.db.save_player(user_id, player)
            return {"success": True, "message": f"Successfully adopted {pet_to_adopt['name']}!"}
            
        except Exception as e:
            print(f"Error adopting pet: {e}")
            return {"success": False, "message": "Failed to adopt pet"}

