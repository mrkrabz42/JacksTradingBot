"""Market Regime Detector — classifies bars as TREND, RANGE, or TRANSITION."""
from __future__ import annotations

from collections import Counter

import pandas as pd
import ta

from bot.structure.config import RegimeConfig


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ADX using ta library."""
    adx_ind = ta.trend.ADXIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=period
    )
    return adx_ind.adx()


def compute_bb_width(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.Series:
    """Compute Bollinger Band width ratio: (upper - lower) / middle."""
    bb = ta.volatility.BollingerBands(
        close=df["close"], window=period, window_dev=std_dev
    )
    upper = bb.bollinger_hband()
    lower = bb.bollinger_lband()
    middle = bb.bollinger_mavg()
    return (upper - lower) / middle


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """Compute rolling session VWAP: cumsum(close * volume) / cumsum(volume)."""
    cum_pv = (df["close"] * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum()
    return cum_pv / cum_vol


def classify_regime(
    close: float,
    adx: float,
    bb_width: float,
    vwap: float,
    config: RegimeConfig,
) -> str:
    """Classify a single bar as TREND, RANGE, or TRANSITION."""
    dist_vwap_pct = abs(close - vwap) / vwap if vwap != 0 else 0.0

    is_adx_trending = adx >= config.adx_trend_threshold
    is_vol_low = bb_width <= config.bb_width_range_threshold
    is_vol_high = bb_width >= config.bb_width_trend_threshold
    near_vwap = dist_vwap_pct <= config.vwap_range_band_pct
    far_from_vwap = dist_vwap_pct >= config.vwap_trend_band_pct

    if not is_adx_trending and is_vol_low and near_vwap:
        return "RANGE"
    if is_adx_trending and (is_vol_high or far_from_vwap):
        return "TREND"
    return "TRANSITION"


def classify_regime_series(df: pd.DataFrame, config: RegimeConfig) -> pd.Series:
    """Classify regime for each bar with majority-vote smoothing."""
    adx = compute_adx(df, config.adx_period)
    bb_width = compute_bb_width(df, config.bb_period, config.bb_std_dev)
    vwap = compute_vwap(df)

    raw_regimes: list[str] = []
    for i in range(len(df)):
        a = adx.iloc[i]
        b = bb_width.iloc[i]
        v = vwap.iloc[i]
        c = df["close"].iloc[i]
        if pd.isna(a) or pd.isna(b) or pd.isna(v):
            raw_regimes.append("TRANSITION")
        else:
            raw_regimes.append(classify_regime(c, a, b, v, config))

    # Majority-vote smoothing
    smoothed: list[str] = []
    lookback = config.lookback_bars
    for i in range(len(raw_regimes)):
        window = raw_regimes[max(0, i - lookback + 1): i + 1]
        counts = Counter(window)
        smoothed.append(counts.most_common(1)[0][0])

    return pd.Series(smoothed, index=df.index, name="regime")


def compute_regime_indicators(df: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
    """Add adx, bb_width, vwap, dist_vwap_pct, and regime columns to df."""
    if config is None:
        config = RegimeConfig()

    result = df.copy()
    result["adx"] = compute_adx(result, config.adx_period)
    result["bb_width"] = compute_bb_width(result, config.bb_period, config.bb_std_dev)
    result["vwap"] = compute_vwap(result)
    result["dist_vwap_pct"] = abs(result["close"] - result["vwap"]) / result["vwap"]
    result["regime"] = classify_regime_series(result, config)

    return result
