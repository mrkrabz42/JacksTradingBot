"""Volatility Engine — ATR-based volatility classification per bar."""
from __future__ import annotations

import pandas as pd
import numpy as np

from bot.structure.config import VolatilityConfig


def compute_volatility_indicators(
    df: pd.DataFrame, config: VolatilityConfig | None = None
) -> pd.DataFrame:
    """Add ``atr`` and ``atr_baseline`` columns to *df*.

    Expects columns: ``high``, ``low``, ``close`` (or ``h``, ``l``, ``c``).
    Returns a copy with the new columns appended.
    """
    if config is None:
        config = VolatilityConfig()

    out = df.copy()

    # Normalise column names
    h = out["high"] if "high" in out.columns else out["h"]
    l = out["low"] if "low" in out.columns else out["l"]
    c = out["close"] if "close" in out.columns else out["c"]

    prev_c = c.shift(1)
    tr = pd.concat(
        [h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1
    ).max(axis=1)

    out["atr"] = tr.rolling(window=config.atr_period, min_periods=config.atr_period).mean()
    out["atr_baseline"] = out["atr"].rolling(
        window=config.baseline_lookback, min_periods=config.baseline_lookback
    ).mean()

    return out


def classify_volatility_series(
    df: pd.DataFrame, config: VolatilityConfig | None = None
) -> pd.Series:
    """Return a Series of ``LOW`` / ``MEDIUM`` / ``HIGH`` per bar.

    If fewer than ``min_bars_for_baseline`` rows or NaN values, defaults to
    ``MEDIUM``.
    """
    if config is None:
        config = VolatilityConfig()

    # Ensure indicators exist
    if "atr" not in df.columns or "atr_baseline" not in df.columns:
        df = compute_volatility_indicators(df, config)

    atr = df["atr"]
    baseline = df["atr_baseline"]

    low_thresh = baseline * config.low_vol_pct
    high_thresh = baseline * config.high_vol_pct

    conditions = [
        atr <= low_thresh,
        atr >= high_thresh,
    ]
    choices = ["LOW", "HIGH"]

    result = pd.Series(
        np.select(conditions, choices, default="MEDIUM"),
        index=df.index,
    )

    # Edge cases: NaN ATR or baseline → MEDIUM
    mask = atr.isna() | baseline.isna()
    result[mask] = "MEDIUM"

    # If total bars < min_bars_for_baseline, all MEDIUM
    if len(df) < config.min_bars_for_baseline:
        result[:] = "MEDIUM"

    return result
