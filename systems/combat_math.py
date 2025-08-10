from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Tuple


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def hit_roll(rng: Random, acc: int, eva: int, graze_window: float = 0.1) -> Tuple[str, float, float]:
    """Return (result, damage_mult, p_hit) with result in {hit, graze, miss}."""
    p_hit = clamp(acc / (acc + max(1, eva)), 0.05, 0.95)
    roll = rng.random()
    if roll <= p_hit * (1 - graze_window):
        return ("hit", 1.0, p_hit)
    elif roll <= p_hit:
        return ("graze", 0.6, p_hit)
    return ("miss", 0.0, p_hit)


def crit_roll(rng: Random, base: float, luck: int, cL: float = 0.002, cap: float = 0.75) -> bool:
    return rng.random() < clamp(base + luck * cL, 0.0, cap)


def phys_damage(
    rng: Random,
    power: float,
    atk: int,
    defense: int,
    pen: int,
    alpha: float = 1.2,
    variance: float = 0.05,
) -> int:
    eff_def = max(0, defense - max(0, pen))
    scale = (atk / (atk + max(1, eff_def))) ** alpha
    base = power * scale
    var = rng.uniform(1.0 - variance, 1.0 + variance)
    return max(1, int(round(base * var)))


def mag_damage(
    rng: Random,
    power: float,
    intelligence: int,
    resistance: int,
    pen: int,
    alpha: float = 1.2,
    variance: float = 0.05,
) -> int:
    eff_res = max(0, resistance - max(0, pen))
    scale = (intelligence / (intelligence + max(1, eff_res))) ** alpha
    base = power * scale
    var = rng.uniform(1.0 - variance, 1.0 + variance)
    return max(1, int(round(base * var)))
