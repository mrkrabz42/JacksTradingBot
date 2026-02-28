"""Module 2: Liquidity Map — identifies and maintains liquidity pools."""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

from bot.structure.config import LiquidityConfig
from bot.structure.swing_engine import Swing


class LiquidityPool(TypedDict, total=False):
    type: str               # "BSL" (buy-side) or "SSL" (sell-side)
    subtype: str            # "equal_highs", "equal_lows", "round_number", "PDH", "PDL", "PWH", "PWL"
    price: float
    touches: int
    strength: str           # "triple", "double", "session", "round"
    first_time: str
    last_time: str
    sweep_probability: float
    distance_pct: float


def find_equal_levels(
    swings: List[Swing],
    level_type: str = "high",
    config: Optional[LiquidityConfig] = None,
) -> List[LiquidityPool]:
    """Detect equal highs or equal lows — key liquidity pools.

    Clusters swing points whose prices fall within tolerance_pct of each other.
    Triple+ clusters have ~85% sweep probability; doubles ~71%.
    """
    if config is None:
        config = LiquidityConfig()
    tolerance = config.equal_level_tolerance_pct

    filtered = [s for s in swings if s["type"] == level_type]
    pools: List[LiquidityPool] = []
    used: set[int] = set()

    for i, s1 in enumerate(filtered):
        if i in used:
            continue
        cluster = [s1]
        for j, s2 in enumerate(filtered):
            if j <= i or j in used:
                continue
            if abs(s1["price"] - s2["price"]) / s1["price"] <= tolerance:
                cluster.append(s2)
                used.add(j)

        if len(cluster) >= 2:
            used.add(i)
            avg_price = sum(s["price"] for s in cluster) / len(cluster)
            pool_type = "BSL" if level_type == "high" else "SSL"

            pools.append({
                "type": pool_type,
                "subtype": f"equal_{level_type}s",
                "price": round(avg_price, 4),
                "touches": len(cluster),
                "strength": "triple" if len(cluster) >= 3 else "double",
                "first_time": cluster[0]["time"],
                "last_time": cluster[-1]["time"],
                "sweep_probability": 0.85 if len(cluster) >= 3 else 0.71,
            })

    return pools


def find_round_number_pools(
    current_price: float,
    config: Optional[LiquidityConfig] = None,
) -> List[LiquidityPool]:
    """Mark nearby round numbers as potential liquidity levels."""
    if config is None:
        config = LiquidityConfig()
    pools: List[LiquidityPool] = []

    for interval in config.round_number_intervals:
        below = (current_price // interval) * interval
        above = below + interval
        pools.append({
            "type": "SSL",
            "subtype": "round_number",
            "price": below,
            "strength": "round",
            "sweep_probability": 0.66,
        })
        pools.append({
            "type": "BSL",
            "subtype": "round_number",
            "price": above,
            "strength": "round",
            "sweep_probability": 0.66,
        })

    return pools


def find_session_level_pools(
    pdh: float,
    pdl: float,
    pwh: Optional[float] = None,
    pwl: Optional[float] = None,
) -> List[LiquidityPool]:
    """Mark previous day/week highs and lows as liquidity pools."""
    pools: List[LiquidityPool] = [
        {"type": "BSL", "subtype": "PDH", "price": pdh,
         "strength": "session", "sweep_probability": 0.62},
        {"type": "SSL", "subtype": "PDL", "price": pdl,
         "strength": "session", "sweep_probability": 0.62},
    ]
    if pwh is not None:
        pools.append({"type": "BSL", "subtype": "PWH", "price": pwh,
                       "strength": "session", "sweep_probability": 0.65})
    if pwl is not None:
        pools.append({"type": "SSL", "subtype": "PWL", "price": pwl,
                       "strength": "session", "sweep_probability": 0.65})
    return pools


def build_liquidity_map(
    swings: List[Swing],
    current_price: float,
    pdh: float,
    pdl: float,
    pwh: Optional[float] = None,
    pwl: Optional[float] = None,
    config: Optional[LiquidityConfig] = None,
) -> List[LiquidityPool]:
    """Combine all pool types into a single liquidity map sorted by distance."""
    if config is None:
        config = LiquidityConfig()

    pools: List[LiquidityPool] = []
    pools += find_equal_levels(swings, level_type="high", config=config)
    pools += find_equal_levels(swings, level_type="low", config=config)
    pools += find_round_number_pools(current_price, config=config)
    pools += find_session_level_pools(pdh, pdl, pwh, pwl)

    # Annotate with distance from current price
    for p in pools:
        p["distance_pct"] = round(abs(p["price"] - current_price) / current_price * 100, 4)

    return sorted(pools, key=lambda x: x.get("distance_pct", 999))
