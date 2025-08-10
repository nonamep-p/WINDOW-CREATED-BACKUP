from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

DamageType = Literal["physical", "magical", "true"]
TargetType = Literal["self", "ally", "enemy", "all_enemies", "all_allies"]

@dataclass
class StatusEffect:
    id: str
    name: str
    description: str
    duration: int
    stacks: int = 1
    # Modifiers applied while active (additive)
    stat_mods: Dict[str, int] = field(default_factory=dict)
    # Periodic effects
    dot: int = 0  # damage over time per tick
    hot: int = 0  # heal over time per tick
    shield: int = 0  # flat shield value, depletes before HP
    # Special flags
    stunned: bool = False
    stealth: bool = False

@dataclass
class Skill:
    id: str
    name: str
    description: str
    sp_cost: int
    cooldown: int
    damage_multiplier: float = 1.0
    damage_type: DamageType = "physical"
    target: TargetType = "enemy"
    # Optional status to apply to target/self
    apply_status_to_target: Optional[StatusEffect] = None
    apply_status_to_self: Optional[StatusEffect] = None
    # Healing
    heal_percent_of_max: float = 0.0

@dataclass
class CombatEntity:
    name: str
    base: Dict[str, int]  # hp, sp, attack, defense, speed, intelligence, luck, agility
    current_hp: int
    current_sp: int
    shield: int = 0
    statuses: List[StatusEffect] = field(default_factory=list)

    def is_alive(self) -> bool:
        return self.current_hp > 0

@dataclass
class BattleState:
    battle_id: str
    user_id: int
    turn: int
    player: CombatEntity
    monster: CombatEntity
    battle_log: List[str] = field(default_factory=list)
    status: Literal["active", "completed"] = "active"
    winner: Optional[Literal["player", "monster", "fled"]] = None
    rewards: Dict[str, int] = field(default_factory=lambda: {"xp": 0, "gold": 0})
    cooldowns: Dict[str, int] = field(default_factory=dict)  # skill_id -> remaining turns
