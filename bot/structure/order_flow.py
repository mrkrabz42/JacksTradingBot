"""Module 4: Order Flow Scorer — quantifies conviction from OHLCV + volume."""
from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

import numpy as np
import pandas as pd

from bot.structure.config import OrderFlowConfig


class VolumeProfile(TypedDict):
    poc: float   # Point of Control — price level with highest volume
    vah: float   # Value Area High
    val: float   # Value Area Low


def calculate_estimated_delta(candle: Dict[str, Any]) -> float:
    """Estimate volume delta from OHLCV (no Level 2 needed).

    Uses the close position within the bar's range to split volume
    between buyers and sellers. Positive = net buying, negative = net selling.
    """
    total_range = candle["high"] - candle["low"]
    if total_range == 0:
        return 0.0

    # Where did the close fall within the range? (0 = at low, 1 = at high)
    close_position = (candle["close"] - candle["low"]) / total_range

    buy_volume = candle["volume"] * close_position
    sell_volume = candle["volume"] * (1 - close_position)

    return buy_volume - sell_volume


def score_order_flow(
    candle: Dict[str, Any],
    volume_sma_20: float,
    atr_14: float,
    config: Optional[OrderFlowConfig] = None,
) -> int:
    """Score the order flow conviction of a single candle (0-100).

    Components:
    - Relative volume (0-40 pts): how unusual is this bar's volume?
    - Estimated delta alignment (0-30 pts): does delta match candle direction?
    - Body-to-range conviction (0-30 pts): clean body = strong conviction
    """
    if config is None:
        config = OrderFlowConfig()

    # 1. Relative volume (0-40 points)
    rel_vol = candle["volume"] / volume_sma_20 if volume_sma_20 > 0 else 1.0
    vol_score = min(rel_vol / 3.0, 1.0) * 40  # 3x avg volume = max score

    # 2. Estimated delta alignment (0-30 points)
    delta = calculate_estimated_delta(candle)
    is_bullish = candle["close"] > candle["open"]
    delta_aligned = (delta > 0 and is_bullish) or (delta < 0 and not is_bullish)
    delta_magnitude = abs(delta) / candle["volume"] if candle["volume"] > 0 else 0
    delta_score = (30.0 if delta_aligned else 10.0) * min(delta_magnitude / 0.7, 1.0)

    # 3. Body-to-range conviction (0-30 points)
    body = abs(candle["close"] - candle["open"])
    total_range = candle["high"] - candle["low"]
    body_ratio = body / total_range if total_range > 0 else 0
    conviction_score = min(body_ratio / 0.8, 1.0) * 30

    return round(vol_score + delta_score + conviction_score)


def calculate_volume_profile(df: pd.DataFrame, num_bins: int = 50) -> VolumeProfile:
    """Build volume profile from OHLCV data.

    Returns POC (Point of Control), VAH (Value Area High), VAL (Value Area Low).
    The Value Area contains ~70% of total volume.

    df must have columns: high, low, close, volume (lowercase).
    """
    typical_price = (df["high"] + df["low"] + df["close"]) / 3

    price_min = float(df["low"].min())
    price_max = float(df["high"].max())
    bins = np.linspace(price_min, price_max, num_bins + 1)

    price_bin = pd.cut(typical_price, bins=bins, labels=bins[:-1], include_lowest=True)
    vp = df.assign(price_bin=price_bin).groupby("price_bin")["volume"].sum().reset_index()
    vp.columns = ["price", "volume"]
    vp["price"] = pd.to_numeric(vp["price"])

    # POC — price level with most volume
    poc = float(vp.loc[vp["volume"].idxmax(), "price"])

    # Value Area — 70% of total volume
    total_vol = vp["volume"].sum()
    target = total_vol * 0.70
    vp_sorted = vp.sort_values("volume", ascending=False)
    vp_sorted["cum_vol"] = vp_sorted["volume"].cumsum()
    va_rows = vp_sorted[vp_sorted["cum_vol"] <= target]

    vah = float(va_rows["price"].max()) if not va_rows.empty else poc
    val = float(va_rows["price"].min()) if not va_rows.empty else poc

    return {"poc": poc, "vah": vah, "val": val}
