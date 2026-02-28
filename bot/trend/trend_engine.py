"""Trend Strength Engine — scores trend intensity (0–100) and classifies direction."""
from __future__ import annotations

import numpy as np
import pandas as pd

from bot.structure.config import TrendConfig


def compute_trend_indicators(df: pd.DataFrame, config: TrendConfig | None = None) -> pd.DataFrame:
    """Add ema_fast, ema_slow, adx, ema_slope, reg_slope columns to *df*."""
    cfg = config or TrendConfig()
    out = df.copy()

    out["ema_fast"] = out["close"].ewm(span=cfg.fast_ema_period, adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=cfg.slow_ema_period, adjust=False).mean()

    # --- ADX (Wilder smoothing) ---
    high = out["high"].values
    low = out["low"].values
    close = out["close"].values
    n = len(out)
    period = cfg.adx_period

    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]

    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

    def _wilder_smooth(arr: np.ndarray) -> np.ndarray:
        result = np.full(n, np.nan)
        s = arr[:period].sum()
        result[period - 1] = s
        for i in range(period, n):
            result[i] = result[i - 1] - result[i - 1] / period + arr[i]
        return result

    s_pdm = _wilder_smooth(plus_dm)
    s_mdm = _wilder_smooth(minus_dm)
    s_tr = _wilder_smooth(tr)

    plus_di = np.where(s_tr > 0, s_pdm / s_tr * 100, 0.0)
    minus_di = np.where(s_tr > 0, s_mdm / s_tr * 100, 0.0)
    di_sum = plus_di + minus_di
    dx = np.where(di_sum > 0, np.abs(plus_di - minus_di) / di_sum * 100, 0.0)

    adx = np.full(n, np.nan)
    start_idx = 2 * period - 2
    if start_idx < n:
        adx[start_idx] = np.nanmean(dx[period - 1 : start_idx + 1])
        for i in range(start_idx + 1, n):
            adx[i] = (adx[i - 1] * (period - 1) + (0.0 if np.isnan(dx[i]) else dx[i])) / period

    out["adx"] = adx

    # --- EMA slope (normalized rate of change over regression_lookback) ---
    ema_slow_vals = out["ema_slow"].values
    lookback = cfg.regression_lookback
    ema_slope = np.full(n, np.nan)
    for i in range(lookback, n):
        prev = ema_slow_vals[i - lookback]
        if prev != 0:
            ema_slope[i] = (ema_slow_vals[i] - prev) / (lookback * prev)
    out["ema_slope"] = ema_slope

    # --- Linear regression slope (normalized by mean price) ---
    reg_slope = np.full(n, np.nan)
    x = np.arange(lookback, dtype=float)
    x_mean = x.mean()
    ss_xx = ((x - x_mean) ** 2).sum()
    for i in range(lookback - 1, n):
        window = close[i - lookback + 1 : i + 1]
        y_mean = window.mean()
        if y_mean == 0:
            continue
        ss_xy = ((x - x_mean) * (window - y_mean)).sum()
        slope = ss_xy / ss_xx
        reg_slope[i] = slope / y_mean
    out["reg_slope"] = reg_slope

    return out


def calculate_trend_strength_series(df: pd.DataFrame, config: TrendConfig | None = None) -> pd.DataFrame:
    """Return DataFrame with trend_strength_score (0–100) and trend_direction (UP/DOWN/NEUTRAL)."""
    cfg = config or TrendConfig()
    out = compute_trend_indicators(df, cfg)

    n = len(out)
    scores = np.zeros(n)
    directions: list[str] = ["NEUTRAL"] * n

    adx_vals = out["adx"].values
    ema_slope_vals = out["ema_slope"].values
    reg_slope_vals = out["reg_slope"].values

    for i in range(n):
        adx_v = adx_vals[i]
        es = ema_slope_vals[i]
        rs = reg_slope_vals[i]

        if i < cfg.min_bars or np.isnan(adx_v) or np.isnan(es) or np.isnan(rs):
            scores[i] = 0.0
            directions[i] = "NEUTRAL"
            continue

        # Score components (each 0–100)
        adx_score = min(adx_v, cfg.adx_cap) / cfg.adx_cap * 100
        ema_score = min(abs(es) / cfg.strong_slope_threshold, 1.0) * 100
        reg_score = min(abs(rs) / cfg.strong_slope_threshold, 1.0) * 100

        raw = adx_score * cfg.weight_adx + ema_score * cfg.weight_ema_slope + reg_score * cfg.weight_reg_slope
        scores[i] = round(max(0.0, min(100.0, raw)), 1)

        # Direction
        if es > 0 and rs > 0:
            directions[i] = "UP"
        elif es < 0 and rs < 0:
            directions[i] = "DOWN"
        else:
            directions[i] = "NEUTRAL"

    out["trend_strength_score"] = scores
    out["trend_direction"] = directions
    return out
