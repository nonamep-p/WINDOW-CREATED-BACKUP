import random
import asyncio
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import logging

from utils.helpers import calculate_damage, is_critical_hit, get_plagg_quote
from systems.combat_math import hit_roll, crit_roll, phys_damage
from random import Random

logger = logging.getLogger(__name__)

class CombatSystem:
    def __init__(self, db, character_system=None, inventory_system=None):
        self.db = db
        self.character_system = character_system
        self.inventory_system = inventory_system
        self.active_battles: Dict[str, Dict] = {}
        # Party combat sessions keyed by combat_id
        self.party_combats: Dict[str, Dict] = {}
        
        # Status effect definitions
        self.status_effects = {
            "burn": {
                "name": "🔥 Burning",
                "description": "Takes fire damage over time",
                "dot": 8,  # damage over time
                "type": "debuff"
            },
            "poison": {
                "name": "☠️ Poisoned", 
                "description": "Takes poison damage over time",
                "dot": 6,
                "type": "debuff"
            },
            "slow": {
                "name": "🐌 Slowed",
                "description": "Reduced speed and accuracy",
                "stat_modifiers": {"speed": -0.3, "accuracy": -10},
                "type": "debuff"
            },
            "shock": {
                "name": "⚡ Shocked",
                "description": "Stunned and unable to act",
                "stun": True,
                "type": "debuff"
            },
            "regeneration": {
                "name": "💚 Regenerating",
                "description": "Slowly heals over time",
                "hot": 12,  # heal over time
                "type": "buff"
            },
            "blessing": {
                "name": "✨ Blessed",
                "description": "Increased damage and accuracy",
                "stat_modifiers": {"attack": 0.2, "accuracy": 15},
                "type": "buff"
            },
            "shield_boost": {
                "name": "🛡️ Shielded",
                "description": "Increased defense",
                "stat_modifiers": {"defense": 0.5},
                "type": "buff"
            },
            "weakness": {
                "name": "💔 Weakened",
                "description": "Reduced attack power",
                "stat_modifiers": {"attack": -0.3},
                "type": "debuff"
            }
        }
        
    async def start_battle(self, user_id: int, monster: Dict) -> Dict:
        """Start a new battle between a player and a monster using player data from DB."""
        # Prevent multiple concurrent battles per user
        for existing_battle in self.active_battles.values():
            if existing_battle["user_id"] == user_id and existing_battle["status"] == "active":
                return {"success": False, "message": "You're already in battle!"}

        character = await self.db.get_player(user_id)
        if not character:
            return {"success": False, "message": "Character not found"}
        # Build player snapshot with derived stats
        if self.character_system:
            derived = self.character_system.get_current_stats(character)
            if not isinstance(derived, dict):
                derived = character.get("stats", {}) or {}
            stats = {
                "hp": derived.get("max_hp", derived.get("hp", 100)),
                "sp": derived.get("max_sp", derived.get("sp", 50)),
                "attack": derived.get("attack", 10),
                "defense": derived.get("defense", 5),
                "speed": derived.get("speed", 5),
                "intelligence": derived.get("intelligence", 5),
                "luck": derived.get("luck", 5),
                "agility": derived.get("agility", 5),
                "accuracy": derived.get("accuracy", 60),
                "evasion": derived.get("evasion", 20),
                "pen": derived.get("pen", 0),
                "crit_base": 0.05,
                "crit_dmg": 1.5,
            }
        else:
            stats = character.get("stats", {})
        player_snapshot = {
            "name": character.get("username", "Player"),
            "hp": stats.get("hp", stats.get("max_hp", 100)),
            "sp": stats.get("sp", stats.get("max_sp", 50)),
            "attack": stats.get("attack", 10),
            "defense": stats.get("defense", 5),
            "speed": stats.get("speed", 5),
            "intelligence": stats.get("intelligence", 5),
            "luck": stats.get("luck", 5),
            "agility": stats.get("agility", 5),
            "accuracy": stats.get("accuracy", 60),
            "evasion": stats.get("evasion", 20),
            "pen": stats.get("pen", 0),
            "crit_base": 0.05,
            "crit_dmg": 1.5,
        }
        # Apply small companion bonuses
        companion = character.get("companion") or {}
        comp_skills = companion.get("skills", {}) if isinstance(companion, dict) else {}
        player_snapshot["attack"] += int(comp_skills.get("attack", 0))
        player_snapshot["defense"] += int(comp_skills.get("defense", 0))

        # Monster snapshot
        monster_snapshot = {
            "name": monster.get("name", "Monster"),
            "hp": monster.get("hp", monster.get("stats", {}).get("hp", 10)),
            "attack": monster.get("attack", monster.get("stats", {}).get("atk", 1)),
            "defense": monster.get("defense", monster.get("stats", {}).get("defense", 0)),
            "level": monster.get("level", 1),
            "xp_reward": monster.get("xp_reward", 10),
            "gold_reward": monster.get("gold_reward", 5),
            "accuracy": monster.get("stats", {}).get("accuracy", 50),
            "evasion": monster.get("stats", {}).get("evasion", 10),
        }

        battle_id = f"{user_id}_{int(datetime.utcnow().timestamp())}"
        battle = {
            "battle_id": battle_id,
            "user_id": user_id,
            "player": {
                **player_snapshot,
                "current_hp": player_snapshot["hp"],
                "current_sp": player_snapshot["sp"],
                "shield": 0,
                "statuses": [],
                "skills": character.get("skills", []),
            },
            "monster": {
                **monster_snapshot,
                "current_hp": monster_snapshot["hp"],
                "shield": 0,
                "statuses": [],
            },
            # Deterministic RNG seed per battle for fairness and debugging
            "seed": hash(f"{user_id}:{monster_snapshot['name']}:{battle_id}") & 0xFFFFFFFF,
            "turn": 1,
            "start_time": datetime.utcnow().isoformat(),
            "battle_log": [],
            "status": "active",
            "battle_ended": False,
            "winner": None,
            "rewards": {"xp": 0, "gold": 0},
            "cooldowns": {},  # skill_id -> remaining turns
        }

        self.active_battles[battle_id] = battle

        battle["battle_log"].append(f"🐾 Battle started (seed {str(battle['seed'])[:4]})! {battle['player']['name']} vs {battle['monster']['name']}")

        return {"success": True, "battle": battle}
    
    async def get_battle_status(self, battle_id: str) -> Optional[Dict]:
        """Get the current battle status by battle ID."""
        return self.active_battles.get(battle_id)
    
    async def get_user_battle(self, user_id: int) -> Optional[Dict]:
        """Return the active battle for a user if any."""
        for battle in self.active_battles.values():
            if battle.get("user_id") == user_id and battle.get("status") == "active":
                return battle
        return None
    
    async def perform_action(self, battle_id: str, action: str, arg: Optional[str] = None) -> Dict:
        """Perform a battle action: attack, defend, flee."""
        battle = self.active_battles.get(battle_id)
        if not battle or battle["status"] != "active":
            return {"success": False, "message": "No active battle"}

        if action == "attack":
            return await self._player_attack(battle_id)
        if action == "defend":
            return await self._player_defend(battle_id)
        if action == "flee":
            return await self._player_flee(battle_id)
        if action == "skill" and arg:
            return await self._player_skill(battle_id, arg)
        if action == "item" and arg:
            return await self._player_use_item(battle_id, arg)
        if action == "ultimate":
            return await self._player_ultimate(battle_id)
        return {"success": False, "message": "Unknown action"}

    def _apply_status_modifiers(self, entity: Dict) -> Dict:
        """Apply status effect modifiers to entity stats"""
        modified_stats = {
            "attack": entity.get("attack", 10),
            "defense": entity.get("defense", 5),
            "speed": entity.get("speed", 5),
            "accuracy": entity.get("accuracy", 60),
            "evasion": entity.get("evasion", 20),
        }
        
        original_stats = modified_stats.copy()
        
        # Apply status effect modifiers
        for status in entity.get("statuses", []):
            if isinstance(status, dict):
                status_id = status.get("id", status.get("status"))
                if status_id in self.status_effects:
                    effect_def = self.status_effects[status_id]
                    stat_mods = effect_def.get("stat_modifiers", {})
                    
                    for stat, modifier in stat_mods.items():
                        if stat in modified_stats:
                            if modifier < 0:  # Percentage reduction (negative modifier)
                                modified_stats[stat] = int(modified_stats[stat] * (1 + modifier))
                            elif modifier < 1 and modifier > 0:  # Percentage bonus
                                modified_stats[stat] = int(modified_stats[stat] * (1 + modifier))
                            else:  # Flat bonus
                                modified_stats[stat] += int(modifier)
        
        # Store modifier info for combat log
        modified_stats["_modifiers_applied"] = []
        for stat, value in modified_stats.items():
            if stat != "_modifiers_applied" and value != original_stats[stat]:
                diff = value - original_stats[stat]
                if diff > 0:
                    modified_stats["_modifiers_applied"].append(f"+{diff} {stat}")
                else:
                    modified_stats["_modifiers_applied"].append(f"{diff} {stat}")
        
        return modified_stats

    async def _monster_thinking_phase(self, battle: Dict, monster: Dict, player: Dict):
        """Add realistic monster AI thinking with delays and strategic messages"""
        import asyncio
        
        monster_name = monster.get("name", "Monster")
        player_hp_percent = (player.get("current_hp", 0) / max(1, player.get("hp", 100))) * 100
        monster_hp_percent = (monster.get("current_hp", 0) / max(1, monster.get("hp", 100))) * 100
        
        # Base thinking time (1-3 seconds)
        thinking_time = random.uniform(1.0, 3.0)
        
        # Add strategic thinking messages based on battle state
        thinking_messages = []
        
        # Health-based reactions
        if monster_hp_percent < 25:
            thinking_messages.extend([
                f"💭 {monster_name} looks desperate...",
                f"💭 {monster_name} is breathing heavily...",
                f"💭 {monster_name} snarls with rage!",
                f"💭 {monster_name} prepares a desperate attack..."
            ])
            thinking_time += 0.5  # Longer thinking when low HP
        elif monster_hp_percent < 50:
            thinking_messages.extend([
                f"💭 {monster_name} assesses the situation...",
                f"💭 {monster_name} circles cautiously...",
                f"💭 {monster_name} plans its next move...",
                f"💭 {monster_name} studies your stance..."
            ])
        else:
            thinking_messages.extend([
                f"💭 {monster_name} eyes you confidently...",
                f"💭 {monster_name} flexes menacingly...",
                f"💭 {monster_name} prepares to strike...",
                f"💭 {monster_name} looks for an opening..."
            ])
        
        # Player health-based reactions
        if player_hp_percent < 30:
            thinking_messages.extend([
                f"💭 {monster_name} senses your weakness...",
                f"💭 {monster_name} moves in for the kill...",
                f"💭 {monster_name} smells blood..."
            ])
            thinking_time -= 0.3  # Faster when player is weak
        
        # Status effect reactions
        player_statuses = player.get("statuses", [])
        monster_statuses = monster.get("statuses", [])
        
        if any(isinstance(s, dict) and s.get("id") in ["burn", "poison"] for s in monster_statuses):
            thinking_messages.extend([
                f"💭 {monster_name} writhes in pain...",
                f"💭 {monster_name} struggles against the effects...",
                f"💭 {monster_name} fights through the agony..."
            ])
            thinking_time += 0.4
            
        if any(isinstance(s, dict) and s.get("id") == "slow" for s in monster_statuses):
            thinking_messages.extend([
                f"💭 {monster_name} moves sluggishly...",
                f"💭 {monster_name} shakes off the slowness...",
                f"💭 {monster_name} struggles to focus..."
            ])
            thinking_time += 0.6
        
        # Turn-based behavior
        turn_num = battle.get("turn", 1)
        if turn_num == 1:
            thinking_messages.extend([
                f"💭 {monster_name} sizes you up...",
                f"💭 {monster_name} enters combat stance...",
                f"💭 {monster_name} prepares for battle..."
            ])
            thinking_time += 1.0  # Longer first turn
        elif turn_num > 8:
            thinking_messages.extend([
                f"💭 {monster_name} is getting tired...",
                f"💭 {monster_name} breathes heavily...",
                f"💭 {monster_name} pushes through fatigue..."
            ])
            thinking_time += 0.3
        
        # Select and display thinking message
        if thinking_messages:
            selected_message = random.choice(thinking_messages)
            battle["battle_log"].append(selected_message)
            
            # Store intermediate state for UI updates
            battle["_thinking_phase"] = True
            battle["_thinking_message"] = selected_message
            
            # Add realistic delay with shorter intervals for better UX
            total_time = min(thinking_time, 2.5)  # Cap at 2.5 seconds max
            intervals = max(2, int(total_time / 0.8))  # Update every ~0.8 seconds
            
            for i in range(intervals):
                await asyncio.sleep(total_time / intervals)
                # Could trigger UI updates here if needed
            
            # Clear thinking phase
            battle["_thinking_phase"] = False
            
            # Add action preparation message
            action_prep = [
                f"⚔️ {monster_name} readies an attack!",
                f"⚔️ {monster_name} lunges forward!",
                f"⚔️ {monster_name} strikes!",
                f"⚔️ {monster_name} attacks with fury!",
                f"⚔️ {monster_name} unleashes its power!"
            ]
            battle["battle_log"].append(random.choice(action_prep))

    async def _monster_thinking_phase_safe(self, battle: Dict, monster: Dict, player: Dict):
        """Safe monster AI thinking with shorter delays and error handling"""
        try:
            import asyncio
            
            monster_name = monster.get("name", "Monster")
            player_hp_percent = (player.get("current_hp", 0) / max(1, player.get("hp", 100))) * 100
            monster_hp_percent = (monster.get("current_hp", 0) / max(1, monster.get("hp", 100))) * 100
            
            # Shorter thinking time (0.5-1.5 seconds)
            thinking_time = random.uniform(0.5, 1.5)
            
            # Add strategic thinking messages based on battle state
            thinking_messages = []
            
            # Health-based reactions
            if monster_hp_percent < 25:
                thinking_messages.extend([
                    f"💭 {monster_name} looks desperate...",
                    f"💭 {monster_name} snarls with rage!",
                    f"💭 {monster_name} prepares a desperate attack..."
                ])
            elif monster_hp_percent < 50:
                thinking_messages.extend([
                    f"💭 {monster_name} assesses the situation...",
                    f"💭 {monster_name} plans its next move...",
                    f"💭 {monster_name} studies your stance..."
                ])
            else:
                thinking_messages.extend([
                    f"💭 {monster_name} eyes you confidently...",
                    f"💭 {monster_name} prepares to strike...",
                    f"💭 {monster_name} looks for an opening..."
                ])
            
            # Player health-based reactions
            if player_hp_percent < 30:
                thinking_messages.extend([
                    f"💭 {monster_name} senses your weakness...",
                    f"💭 {monster_name} moves in for the kill..."
                ])
                thinking_time -= 0.2  # Faster when player is weak
            
            # Select and display thinking message
            if thinking_messages:
                selected_message = random.choice(thinking_messages)
                battle["battle_log"].append(selected_message)
                
                # Add realistic but short delay
                await asyncio.sleep(min(thinking_time, 1.0))  # Cap at 1 second max
                
                # Add action preparation message
                action_prep = [
                    f"⚔️ {monster_name} attacks!",
                    f"⚔️ {monster_name} strikes!",
                    f"⚔️ {monster_name} lunges forward!"
                ]
                battle["battle_log"].append(random.choice(action_prep))
                
        except Exception as e:
            # If thinking phase fails, just continue without it
            print(f"Monster thinking phase error: {e}")
            pass

    def _monster_choose_attack_style(self, monster: Dict, player: Dict, rng) -> str:
        """Monster AI chooses attack style based on battle conditions"""
        monster_hp_percent = (monster.get("current_hp", 0) / max(1, monster.get("hp", 100))) * 100
        player_hp_percent = (player.get("current_hp", 0) / max(1, player.get("hp", 100))) * 100
        
        # Desperate when very low HP
        if monster_hp_percent < 20:
            if rng.random() < 0.7:  # 70% chance
                return "desperate"
        
        # Aggressive when player is weak
        if player_hp_percent < 30:
            if rng.random() < 0.6:  # 60% chance
                return "aggressive"
        
        # Defensive when monster is moderately wounded
        if monster_hp_percent < 50 and monster_hp_percent > 20:
            if rng.random() < 0.4:  # 40% chance
                return "defensive"
        
        # Check status effects
        monster_statuses = monster.get("statuses", [])
        if any(isinstance(s, dict) and s.get("id") in ["burn", "poison"] for s in monster_statuses):
            if rng.random() < 0.5:  # 50% chance to be aggressive when suffering DoT
                return "aggressive"
        
        # Default to normal attack
        base_chance = rng.random()
        if base_chance < 0.15:  # 15% chance
            return "aggressive"
        elif base_chance < 0.25:  # 10% chance
            return "defensive"
        else:
            return "normal"  # 75% chance

    async def _player_attack(self, battle_id: str) -> Dict:
        battle = self.active_battles[battle_id]
        player = battle["player"]
        monster = battle["monster"]
        rng = Random(battle["seed"] + battle["turn"])  # per-turn deterministic

        # Apply status effect modifiers
        player_stats = self._apply_status_modifiers(player)
        monster_stats = self._apply_status_modifiers(monster)

        kind, mult, p_hit = hit_roll(rng, player_stats["accuracy"], monster_stats["evasion"])
        log_bits = [f"🎯 {kind.upper()} (p={p_hit:.2f})"]
        damage = 0
        crit = False
        if kind != "miss":
            base = phys_damage(rng, power=100.0, atk=player_stats["attack"], defense=monster_stats["defense"], pen=player.get("pen", 0))
            crit = crit_roll(rng, player.get("crit_base", 0.05), player.get("luck", 5))
            if crit:
                base = int(round(base * player.get("crit_dmg", 1.5)))
            damage = int(round(base * mult))
        # Apply shields
        if monster.get("shield", 0) > 0 and damage > 0:
            absorbed = min(monster["shield"], damage)
            monster["shield"] -= absorbed
            damage -= absorbed
            log_bits.append(f"🛡️ {absorbed} absorbed")
        if damage > 0:
            monster["current_hp"] = max(0, monster["current_hp"] - damage)
        # SP regen on action
        player["current_sp"] = min(player["sp"], player.get("current_sp", 0) + 20)
        # Log
        line = f"⚔️ {player['name']} → {monster['name']}: {damage} dmg" + (" (CRIT)" if crit else "") + f" | {'; '.join(log_bits)}"
        battle["battle_log"].append(line)

        if monster["current_hp"] <= 0:
            return await self._end_battle(battle_id, "player")

        return await self._end_player_turn_and_counter(battle_id)

    async def _player_defend(self, battle_id: str) -> Dict:
        battle = self.active_battles[battle_id]
        player = battle["player"]
        # Defend grants guard points (GP) scaled by defense and some SP
        shield_gain = max(5, int(player.get("defense", 5) * 0.6))
        player["shield"] = player.get("shield", 0) + shield_gain
        player["current_sp"] = min(player["sp"], player.get("current_sp", 0) + 15)
        battle["battle_log"].append(f"🛡️ {player['name']} Defend: +{shield_gain} GP, +15 SP")
        return await self._end_player_turn_and_counter(battle_id, defend=True)

    async def _player_flee(self, battle_id: str) -> Dict:
        battle = self.active_battles[battle_id]
        player = battle["player"]
        user_id = battle["user_id"]
        
        if random.random() < 0.7:
            # Successful flee - apply penalties
            gold_penalty = max(1, player.get("gold", 0) // 20)  # Lose 5% gold
            hp_penalty = max(1, player.get("current_hp", 0) // 4)  # Lose 25% current HP
            
            # Apply penalties to character data
            character = await self.db.get_player(user_id)
            if character:
                character["gold"] = max(0, character.get("gold", 0) - gold_penalty)
                character["hp"] = max(1, player.get("current_hp", 0) - hp_penalty)
                await self.db.save_player(user_id, character)
            
            battle["battle_log"].append(f"🏃 You fled successfully! Lost {gold_penalty} gold and {hp_penalty} HP as penalty!")
            return await self._end_battle(battle_id, "fled")
        else:
            battle["battle_log"].append("🏃 Failed to flee! Monster gets a free attack!")
            return await self._monster_attack(battle_id)

    async def _player_skill(self, battle_id: str, skill_id: str) -> Dict:
        """Player uses a skill in battle"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {"success": False, "message": "Battle not found"}
        
        player = battle["player"]
        monster = battle["monster"]
        
        # Get skill info
        skill_info = await self.character_system.get_skill_info(skill_id)
        if not skill_info:
            return {"success": False, "message": "Skill not found"}
        
        # Check SP cost
        sp_cost = skill_info.get("sp_cost", 0)
        if player["sp"] < sp_cost:
            return {"success": False, "message": f"Not enough SP! Need {sp_cost}, have {player['sp']}"}
        
        # Consume SP from both battle and character
        player["sp"] -= sp_cost
        
        # Update character stats in database
        if self.character_system:
            await self.character_system.restore_sp(battle["user_id"], -sp_cost)  # Negative to consume
        
        # Calculate skill damage
        base_damage = skill_info.get("power", 20)
        skill_multiplier = skill_info.get("multiplier", 1.5)
        
        # Apply intelligence bonus for magic skills
        if skill_info.get("type") == "magic":
            int_bonus = player.get("intelligence", 5) * 0.1
            skill_multiplier += int_bonus
        
        # Calculate final damage
        damage = int(base_damage * skill_multiplier)
        
        # Apply accuracy check
        accuracy = player.get("accuracy", 60)
        if random.randint(1, 100) > accuracy:
            return {"success": False, "message": "Skill missed!"}
        
        # Apply critical hit
        crit_chance = player.get("luck", 5) * 0.5
        is_crit = random.randint(1, 100) <= crit_chance
        if is_crit:
            damage = int(damage * 2)
            battle["battle_log"].append(f"🎯 **Critical Hit!** {player['name']} uses {skill_id} for {damage} damage!")
        else:
            battle["battle_log"].append(f"⚡ {player['name']} uses {skill_id} for {damage} damage!")
        
        # Apply damage to monster
        monster["current_hp"] = max(0, monster["current_hp"] - damage)
        
        # Apply skill effects
        effects = skill_info.get("effects", [])
        for effect in effects:
            if effect in self.status_effects:
                monster["statuses"] = monster.get("statuses", [])
                monster["statuses"].append({
                    "id": effect,
                    "status": effect,
                    "duration": 3,
                    "applied_by": player["name"]
                })
                battle["battle_log"].append(f"💫 {monster['name']} is affected by {self.status_effects[effect]['name']}!")
        
        # Check if monster is defeated
        if monster["current_hp"] <= 0:
            battle["status"] = "player_won"
            battle["battle_log"].append(f"💀 {monster['name']} has been defeated!")
            return {"success": True, "message": "Monster defeated!", "battle_ended": True}
        
        # Update battle state
        battle["turn"] += 1 # Increment turn
        battle["last_action"] = f"skill_{skill_id}"
        
        return {
            "success": True,
            "message": f"Skill {skill_id} used successfully!",
            "damage_dealt": damage,
            "sp_consumed": sp_cost,
            "is_critical": is_crit
        }

    async def _player_use_item(self, battle_id: str, item_id: str) -> Dict:
        """Player uses an item in battle"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {"success": False, "message": "Battle not found"}
        
        player = battle["player"]
        
        # Use item through inventory system
        if not self.inventory_system:
            return {"success": False, "message": "Inventory system unavailable"}
        
        result = await self.inventory_system.use_item(battle["user_id"], item_id, 1)
        if not result["success"]:
            return result
        
        # Apply item effects to battle state
        effects = result.get("effects", {})
        
        # Update player stats in battle based on item effects
        if "hp_healed" in effects:
            heal_amount = effects["hp_healed"]
            old_hp = player["current_hp"]
            player["current_hp"] = min(player["hp"], player["current_hp"] + heal_amount)
            battle["battle_log"].append(f"🧪 {player['name']} uses {result['item_name']} and heals {heal_amount} HP")
        
        if "sp_restored" in effects:
            sp_amount = effects["sp_restored"]
            old_sp = player["current_sp"]
            player["current_sp"] = min(player["sp"], player["current_sp"] + sp_amount)
            battle["battle_log"].append(f"🔷 Restored {sp_amount} SP")
        
        # Apply stat boosts
        for stat, boost in effects.items():
            if stat.endswith("_boost") and stat[:-5] in player:
                stat_name = stat[:-5]
                player[stat_name] += boost
                battle["battle_log"].append(f"⚡ {stat_name.title()} increased by {boost}")
        
        return await self._end_player_turn_and_counter(battle_id, item_used=True)
            
    async def _monster_attack(self, battle_id: str) -> Dict:
        battle = self.active_battles[battle_id]
        player = battle["player"]
        monster = battle["monster"]
        rng = Random(battle["seed"] + battle["turn"] + 999)

        # Add thinking delay and behavior
        await self._monster_thinking_phase_safe(battle, monster, player)

        # Check if monster is stunned
        for status in monster.get("statuses", []):
            if isinstance(status, dict):
                status_id = status.get("id", status.get("status"))
                if status_id in self.status_effects:
                    effect_def = self.status_effects[status_id]
                    if effect_def.get("stun", False):
                        battle["battle_log"].append(f"⚡ {monster['name']} is stunned and cannot act!")
                        return {"success": True, "battle": battle}

        # Apply status effect modifiers
        player_stats = self._apply_status_modifiers(player)
        monster_stats = self._apply_status_modifiers(monster)

        # Monster AI decision making
        attack_style = self._monster_choose_attack_style(monster, player, rng)
        
        # Apply attack style modifiers
        accuracy_mod = monster_stats["accuracy"]
        power_mod = 100.0
        
        if attack_style == "aggressive":
            power_mod = 130.0  # +30% damage
            accuracy_mod = int(accuracy_mod * 0.8)  # -20% accuracy
            battle["battle_log"].append(f"💢 {monster['name']} attacks aggressively!")
        elif attack_style == "defensive":
            power_mod = 70.0   # -30% damage
            accuracy_mod = int(accuracy_mod * 1.2)  # +20% accuracy
            battle["battle_log"].append(f"🛡️ {monster['name']} attacks carefully!")
        elif attack_style == "desperate":
            power_mod = 150.0  # +50% damage
            accuracy_mod = int(accuracy_mod * 0.6)  # -40% accuracy
            battle["battle_log"].append(f"😤 {monster['name']} attacks desperately!")

        kind, mult, p_hit = hit_roll(rng, accuracy_mod, player_stats["evasion"])
        log_bits = [f"🎯 {kind.upper()} (p={p_hit:.2f})"]
        monster_damage = 0
        crit = False
        if kind != "miss":
            base = phys_damage(rng, power=power_mod, atk=monster_stats["attack"], defense=player_stats["defense"], pen=0)
            crit = crit_roll(rng, 0.05, monster.get("level", 1))
            if crit:
                base = int(round(base * 1.5))
            monster_damage = int(round(base * mult))
        # Shields absorb first
        if player.get("shield", 0) > 0:
            absorbed = min(player["shield"], monster_damage)
            player["shield"] -= absorbed
            monster_damage -= absorbed
            log_bits.append(f"🛡️ {absorbed} absorbed")
        if monster_damage > 0:
            player["current_hp"] = max(0, player["current_hp"] - monster_damage)
        battle["battle_log"].append(f"👹 {monster['name']} → {player['name']}: {monster_damage} dmg" + (" (CRIT)" if crit else "") + f" | {'; '.join(log_bits)}")

        if player["current_hp"] <= 0:
            return await self._end_battle(battle_id, "monster")

        return {"success": True, "battle": battle}

    async def _end_player_turn_and_counter(self, battle_id: str, defend: bool = False, item_used: bool = False, ultimate_used: bool = False) -> Dict:
        """Handle end of player's turn: tick statuses/cooldowns, monster counter, advance turn."""
        battle = self.active_battles[battle_id]
        # Tick cooldowns
        for skill_id in list(battle["cooldowns"].keys()):
            if battle["cooldowns"][skill_id] > 0:
                battle["cooldowns"][skill_id] -= 1
        # Tick statuses (DoT/HoT)
        await self._tick_statuses(battle)
        # Monster counter (reduced if defend applied)
        if defend:
            # On defend, monster deals half damage implicitly via shield; still attempt attack for feedback
            res = await self._monster_attack(battle_id)
        else:
            res = await self._monster_attack(battle_id)
        battle["turn"] += 1
        return res

    async def _tick_statuses(self, battle: Dict):
        """Enhanced status effect processing with proper effects"""
        for side in ("player", "monster"):
            entity = battle[side]
            new_statuses = []
            total_dot = 0
            total_hot = 0
            status_messages = []
            
            for status in entity.get("statuses", []):
                if isinstance(status, dict):
                    status_id = status.get("id", status.get("status", "unknown"))
                    duration = status.get("duration", 0)
                    
                    # Get status effect definition
                    effect_def = self.status_effects.get(status_id, {})
                    
                    # Apply damage over time
                    if effect_def.get("dot", 0):
                        dot_damage = effect_def["dot"]
                        total_dot += dot_damage
                        
                    # Apply healing over time
                    if effect_def.get("hot", 0):
                        hot_heal = effect_def["hot"]
                        total_hot += hot_heal
                    
                    # Decrease duration
                    status["duration"] = max(0, duration - 1)
                    
                    # Keep status if still active
                    if status["duration"] > 0:
                        new_statuses.append(status)
                    else:
                        # Status expired
                        status_name = effect_def.get("name", status_id)
                        status_messages.append(f"{status_name} wore off {entity['name']}")
                
                # Handle legacy status format
                elif isinstance(status, str):
                    # This is for backward compatibility - convert to new format
                    pass
            
            # Update statuses
            entity["statuses"] = new_statuses
            
            # Apply damage over time
            if total_dot > 0:
                # Apply to shield first
                if entity.get("shield", 0) > 0:
                    absorbed = min(entity["shield"], total_dot)
                    entity["shield"] -= absorbed
                    total_dot -= absorbed
                
                # Apply remaining damage to HP
                if total_dot > 0:
                    entity["current_hp"] = max(0, entity["current_hp"] - total_dot)
                    status_messages.append(f"🔥 {entity['name']} takes {total_dot} damage from status effects!")
            
            # Apply healing over time
            if total_hot > 0:
                old_hp = entity["current_hp"]
                max_hp = entity.get("hp", entity.get("max_hp", 100))
                entity["current_hp"] = min(max_hp, entity["current_hp"] + total_hot)
                actual_heal = entity["current_hp"] - old_hp
                if actual_heal > 0:
                    status_messages.append(f"💚 {entity['name']} heals {actual_heal} HP from regeneration!")
            
            # Add status messages to battle log
            if status_messages:
                if "battle_log" not in battle:
                    battle["battle_log"] = []
                battle["battle_log"].extend(status_messages)
 
    async def _end_battle(self, battle_id: str, winner: str) -> Dict:
        battle = self.active_battles[battle_id]
        battle["status"] = "completed"
        battle["battle_ended"] = True
        battle["winner"] = winner
        battle["end_time"] = datetime.utcnow().isoformat()

        # Rewards on victory
        if winner == "player":
            xp_reward = battle["monster"].get("xp_reward", 10)
            gold_reward = battle["monster"].get("gold_reward", 5)
            battle["rewards"] = {"xp": xp_reward, "gold": gold_reward}
            battle["battle_log"].append(
                f"🎉 Victory! +{xp_reward} XP, +{gold_reward} Gold"
            )

            # Persist rewards
            from systems.character import CharacterSystem
            char_system = self.character_system or CharacterSystem(self.db)
            await char_system.add_xp(battle["user_id"], xp_reward)
            await char_system.add_gold(battle["user_id"], gold_reward)
            # Companion hunting: small chance to bring an extra item
            try:
                character = await self.db.get_player(battle["user_id"]) or {}
                comp = character.get("companion") or {}
                hunt_pts = int((comp.get("skills") or {}).get("hunting", 0))
                if hunt_pts > 0 and random.random() < min(0.35, 0.05 * hunt_pts):
                    items_map = await self.db.load_items()
                    if items_map:
                        import random as _r
                        iid = _r.choice(list(items_map.keys()))
                        from systems.inventory import InventorySystem
                        inv = self.inventory_system or InventorySystem(self.db)
                        await inv.add_item(battle["user_id"], iid, 1)
                        battle["battle_log"].append(f"🦮 Companion found extra loot: {items_map.get(iid, {}).get('name', iid)}")
            except Exception:
                pass

        elif winner == "monster":
            battle["battle_log"].append("💀 Defeat! Better luck next time.")

        elif winner == "fled":
            battle["battle_log"].append("🏃 You escaped the battle.")

        return {"success": True, "battle": battle}
 
    async def cleanup_battle(self, battle_id: str) -> None:
        """Remove a completed battle from active battles."""
        if battle_id in self.active_battles:
            del self.active_battles[battle_id]
 
    def get_battle_embed(self, battle: Dict) -> Dict:
        """Return a structure suitable for create_embed() showing battle status."""
        player = battle["player"]
        monster = battle["monster"]
        description_lines = battle["battle_log"][-6:]
        player_status = ", ".join([s.get("name", "") for s in player.get("statuses", [])]) or "None"
        monster_status = ", ".join([s.get("name", "") for s in monster.get("statuses", [])]) or "None"
        return {
            "title": f"⚔️ {player['name']} vs {monster['name']}",
            "description": "\n".join(description_lines),
            "color": None,
            "fields": [
                {"name": "Player", "value": f"HP: {player['current_hp']}/{player['hp']} | SP: {player['current_sp']}/{player['sp']}\nShield: {player.get('shield',0)}\nATK/DEF: {player['attack']}/{player['defense']}\nACC/EVA: {player.get('accuracy',60)}/{player.get('evasion',20)}\nStatuses: {player_status}", "inline": True},
                {"name": "Monster", "value": f"HP: {monster['current_hp']}/{monster['hp']}\nShield: {monster.get('shield',0)}\nATK/DEF: {monster['attack']}/{monster['defense']}\nACC/EVA: {monster.get('accuracy',50)}/{monster.get('evasion',10)}\nStatuses: {monster_status}", "inline": True},
            ],
            "footer": f"Turn {battle['turn']} • Battle ID: {battle['battle_id']}"
        }
 
    async def is_in_battle(self, user_id: int) -> bool:
        """Check if a user is currently in battle."""
        for battle in self.active_battles.values():
            if battle["user_id"] == user_id and battle["status"] == "active":
                return True
        return False

    async def use_item_in_battle(self, battle_id: str, user_id: int, item_id: str) -> Dict:
        """Use an item during battle with proper stat updates"""
        try:
            battle = self.active_battles.get(battle_id)
            if not battle:
                return {"success": False, "message": "Battle not found"}
            
            if battle["user_id"] != user_id:
                return {"success": False, "message": "Not your battle"}
            
            if battle["status"] != "active":
                return {"success": False, "message": "Battle is not active"}
            
            player = battle["player"]
            
            # Get item data
            item = await self.db.get_item(item_id)
            if not item:
                return {"success": False, "message": "Item not found"}
            
            # Check if item is usable
            if item.get("type") not in ["consumable", "potion", "scroll", "artifact"]:
                return {"success": False, "message": f"{item['name']} cannot be used in battle"}
            
            # Use item through inventory system
            if self.inventory_system:
                result = await self.inventory_system.use_item(user_id, item.get("name", item_id))
                if not result["success"]:
                    return result
                
                # Apply item effects to battle state
                effects_applied = result.get("effects_applied", [])
                
                # Update player stats in battle based on item effects
                if "heal_amount" in item:
                    heal_amount = item["heal_amount"]
                    old_hp = player["current_hp"]
                    player["current_hp"] = min(player["hp"], player["current_hp"] + heal_amount)
                    actual_heal = player["current_hp"] - old_hp
                    if actual_heal > 0:
                        effects_applied.append(f"Restored {actual_heal} HP")
                
                if "sp_amount" in item:
                    sp_amount = item["sp_amount"]
                    old_sp = player["current_sp"]
                    player["current_sp"] = min(player["sp"], player["current_sp"] + sp_amount)
                    actual_sp = player["current_sp"] - old_sp
                    if actual_sp > 0:
                        effects_applied.append(f"Restored {actual_sp} SP")
            
                if "shield" in item:
                    shield_amount = item["shield"]
                    player["shield"] = player.get("shield", 0) + shield_amount
                    effects_applied.append(f"Gained {shield_amount} shield")
                
                # Apply stat buffs
                stat_buffs = item.get("stat_buffs", {})
                for stat, buff in stat_buffs.items():
                    if stat in player:
                        if isinstance(buff, dict):
                            if "percent" in buff:
                                increase = int(player[stat] * (buff["percent"] / 100))
                                player[stat] += increase
                                effects_applied.append(f"+{increase} {stat.title()} ({buff['percent']}%)")
                            elif "flat" in buff:
                                player[stat] += buff["flat"]
                                effects_applied.append(f"+{buff['flat']} {stat.title()}")
                        else:
                            player[stat] += buff
                            effects_applied.append(f"+{buff} {stat.title()}")
                
                # Create effect message
                effect_message = f"🧪 {player['name']} used {item['name']}!"
                if effects_applied:
                    effect_message += f" {' | '.join(effects_applied)}"
            
            # Add to battle log
            if "battle_log" not in battle:
                battle["battle_log"] = []
            battle["battle_log"].append(effect_message)
            
            # End player turn and let monster act
            await self._end_player_turn_and_counter(battle_id, item_used=True)
            
            return {
                "success": True, 
                "message": effect_message,
                "battle": battle
            }
            
        except Exception as e:
            logger.error(f"Error using item in battle: {e}")
            return {"success": False, "message": "Failed to use item"}

    async def use_skill(self, battle_id: str, user_id: int, skill_id: str) -> Dict:
        """Use a skill during battle with proper SP consumption and stat updates"""
        try:
            battle = self.active_battles.get(battle_id)
            if not battle:
                return {"success": False, "message": "Battle not found"}
            
            if battle["user_id"] != user_id:
                return {"success": False, "message": "Not your battle"}
            
            if battle["status"] != "active":
                return {"success": False, "message": "Battle is not active"}
            
            player = battle["player"]
            
            # Check if player has the skill
            if skill_id not in player.get("skills", []):
                return {"success": False, "message": "You don't know this skill"}
            
            # Get skill data
            skills_data = await self.db.load_json_data("skills.json")
            if skill_id not in skills_data:
                return {"success": False, "message": "Skill not found"}
            
            skill = skills_data[skill_id]
            
            # Check SP cost
            sp_cost = skill.get("sp_cost", 0)
            if player["current_sp"] < sp_cost:
                return {"success": False, "message": f"Not enough SP! Need {sp_cost}, have {player['current_sp']}"}
            
            # Check cooldown (if implemented)
            try:
                character = await self.db.load_player_data(user_id)
                skill_cooldowns = character.get("skill_cooldowns", {})
                if skill_cooldowns.get(skill_id, 0) > 0:
                    return {"success": False, "message": f"Skill on cooldown for {skill_cooldowns[skill_id]} more turns"}
            except:
                # If character loading fails, skip cooldown check
                pass
            
            # Use SP and update character
            player["current_sp"] -= sp_cost
            
            # Update character SP in database
            if self.character_system:
                await self.character_system.restore_sp(user_id, -sp_cost)  # Negative to reduce SP
            
            # Apply skill effects
            monster = battle["monster"]
            effect = skill.get("effect", {})
            
            damage_multiplier = effect.get("damage", 1.0)
            base_damage = int(player["attack"] * damage_multiplier)
            
            # Apply damage
            if damage_multiplier > 0:
                # Calculate damage with resistances
                final_damage = max(1, base_damage - monster.get("defense", 0))
                
                # Apply to shield first
                shield = monster.get("shield", 0)
                if shield > 0:
                    shield_damage = min(shield, final_damage)
                    monster["shield"] = shield - shield_damage
                    final_damage -= shield_damage
                
                # Apply remaining damage to HP
                monster["current_hp"] = max(0, monster["current_hp"] - final_damage)
                
                effect_message = f"{player['name']} used {skill['name']} for {final_damage} damage!"
            else:
                effect_message = f"{player['name']} used {skill['name']}!"
            
            # Apply status effects
            if "apply" in effect:
                for status_effect in effect["apply"]:
                    status_id = status_effect.get("status")
                    duration = status_effect.get("duration", 3)
                    if status_id and status_id in self.status_effects:
                        # Determine target based on status type
                        status_def = self.status_effects[status_id]
                        is_buff = status_def.get("type") == "buff"
                        target = player if is_buff else monster
                        target_name = player['name'] if is_buff else monster['name']
                        
                        # Initialize statuses list if needed
                        if "statuses" not in target:
                            target["statuses"] = []
                        
                        # Create new status effect
                        new_status = {
                            "id": status_id,
                            "status": status_id,  # for backward compatibility
                            "duration": duration,
                            "applied_by": skill['name']
                        }
                        
                        # Check if status already exists and update duration
                        existing_status = None
                        for i, existing in enumerate(target["statuses"]):
                            if isinstance(existing, dict) and existing.get("id") == status_id:
                                existing_status = i
                                break
                        
                        if existing_status is not None:
                            # Update existing status duration
                            target["statuses"][existing_status]["duration"] = max(
                                target["statuses"][existing_status]["duration"], duration
                            )
                        else:
                            # Add new status
                            target["statuses"].append(new_status)
                        
                        effect_message += f" Applied {status_id} to {target_name}!"
            
            # Update cooldowns in character data
            try:
                character = await self.db.load_player_data(user_id)
                if "skill_cooldowns" not in character:
                    character["skill_cooldowns"] = {}
                character["skill_cooldowns"][skill_id] = skill.get("cooldown", 1)
                await self.db.save_player(user_id, character)
            except:
                # If character loading fails, skip cooldown update
                pass
            
            # Add to battle log
            if "battle_log" not in battle:
                battle["battle_log"] = []
            battle["battle_log"].append(effect_message)
            
            # Check if monster is defeated
            if monster["current_hp"] <= 0:
                await self._end_battle(battle_id, "victory")
            else:
                # End player turn and let monster act
                await self._end_player_turn_and_counter(battle_id)
            
            return {
                "success": True,
                "message": effect_message,
                "battle": battle
            }
            
        except Exception as e:
            logger.error(f"Error using skill: {e}")
            return {"success": False, "message": "Failed to use skill"}

    async def _player_ultimate(self, battle_id: str) -> Dict:
        """Player uses ultimate ability"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {"success": False, "message": "Battle not found"}
        
        player = battle["player"]
        monster = battle["monster"]
        
        # Check if ultimate is ready (has enough SP)
        sp_cost = 100  # Ultimate costs 100% of SP
        if player["current_sp"] < sp_cost:
            return {"success": False, "message": f"Not enough SP! Need {sp_cost}, have {player['current_sp']}"}
        
        # Get ultimate info
        ultimate_info = await self.character_system.get_ultimate_info(battle["user_id"])
        if not ultimate_info:
            return {"success": False, "message": "No ultimate ability available"}
        
        # Use SP
        player["current_sp"] = 0  # Ultimate consumes all SP
        
        # Calculate ultimate damage
        base_damage = player["attack"] * 3  # 3x attack power
        crit_chance = player.get("luck", 0) / 100  # Luck affects crit chance
        
        if random.random() < crit_chance:
            damage = int(base_damage * 1.5)
            battle["battle_log"].append(f"💥 {player['name']} uses ULTIMATE! CRITICAL HIT! {damage} damage!")
        else:
            damage = base_damage
            battle["battle_log"].append(f"💥 {player['name']} uses ULTIMATE! {damage} damage!")
        
        # Apply damage to monster
        monster["current_hp"] = max(0, monster["current_hp"] - damage)
        
        # Check if monster is defeated
        if monster["current_hp"] <= 0:
            battle["battle_log"].append(f"💀 {monster['name']} has been defeated!")
            return await self._end_battle(battle_id, True)
        
        # Update character SP in database
        if self.character_system:
            await self.character_system.restore_sp(battle["user_id"], 0)  # Set SP to 0
        
        return await self._end_player_turn_and_counter(battle_id, ultimate_used=True)
