import random
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class DamageType(Enum):
    PHYSICAL = "physical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    SHADOW = "shadow"
    MAGIC = "magic"

class StatusEffect(Enum):
    BURN = "burn"
    FROST = "frost"
    SHOCK = "shock"
    POISON = "poison"
    BLEED = "bleed"
    STUN = "stun"
    SILENCE = "silence"
    TAUNT = "taunt"
    HASTE = "haste"
    SLOW = "slow"
    REGEN = "regen"
    SHIELD = "shield"

class AdvancedCombatSystem:
    def __init__(self, db, character_system=None, inventory_system=None):
        self.db = db
        self.character_system = character_system
        self.inventory_system = inventory_system
        
        # Elemental effectiveness matrix
        self.elemental_effectiveness = {
            DamageType.FIRE: {DamageType.ICE: 1.5},
            DamageType.ICE: {DamageType.FIRE: 1.5},
            DamageType.LIGHTNING: {DamageType.ICE: 1.5},
            DamageType.POISON: {DamageType.HOLY: 0.5},
            DamageType.HOLY: {DamageType.SHADOW: 1.5},
            DamageType.SHADOW: {DamageType.HOLY: 1.5}
        }
        
        # Status effect definitions
        self.status_effects = {
            StatusEffect.BURN: {"damage_per_turn": 5, "duration": 3},
            StatusEffect.FROST: {"speed_reduction": 0.3, "duration": 2},
            StatusEffect.SHOCK: {"stun_chance": 0.3, "duration": 1},
            StatusEffect.POISON: {"damage_per_turn": 3, "duration": 4},
            StatusEffect.BLEED: {"damage_per_turn": 4, "duration": 3},
            StatusEffect.STUN: {"skip_turn": True, "duration": 1},
            StatusEffect.SILENCE: {"cannot_cast": True, "duration": 2},
            StatusEffect.TAUNT: {"forced_target": True, "duration": 2},
            StatusEffect.HASTE: {"speed_bonus": 0.3, "damage_bonus": 0.2, "duration": 3},
            StatusEffect.SLOW: {"speed_reduction": 0.3, "damage_reduction": 0.2, "duration": 2},
            StatusEffect.REGEN: {"heal_per_turn": 8, "duration": 3},
            StatusEffect.SHIELD: {"damage_reduction": 0.4, "duration": 2}
        }
        
        # Combo system
        self.combo_multipliers = {
            1: 1.0,   # No combo
            2: 1.1,   # 2-hit combo
            3: 1.25,  # 3-hit combo
            4: 1.4,   # 4-hit combo
            5: 1.6    # 5+ hit combo
        }
    
    async def calculate_elemental_damage(self, base_damage: int, damage_type: DamageType, 
                                       target_resistances: Dict[DamageType, float]) -> int:
        """Calculate damage with elemental effectiveness"""
        effectiveness = 1.0
        if damage_type in self.elemental_effectiveness:
            for target_type, multiplier in self.elemental_effectiveness[damage_type].items():
                if target_type in target_resistances:
                    effectiveness *= multiplier
        
        resistance = target_resistances.get(damage_type, 1.0)
        final_damage = int(base_damage * effectiveness * resistance)
        return max(1, final_damage)
    
    async def apply_status_effect(self, target: Dict, effect: StatusEffect, 
                                caster: Dict, duration: int = None) -> bool:
        """Apply a status effect to a target"""
        if effect not in self.status_effects:
            return False
        
        effect_data = self.status_effects[effect].copy()
        if duration:
            effect_data["duration"] = duration
        
        if "status_effects" not in target:
            target["status_effects"] = {}
        
        target["status_effects"][effect.value] = [{
            "caster": caster.get("id"),
            "duration": effect_data["duration"],
            "data": effect_data
        }]
        return True
    
    async def process_status_effects(self, target: Dict) -> Dict:
        """Process status effects on a target"""
        effects_processed = {}
        
        if "status_effects" not in target:
            return effects_processed
        
        for effect_name, effect_list in target["status_effects"].items():
            if not effect_list:
                continue
            
            for effect in effect_list[:]:
                effect["duration"] -= 1
                
                if effect_name == StatusEffect.BURN.value:
                    damage = effect["data"]["damage_per_turn"]
                    target["hp"] = max(0, target["hp"] - damage)
                    effects_processed["burn_damage"] = effects_processed.get("burn_damage", 0) + damage
                
                elif effect_name == StatusEffect.POISON.value:
                    damage = effect["data"]["damage_per_turn"]
                    target["hp"] = max(0, target["hp"] - damage)
                    effects_processed["poison_damage"] = effects_processed.get("poison_damage", 0) + damage
                
                elif effect_name == StatusEffect.REGEN.value:
                    heal = effect["data"]["heal_per_turn"]
                    max_hp = target.get("max_hp", target["hp"])
                    target["hp"] = min(max_hp, target["hp"] + heal)
                    effects_processed["regen_heal"] = effects_processed.get("regen_heal", 0) + heal
                
                if effect["duration"] <= 0:
                    effect_list.remove(effect)
        
        return effects_processed
    
    async def calculate_combo_damage(self, base_damage: int, combo_count: int) -> int:
        """Calculate damage with combo multiplier"""
        multiplier = self.combo_multipliers.get(combo_count, 1.0)
        return int(base_damage * multiplier)
    
    async def get_ai_action(self, ai_entity: Dict, player: Dict, 
                           available_actions: List[str]) -> str:
        """Determine AI action based on behavior pattern"""
        health_percentage = ai_entity["hp"] / ai_entity.get("max_hp", ai_entity["hp"])
        
        if health_percentage < 0.3:
            return "defend" if "defend" in available_actions else available_actions[0]
        elif health_percentage < 0.6:
            return random.choice(available_actions)
        else:
            return "attack" if "attack" in available_actions else available_actions[0]
