"""Canonical MarketSnapshot schema.

A single, authoritative data model for every bar in the execution pipeline.
All engine modules (regime, volatility, trend, volume, liquidity, MTF
alignment, breakout quality, confluence) read from and write into this schema.

Usage
-----
Build from raw OHLCV bars:
    df = build_snapshot_df("SPY", "5m", raw_bar_list)

Validate before running the full pipeline:
    validate_snapshot_df(df)  # raises on missing core fields; warns on missing derived

Add engine outputs as normal DataFrame column assignments:
    df["regime"] = compute_regime_series(df)   # already returns matching column name
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd
from loguru import logger


# ── Core field list (always required) ────────────────────────────────────────

REQUIRED_CORE_FIELDS: list[str] = [
    "symbol", "timeframe", "timestamp_utc",
    "open", "high", "low", "close", "volume",
]

# All derived fields that should be present after full pipeline processing
DERIVED_ENVIRONMENT_FIELDS: list[str] = [
    "session",
    "session_high", "session_low",
    "session_high_asia", "session_low_asia",
    "session_high_london", "session_low_london",
    "session_high_ny", "session_low_ny",
    "regime", "volatility_state",
    "trend_direction", "trend_strength_score",
    "vwap", "poc", "vah", "val", "volume_state",
    "liquidity_draw_direction", "liquidity_magnet_score",
    "htf_bias", "mtf_structure_bias", "ltf_direction",
    "mtf_alignment_state", "mtf_alignment_score",
    "breakout_quality_score", "breakout_type",
    "confluence_score", "setup_grade", "bar_trade_bias",
    "rvol_ratio", "participation_state", "volume_spike_flag",
]


# ── Canonical dataclass ───────────────────────────────────────────────────────

@dataclass
class MarketSnapshot:
    """One execution-timeframe bar with all environment fields.

    Core OHLCV fields are always required.  All derived fields default to
    ``None`` and are populated progressively as each engine module runs.
    """

    # ── Core (always present) ────────────────────────────────────────
    symbol: str
    timeframe: str                     # e.g. "5m", "1h"
    timestamp_utc: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float

    # ── Session / structural tag ─────────────────────────────────────
    session: str | None = None         # 'ASIA' | 'LONDON' | 'NY' | 'OUTSIDE'

    # ── Session-specific liquidity levels ────────────────────────────
    session_high: float | None = None         # current session's high for this day
    session_low: float | None = None          # current session's low for this day
    session_high_asia: float | None = None
    session_low_asia: float | None = None
    session_high_london: float | None = None
    session_low_london: float | None = None
    session_high_ny: float | None = None
    session_low_ny: float | None = None

    # ── Market regime ────────────────────────────────────────────────
    regime: str | None = None          # 'TREND' | 'RANGE' | 'TRANSITION'
    volatility_state: str | None = None  # 'LOW' | 'MEDIUM' | 'HIGH'

    # ── Trend ────────────────────────────────────────────────────────
    trend_direction: str | None = None       # 'UP' | 'DOWN' | 'NEUTRAL'
    trend_strength_score: float | None = None  # 0–100

    # ── Volume / value area ──────────────────────────────────────────
    vwap: float | None = None
    poc: float | None = None
    vah: float | None = None
    val: float | None = None
    volume_state: str | None = None    # 'IN_VALUE' | 'ACCEPTING_ABOVE' | 'ACCEPTING_BELOW'
                                       # | 'REJECTING_ABOVE' | 'REJECTING_BELOW'

    # ── Liquidity proximity / draw ───────────────────────────────────
    liquidity_draw_direction: str | None = None   # 'ABOVE' | 'BELOW' | 'NEUTRAL'
    liquidity_magnet_score: float | None = None   # 0–100

    # ── Multi-timeframe alignment ────────────────────────────────────
    htf_bias: str | None = None           # 'UP' | 'DOWN' | 'RANGE'
    mtf_structure_bias: str | None = None  # 'LONG_BIAS' | 'SHORT_BIAS' | 'NEUTRAL'
    ltf_direction: str | None = None       # 'UP' | 'DOWN' | 'NEUTRAL'
    mtf_alignment_state: str | None = None
    mtf_alignment_score: float | None = None  # 0–100

    # ── Breakout quality (bar context) ───────────────────────────────
    breakout_quality_score: float | None = None  # 0–100
    breakout_type: str | None = None             # 'CONTINUATION' | 'FAKEOUT' | 'UNCLEAR'

    # ── Confluence summary (core brain) ─────────────────────────────
    confluence_score: float | None = None   # 0–100
    setup_grade: str | None = None          # 'NO_TRADE' | 'MEDIUM_SETUP'
                                            # | 'HIGH_SETUP' | 'A_PLUS_SETUP'
    bar_trade_bias: str | None = None       # 'LONG' | 'SHORT' | 'NEUTRAL'

    # ── Participation / RVOL ─────────────────────────────────────────
    rvol_ratio: float | None = None
    participation_state: str | None = None  # 'LOW_ACTIVITY' | 'NORMAL' | 'ELEVATED' | 'EXTREME'
    volume_spike_flag: bool | None = None


# ── Factory helpers ───────────────────────────────────────────────────────────

def make_base_snapshot(
    symbol: str,
    timeframe: str,
    bar: dict[str, Any],
) -> MarketSnapshot:
    """Create a ``MarketSnapshot`` with core OHLCV fields filled, all others ``None``.

    Parameters
    ----------
    symbol:
        Ticker, e.g. ``"SPY"``.
    timeframe:
        Bar timeframe string, e.g. ``"5m"`` or ``"1h"``.
    bar:
        Dict with keys: ``timestamp_utc``, ``open``, ``high``, ``low``,
        ``close``, ``volume``.

    Returns
    -------
    ``MarketSnapshot`` with core fields set; derived fields default to ``None``.
    """
    return MarketSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        timestamp_utc=pd.Timestamp(bar["timestamp_utc"]),
        open=float(bar["open"]),
        high=float(bar["high"]),
        low=float(bar["low"]),
        close=float(bar["close"]),
        volume=float(bar["volume"]),
    )


def snapshot_to_dict(snapshot: MarketSnapshot) -> dict[str, Any]:
    """Convert a ``MarketSnapshot`` to a plain dict (DataFrame-compatible)."""
    return asdict(snapshot)


def build_snapshot_df(
    symbol: str,
    timeframe: str,
    raw_bars: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build a snapshot DataFrame from a list of raw OHLCV dicts.

    Each dict must contain: ``timestamp_utc``, ``open``, ``high``, ``low``,
    ``close``, ``volume``.  All derived snapshot fields are added as ``None``
    columns so downstream modules can fill them in.

    Parameters
    ----------
    symbol:
        Ticker symbol.
    timeframe:
        Bar timeframe string.
    raw_bars:
        List of dicts, one per bar.

    Returns
    -------
    ``pd.DataFrame`` with columns matching ``MarketSnapshot`` fields, sorted
    by ``timestamp_utc`` ascending.
    """
    snapshots = [make_base_snapshot(symbol, timeframe, b) for b in raw_bars]
    df = pd.DataFrame([snapshot_to_dict(s) for s in snapshots])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df.sort_values("timestamp_utc").reset_index(drop=True)
    return df


def from_bars_df(
    symbol: str,
    timeframe: str,
    bars_df: pd.DataFrame,
    ts_col: str = "timestamp_utc",
) -> pd.DataFrame:
    """Convert an existing OHLCV DataFrame to the snapshot schema.

    Handles the case where ``bars_df`` has a DatetimeIndex (Alpaca-style) or
    a named timestamp column.  Normalises column names to lowercase.

    Parameters
    ----------
    symbol:
        Ticker symbol.
    timeframe:
        Bar timeframe string.
    bars_df:
        OHLCV DataFrame.  Columns may be Title-Case (``Open``, ``High`` …)
        or lowercase.  Index may be the timestamp.
    ts_col:
        Name for the resulting timestamp column.

    Returns
    -------
    Snapshot-schema DataFrame with ``symbol`` and ``timeframe`` prepended.
    """
    df = bars_df.copy()

    # Reset DatetimeIndex → column
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        # Alpaca names the index column 'timestamp' after reset
        for candidate in ("timestamp", "index"):
            if candidate in df.columns:
                df = df.rename(columns={candidate: ts_col})
                break

    # Normalise OHLCV column names to lowercase
    col_map = {c: c.lower() for c in df.columns}
    df = df.rename(columns=col_map)

    # Ensure ts_col is correct
    if ts_col not in df.columns:
        raise ValueError(
            f"Cannot find timestamp column in bars_df. "
            f"Expected '{ts_col}' after normalisation. "
            f"Available columns: {list(df.columns)}"
        )

    df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
    df.insert(0, "timeframe", timeframe)
    df.insert(0, "symbol", symbol)

    # Add any missing snapshot fields as None
    all_fields = [f.name for f in MarketSnapshot.__dataclass_fields__.values()]
    for field_name in all_fields:
        if field_name not in df.columns:
            df[field_name] = None

    df = df.sort_values(ts_col).reset_index(drop=True)
    return df


# ── Validation ────────────────────────────────────────────────────────────────

def validate_snapshot_df(df: pd.DataFrame) -> None:
    """Validate that a snapshot DataFrame has the expected structure.

    Raises
    ------
    ValueError
        If any required core field is missing.

    Logs warnings for missing derived fields (non-fatal — they may not have
    been computed yet).
    """
    missing_core = [f for f in REQUIRED_CORE_FIELDS if f not in df.columns]
    if missing_core:
        raise ValueError(
            f"Snapshot DataFrame missing required core fields: {missing_core}"
        )

    missing_derived = [f for f in DERIVED_ENVIRONMENT_FIELDS if f not in df.columns]
    if missing_derived:
        logger.warning(
            f"Snapshot DataFrame missing derived fields (not yet computed): "
            f"{missing_derived}"
        )

    null_core = [
        f for f in REQUIRED_CORE_FIELDS
        if f in df.columns and df[f].isna().any()
    ]
    if null_core:
        logger.warning(
            f"Snapshot DataFrame has null values in core fields: {null_core}"
        )

    logger.debug(
        f"validate_snapshot_df: {len(df)} rows, "
        f"{len(df.columns)} columns — OK"
    )
