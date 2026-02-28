"""Snapshot pipeline — runs all environment engines on a symbol's bars.

Orchestration order (per spec Step 8):
  1.  from_bars_df           → canonical snapshot schema
  2.  session tagging        → session column
  3.  add_session_high_low   → per-session H/L levels
  4.  volatility engine      → atr, atr_baseline, volatility_state
  5.  regime engine          → adx, bb_width, vwap (regime), regime
  6.  trend engine           → ema_fast/slow, trend_direction, trend_strength_score
  7.  volume engine          → vwap (session), poc, vah, val, volume_state
  8.  swing detection        → List[Swing] for liquidity module
  9.  liquidity engine       → dist columns, liquidity_draw_direction, liquidity_magnet_score
  10. participation engine   → rvol_ratio, participation_state, volume_spike_flag
  11. MTF alignment          → htf_bias, mtf_structure_bias, ltf_direction,
                               mtf_alignment_state, mtf_alignment_score
  12. confluence engine      → confluence_score, setup_grade, bar_trade_bias
  13. context formatter      → context_flags, environment_summary (latest bar)
  14. storage                → write enriched snapshot to SQLite
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from bot.snapshots.market_snapshot import from_bars_df
from bot.sessions.classifier import get_session
from bot.liquidity.session_levels import add_session_high_low
from bot.volatility.volatility_engine import (
    compute_volatility_indicators,
    classify_volatility_series,
)
from bot.structure.regime import compute_regime_indicators
from bot.trend.trend_engine import calculate_trend_strength_series
from bot.volume.volume_engine import compute_vwap_and_profile, classify_volume_state_series
from bot.structure.swing_engine import detect_swings
from bot.liquidity.liquidity_draw import (
    compute_liquidity_reference_levels,
    classify_liquidity_draw_series,
)
from bot.volume.participation_engine import apply_participation_metrics
from bot.mtf.mtf_alignment_engine import compute_mtf_alignment
from bot.confluence.confluence_engine import compute_confluence_for_bars
from bot.context.context_formatter import build_context_flags, build_environment_summary
from bot.storage.market_storage import init_storage, write_snapshots

_STORAGE_INITIALISED = False
_DB_URL = "sqlite:///bot_snapshots.sqlite"


# ── Storage init (once per process) ──────────────────────────────────────────

def _ensure_storage() -> None:
    global _STORAGE_INITIALISED
    if not _STORAGE_INITIALISED:
        init_storage(_DB_URL)
        _STORAGE_INITIALISED = True


# ── Session tagging ───────────────────────────────────────────────────────────

def _tag_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorised UTC session classification for every bar."""
    df = df.copy()
    df["session"] = df["timestamp_utc"].apply(
        lambda ts: get_session(ts.to_pydatetime()) if pd.notna(ts) else "OUTSIDE"
    )
    return df


# ── MTF resampling ────────────────────────────────────────────────────────────

def _resample_for_mtf(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample a snapshot DataFrame to a coarser timeframe.

    Runs the trend engine on the resampled bars so that
    ``trend_direction`` and ``trend_strength_score`` are available
    for MTF alignment.

    Parameters
    ----------
    df:
        Snapshot DataFrame with ``time``, ``open``, ``high``, ``low``,
        ``close``, ``volume`` columns.
    rule:
        Pandas resample rule, e.g. ``"W"`` (weekly) or ``"ME"`` (month-end).

    Returns
    -------
    DataFrame with ``time``, ``trend_direction``, ``trend_strength_score``.
    """
    resampled = (
        df.set_index("time")
        .resample(rule)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .dropna(subset=["close"])
        .reset_index()
    )

    if len(resampled) < 5:
        resampled["trend_direction"] = "NEUTRAL"
        resampled["trend_strength_score"] = 0.0
        return resampled

    try:
        resampled = calculate_trend_strength_series(resampled)
    except Exception as exc:
        logger.warning(f"[pipeline] MTF trend calc failed for rule={rule!r}: {exc}")
        resampled["trend_direction"] = "NEUTRAL"
        resampled["trend_strength_score"] = 0.0

    return resampled


# ── Nearest liquidity label ───────────────────────────────────────────────────

def _nearest_liquidity_label(row: dict) -> str | None:
    """Return a human-readable string for the nearest session liquidity level.

    Example: ``"London High 0.6 ATR above"``
    """
    atr = row.get("atr")
    close = row.get("close")
    if not atr or atr <= 0 or not close:
        return None

    candidates: list[tuple[float, str]] = []
    for key, label in [
        ("session_high_asia",   "Asia High"),
        ("session_low_asia",    "Asia Low"),
        ("session_high_london", "London High"),
        ("session_low_london",  "London Low"),
        ("session_high_ny",     "NY High"),
        ("session_low_ny",      "NY Low"),
    ]:
        level = row.get(key)
        if level is None:
            continue
        try:
            lf = float(level)
        except (TypeError, ValueError):
            continue
        if lf != lf:  # NaN check
            continue
        dist_atr = abs(lf - close) / atr
        direction = "above" if lf > close else "below"
        candidates.append((dist_atr, f"{label} {dist_atr:.1f} ATR {direction}"))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


# ── Main pipeline ─────────────────────────────────────────────────────────────

def build_enriched_snapshot(
    symbol: str,
    bars_df: pd.DataFrame,
    timeframe: str = "day",
    store: bool = True,
) -> pd.DataFrame:
    """Run all environment engines on *bars_df* and return an enriched snapshot DataFrame.

    Parameters
    ----------
    symbol:
        Ticker symbol, e.g. ``"AAPL"``.
    bars_df:
        Raw OHLCV DataFrame from Alpaca (Title-Case or lowercase columns,
        DatetimeIndex or named timestamp column).
    timeframe:
        Snapshot schema timeframe string, e.g. ``"day"``.
    store:
        If ``True``, persist the enriched snapshot to SQLite after completion.

    Returns
    -------
    Enriched snapshot DataFrame with all derived environment columns populated.
    """
    logger.debug(f"[pipeline] {symbol}: building enriched snapshot ({len(bars_df)} bars)")

    # ── 1. Canonical snapshot schema ─────────────────────────────────────
    df = from_bars_df(symbol, timeframe, bars_df)

    # Add `time` alias — required by swing engine, liquidity, MTF, volume engines
    df["time"] = df["timestamp_utc"]

    # ── 2. Session tagging ────────────────────────────────────────────────
    df = _tag_sessions(df)

    # ── 3. Session high / low ─────────────────────────────────────────────
    df = add_session_high_low(df)

    # ── 4. Volatility ─────────────────────────────────────────────────────
    df = compute_volatility_indicators(df)
    df["volatility_state"] = classify_volatility_series(df)

    # ── 5. Regime ─────────────────────────────────────────────────────────
    # Adds adx, bb_width, vwap (regime rolling), regime
    df = compute_regime_indicators(df)

    # ── 6. Trend strength ─────────────────────────────────────────────────
    # Adds ema_fast, ema_slow, trend_direction, trend_strength_score
    df = calculate_trend_strength_series(df)

    # ── 7. Volume profile ─────────────────────────────────────────────────
    # Overwrites vwap with session-based VWAP; adds poc, vah, val, volume_state
    df = compute_vwap_and_profile(df)
    df["volume_state"] = classify_volume_state_series(df)

    # ── 8. Swing detection ────────────────────────────────────────────────
    swings = detect_swings(df)

    # ── 9. Liquidity reference levels + draw ──────────────────────────────
    # Requires: time, high, low, close, atr (from volatility), session levels
    df = compute_liquidity_reference_levels(df, swings)
    df = classify_liquidity_draw_series(df)

    # ── 10. Participation / RVOL ──────────────────────────────────────────
    df = apply_participation_metrics(df)

    # ── 11. Multi-timeframe alignment ─────────────────────────────────────
    # Resample daily → weekly (MTF) and month-end (HTF), run trend on each
    try:
        df_mtf = _resample_for_mtf(df, "W")
        df_htf = _resample_for_mtf(df, "ME")
        if not df_mtf.empty and not df_htf.empty:
            df = compute_mtf_alignment(df, df_mtf, df_htf)
    except Exception as exc:
        logger.warning(f"[pipeline] {symbol}: MTF alignment failed — {exc}")

    # ── 12. Confluence ────────────────────────────────────────────────────
    df = compute_confluence_for_bars(df)

    # ── 13. Persist to storage ────────────────────────────────────────────
    if store:
        try:
            _ensure_storage()
            write_snapshots(symbol, timeframe, df)
        except Exception as exc:
            logger.warning(f"[pipeline] {symbol}: storage write failed — {exc}")

    last = df.iloc[-1]
    logger.debug(
        f"[pipeline] {symbol}: enriched OK — "
        f"regime={last.get('regime')} | "
        f"trend={last.get('trend_direction')} ({last.get('trend_strength_score', 0):.0f}) | "
        f"grade={last.get('setup_grade')} | "
        f"confluence={last.get('confluence_score', 0):.0f}"
    )
    return df


def get_latest_context(df: pd.DataFrame) -> dict:
    """Extract context flags and environment summary from the latest bar.

    Returns
    -------
    dict with keys:
        ``context_flags``, ``environment_summary``, ``setup_grade``,
        ``confluence_score``, ``bar_trade_bias``, ``regime``,
        ``volatility_state``, ``trend_direction``, ``trend_strength_score``,
        ``liquidity_draw_direction``, ``liquidity_magnet_score``,
        ``mtf_alignment_state``, ``nearest_liquidity``.
    """
    last = df.iloc[-1].to_dict()
    flags = build_context_flags(last)
    summary = build_environment_summary(last)
    nearest = _nearest_liquidity_label(last)

    return {
        "context_flags": flags,
        "environment_summary": summary,
        "setup_grade": last.get("setup_grade"),
        "confluence_score": last.get("confluence_score"),
        "bar_trade_bias": last.get("bar_trade_bias"),
        "regime": last.get("regime"),
        "volatility_state": last.get("volatility_state"),
        "trend_direction": last.get("trend_direction"),
        "trend_strength_score": last.get("trend_strength_score"),
        "liquidity_draw_direction": last.get("liquidity_draw_direction"),
        "liquidity_magnet_score": last.get("liquidity_magnet_score"),
        "mtf_alignment_state": last.get("mtf_alignment_state"),
        "nearest_liquidity": nearest,
    }
