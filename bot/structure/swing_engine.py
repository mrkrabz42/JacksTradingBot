"""Module 1: Swing Engine — detects swing highs/lows and classifies trend."""
from __future__ import annotations

from typing import List, Optional, TypedDict

import pandas as pd

from bot.structure.config import SwingConfig


class Swing(TypedDict):
    type: str          # "high" or "low"
    index: int
    price: float
    time: str          # ISO timestamp


def detect_swings(df: pd.DataFrame, config: Optional[SwingConfig] = None) -> List[Swing]:
    """Detect swing highs and lows using N-bar lookback/forward pivot detection.

    df must have columns: high, low, close, time (lowercase).
    """
    if config is None:
        config = SwingConfig()
    n = config.lookback_n
    swings: List[Swing] = []

    for i in range(n, len(df) - n):
        window_high = df["high"].iloc[i - n : i + n + 1]
        window_low = df["low"].iloc[i - n : i + n + 1]

        # Swing High: bar's high is the max in the 2N+1 window
        if df["high"].iloc[i] == window_high.max():
            swings.append({
                "type": "high",
                "index": i,
                "price": float(df["high"].iloc[i]),
                "time": str(df["time"].iloc[i]),
            })

        # Swing Low: bar's low is the min in the 2N+1 window
        if df["low"].iloc[i] == window_low.min():
            swings.append({
                "type": "low",
                "index": i,
                "price": float(df["low"].iloc[i]),
                "time": str(df["time"].iloc[i]),
            })

    return sorted(swings, key=lambda x: x["index"])


def classify_trend(swings: List[Swing], config: Optional[SwingConfig] = None) -> str:
    """Classify trend from swing sequence as UPTREND, DOWNTREND, or RANGING."""
    if config is None:
        config = SwingConfig()

    highs = [s for s in swings if s["type"] == "high"][-2:]
    lows = [s for s in swings if s["type"] == "low"][-2:]

    if len(highs) < 2 or len(lows) < 2:
        return "RANGING"

    hh = highs[-1]["price"] > highs[-2]["price"]  # Higher High
    hl = lows[-1]["price"] > lows[-2]["price"]     # Higher Low
    lh = highs[-1]["price"] < highs[-2]["price"]   # Lower High
    ll = lows[-1]["price"] < lows[-2]["price"]      # Lower Low

    if hh and hl:
        return "UPTREND"
    elif lh and ll:
        return "DOWNTREND"
    else:
        return "RANGING"
