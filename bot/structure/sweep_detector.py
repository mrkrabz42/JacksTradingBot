"""Module 3: Sweep Detector — detects liquidity sweeps vs genuine breaks."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from bot.structure.config import SweepConfig
from bot.structure.liquidity_map import LiquidityPool


class SweepEvent(TypedDict, total=False):
    pool: LiquidityPool
    sweep_type: str          # "liquidity_sweep" or "genuine_break"
    direction: str           # "bullish_sweep", "bearish_sweep", "bullish_break", "bearish_break"
    penetration_ticks: float
    penetration_atr: float
    candle_time: str
    candle_close: float
    sweep_quality: int       # 0-100


def calculate_sweep_quality(
    penetration: float,
    atr: float,
    pool_strength: str,
    candle: Dict[str, Any],
) -> int:
    """Score the sweep's quality 0-100.

    Factors:
    - Penetration depth (40%): ideal is 0.1-0.5 ATR (brief spike)
    - Pool strength (35%): triple > double > session > round
    - Wick-to-body ratio (25%): high wick ratio = clean sweep candle
    """
    # Penetration depth score
    pen_ratio = penetration / atr if atr > 0 else 0
    if 0 < pen_ratio <= 0.5:
        pen_score = 90
    elif pen_ratio <= 1.0:
        pen_score = 60
    else:
        pen_score = 30  # Too deep — may not be a sweep

    # Pool strength score
    strength_map = {"triple": 100, "double": 70, "session": 60, "round": 50}
    strength_score = strength_map.get(pool_strength, 40)

    # Wick-to-body ratio (high ratio = sweep, low ratio = break)
    body = abs(candle["close"] - candle["open"])
    total_range = candle["high"] - candle["low"]
    wick_ratio = 1 - (body / total_range) if total_range > 0 else 0
    wick_score = min(wick_ratio / 0.6, 1.0) * 100  # 60%+ wick = perfect sweep candle

    return round(pen_score * 0.40 + strength_score * 0.35 + wick_score * 0.25)


def detect_sweeps(
    candle: Dict[str, Any],
    liquidity_pools: List[LiquidityPool],
    atr: float,
    config: Optional[SweepConfig] = None,
) -> List[SweepEvent]:
    """Check if the current candle swept any nearby liquidity pool.

    A *liquidity sweep* occurs when price wicks through a pool but the body
    closes back inside — stop-hunt complete, expect reversal.

    A *genuine break* occurs when the body closes beyond the pool — structure
    break, may lead to MSS.
    """
    if config is None:
        config = SweepConfig()
    sweep_events: List[SweepEvent] = []

    for pool in liquidity_pools:
        if pool["type"] == "BSL":  # Buy-side liquidity (above price)
            pierced = candle["high"] > pool["price"]
            body_closed_back = candle["close"] < pool["price"]
            penetration = candle["high"] - pool["price"] if pierced else 0

            if pierced and body_closed_back:
                quality = calculate_sweep_quality(
                    penetration, atr, pool.get("strength", ""), candle
                )
                if quality >= config.min_quality:
                    sweep_events.append({
                        "pool": pool,
                        "sweep_type": "liquidity_sweep",
                        "direction": "bearish_sweep",  # swept BSL = bearish intent
                        "penetration_ticks": round(penetration, 4),
                        "penetration_atr": round(penetration / atr, 4) if atr > 0 else 0,
                        "candle_time": str(candle.get("time", "")),
                        "candle_close": float(candle["close"]),
                        "sweep_quality": quality,
                    })
            elif pierced and not body_closed_back:
                sweep_events.append({
                    "pool": pool,
                    "sweep_type": "genuine_break",
                    "direction": "bullish_break",
                    "penetration_ticks": round(penetration, 4),
                    "candle_time": str(candle.get("time", "")),
                })

        elif pool["type"] == "SSL":  # Sell-side liquidity (below price)
            pierced = candle["low"] < pool["price"]
            body_closed_back = candle["close"] > pool["price"]
            penetration = pool["price"] - candle["low"] if pierced else 0

            if pierced and body_closed_back:
                quality = calculate_sweep_quality(
                    penetration, atr, pool.get("strength", ""), candle
                )
                if quality >= config.min_quality:
                    sweep_events.append({
                        "pool": pool,
                        "sweep_type": "liquidity_sweep",
                        "direction": "bullish_sweep",  # swept SSL = bullish intent
                        "penetration_ticks": round(penetration, 4),
                        "penetration_atr": round(penetration / atr, 4) if atr > 0 else 0,
                        "candle_time": str(candle.get("time", "")),
                        "candle_close": float(candle["close"]),
                        "sweep_quality": quality,
                    })
            elif pierced and not body_closed_back:
                sweep_events.append({
                    "pool": pool,
                    "sweep_type": "genuine_break",
                    "direction": "bearish_break",
                    "penetration_ticks": round(penetration, 4),
                    "candle_time": str(candle.get("time", "")),
                })

    return sweep_events
