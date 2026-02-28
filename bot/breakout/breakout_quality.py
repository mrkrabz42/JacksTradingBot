"""Breakout Quality Model.

Evaluates each MSS / structure-break event on four dimensions:
  1. Break Strength   – how decisively price closed beyond the broken level.
  2. Retest Quality   – did price cleanly retest and hold the broken level?
  3. Volume Confirmation – relative volume and acceptance state at the break.
  4. Environment Alignment – MTF alignment, liquidity draw, regime context.

Public interface
----------------
evaluate_breakout_events(df, events, config) -> list[dict]
    Enriches each event with breakout_quality_score, breakout_type, and
    the four sub-scores.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from bot.structure.config import BreakoutConfig


# ── Public interface ──────────────────────────────────────────────────────────

def evaluate_breakout_events(
    df: pd.DataFrame,
    events: list[dict[str, Any]],
    config: BreakoutConfig | None = None,
) -> list[dict[str, Any]]:
    """Evaluate breakout quality for a list of MSS / break events.

    Parameters
    ----------
    df:
        OHLCV + indicator DataFrame at the execution timeframe (e.g. 5M).
        Must contain: ``time``, ``open``, ``high``, ``low``, ``close``,
        ``volume``, and any indicator columns referenced (``atr``,
        ``volatility_state``, ``trend_direction``, ``trend_strength_score``,
        ``regime``, ``volume_state``, ``liquidity_draw_direction``,
        ``liquidity_magnet_score``, ``mtf_alignment_score``).
    events:
        List of event dicts, each with at least:
        ``time``, ``direction`` (``'BULL'``/``'BEAR'`` or ``'UP'``/``'DOWN'``),
        ``control_point_price`` (the broken price level).
    config:
        ``BreakoutConfig`` instance; uses defaults when ``None``.

    Returns
    -------
    Same list with these fields added to every event:
        ``breakout_quality_score``, ``breakout_type``,
        ``break_strength_score``, ``retest_quality_score``,
        ``volume_confirmation_score``, ``environment_alignment_score``,
        ``has_clean_retest``, ``closed_beyond_level``.
    """
    if config is None:
        config = BreakoutConfig()

    # ── Prepare a time-indexed view for fast row lookup ────────────────
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # Rolling volume mean (20-bar SMA of volume)
    df["_vol_sma"] = df["volume"].rolling(20, min_periods=1).mean()

    # Build a time → row-index map for O(1) lookup
    time_to_idx: dict[Any, int] = {t: i for i, t in enumerate(df["time"])}

    enriched: list[dict[str, Any]] = []
    for evt in events:
        enriched.append(_evaluate_one(evt, df, time_to_idx, config))

    return enriched


# ── Per-event evaluation ──────────────────────────────────────────────────────

def _evaluate_one(
    evt: dict[str, Any],
    df: pd.DataFrame,
    time_to_idx: dict[Any, int],
    cfg: BreakoutConfig,
) -> dict[str, Any]:
    evt = dict(evt)  # shallow copy so we don't mutate the caller's dict

    # ── Locate the event bar ───────────────────────────────────────────
    raw_time = evt.get("time") or evt.get("timestamp")
    if raw_time is None:
        return _attach_defaults(evt)

    ts = pd.Timestamp(raw_time)
    idx = time_to_idx.get(ts)
    if idx is None:
        return _attach_defaults(evt)

    row = df.iloc[idx]

    # ── Derive break direction ─────────────────────────────────────────
    direction = str(evt.get("direction", "")).upper()
    break_direction = "UP" if direction in ("BULL", "BULL_MSS", "UP") else "DOWN"

    broken_level: float = float(
        evt.get("control_point_price")
        or evt.get("broken_level")
        or row["close"]
    )

    close = float(row["close"])
    atr   = float(row["atr"]) if "atr" in df.columns and not pd.isna(row.get("atr", float("nan"))) else None

    # ── Sub-score 1: Break strength ────────────────────────────────────
    bs_score, closed_beyond = _score_break_strength(
        close, broken_level, break_direction, atr, cfg
    )

    # ── Sub-score 2: Retest quality ────────────────────────────────────
    lookahead = df.iloc[idx + 1 : idx + 1 + cfg.lookahead_bars_for_retest]
    rt_score, has_clean_retest = _score_retest(
        lookahead, broken_level, break_direction, atr, cfg
    )

    # ── Sub-score 3: Volume confirmation ──────────────────────────────
    vol_raw   = float(row["volume"]) if "volume" in df.columns else 0.0
    vol_sma   = float(row["_vol_sma"]) if "_vol_sma" in df.columns and row["_vol_sma"] > 0 else 1.0
    vol_state = str(row.get("volume_state", "")) if "volume_state" in df.columns else ""
    vc_score  = _score_volume(vol_raw, vol_sma, vol_state, break_direction, cfg)

    # ── Sub-score 4: Environment alignment ────────────────────────────
    mtf_score   = float(row.get("mtf_alignment_score", 50)) if "mtf_alignment_score" in df.columns else 50.0
    liq_dir     = str(row.get("liquidity_draw_direction", "")) if "liquidity_draw_direction" in df.columns else ""
    liq_mag     = float(row.get("liquidity_magnet_score", 0)) if "liquidity_magnet_score" in df.columns else 0.0
    regime      = str(row.get("regime", "TRANSITION")) if "regime" in df.columns else "TRANSITION"
    env_score   = _score_environment(mtf_score, liq_dir, liq_mag, regime, break_direction)

    # ── Combine ────────────────────────────────────────────────────────
    w = cfg.weights
    quality = (
        bs_score  * w.break_strength +
        rt_score  * w.retest_quality +
        vc_score  * w.volume_confirmation +
        env_score * w.environment_alignment
    )
    quality = round(min(max(quality, 0.0), 100.0), 2)

    if quality >= cfg.continuation_threshold:
        btype = "CONTINUATION"
    elif quality <= cfg.fakeout_threshold:
        btype = "FAKEOUT"
    else:
        btype = "UNCLEAR"

    evt.update({
        "breakout_quality_score":       quality,
        "breakout_type":                btype,
        "break_strength_score":         round(bs_score, 2),
        "retest_quality_score":         round(rt_score, 2),
        "volume_confirmation_score":    round(vc_score, 2),
        "environment_alignment_score":  round(env_score, 2),
        "has_clean_retest":             has_clean_retest,
        "closed_beyond_level":          closed_beyond,
    })
    return evt


# ── Sub-scorers ───────────────────────────────────────────────────────────────

def _score_break_strength(
    close: float,
    broken_level: float,
    break_direction: str,
    atr: float | None,
    cfg: BreakoutConfig,
) -> tuple[float, bool]:
    """Return (score 0-100, closed_beyond_level flag)."""
    if atr is None or atr <= 0:
        return 0.0, False

    delta = (close - broken_level) if break_direction == "UP" else (broken_level - close)
    delta_atr = delta / atr
    closed_beyond = delta_atr > 0

    if delta_atr <= 0:
        score = 0.0
    elif delta_atr >= cfg.strong_close_beyond_atr:
        score = 100.0
    else:
        x = (delta_atr - cfg.min_close_beyond_atr) / (
            cfg.strong_close_beyond_atr - cfg.min_close_beyond_atr
        )
        score = max(0.0, min(x, 1.0)) * 100.0

    return score, closed_beyond


def _score_retest(
    lookahead: pd.DataFrame,
    broken_level: float,
    break_direction: str,
    atr: float | None,
    cfg: BreakoutConfig,
) -> tuple[float, bool]:
    """Return (score 0-100, has_clean_retest flag)."""
    if atr is None or atr <= 0 or lookahead.empty:
        return 50.0, False

    tolerance = cfg.max_retest_tolerance_atr * atr
    has_clean_retest = False
    failed_retest = False

    for _, bar in lookahead.iterrows():
        if break_direction == "UP":
            distance = broken_level - float(bar["low"])
            if 0 <= distance <= tolerance:
                if float(bar["close"]) >= broken_level:
                    has_clean_retest = True
                else:
                    failed_retest = True
                    break
        else:  # DOWN
            distance = float(bar["high"]) - broken_level
            if 0 <= distance <= tolerance:
                if float(bar["close"]) <= broken_level:
                    has_clean_retest = True
                else:
                    failed_retest = True
                    break

    if has_clean_retest and not failed_retest:
        return 85.0, True
    if failed_retest:
        return 10.0, False
    return 50.0, False  # no clear retest


def _score_volume(
    vol: float,
    vol_sma: float,
    volume_state: str,
    break_direction: str,
    cfg: BreakoutConfig,
) -> float:
    """Return volume confirmation score 0-100."""
    rel_vol = vol / vol_sma if vol_sma > 0 else 0.0

    if rel_vol >= cfg.strong_volume_relative:
        score = 100.0
    elif rel_vol >= cfg.min_volume_relative:
        x = (rel_vol - cfg.min_volume_relative) / (
            cfg.strong_volume_relative - cfg.min_volume_relative
        )
        score = max(0.0, min(x, 1.0)) * 100.0
    else:
        score = 20.0

    # Directional adjustment based on volume acceptance state
    if break_direction == "UP" and volume_state == "REJECTING_ABOVE":
        score = min(score, 20.0)
    elif break_direction == "DOWN" and volume_state == "REJECTING_BELOW":
        score = min(score, 20.0)
    # Accepting states get a small boost (cap at 100)
    elif break_direction == "UP" and volume_state == "ACCEPTING_ABOVE":
        score = min(score * 1.1, 100.0)
    elif break_direction == "DOWN" and volume_state == "ACCEPTING_BELOW":
        score = min(score * 1.1, 100.0)

    return score


def _score_environment(
    mtf_alignment_score: float,
    liquidity_draw_direction: str,
    liquidity_magnet_score: float,
    regime: str,
    break_direction: str,
) -> float:
    """Return environment alignment score 0-100."""
    score = float(mtf_alignment_score)

    # Liquidity draw alignment
    liq_up   = liquidity_draw_direction == "ABOVE"
    liq_down = liquidity_draw_direction == "BELOW"
    mag = liquidity_magnet_score / 100.0

    if (break_direction == "UP"   and liq_up) or \
       (break_direction == "DOWN" and liq_down):
        score = min(score * (1.0 + 0.2 * mag), 100.0)
    elif (break_direction == "UP"   and liq_down) or \
         (break_direction == "DOWN" and liq_up):
        score = score * (1.0 - 0.2 * mag)

    # Regime penalty for RANGE
    if regime == "RANGE":
        score *= 0.75

    return min(max(score, 0.0), 100.0)


# ── Fallback when data is unavailable ────────────────────────────────────────

def _attach_defaults(evt: dict[str, Any]) -> dict[str, Any]:
    evt.update({
        "breakout_quality_score":       0.0,
        "breakout_type":                "UNCLEAR",
        "break_strength_score":         0.0,
        "retest_quality_score":         50.0,
        "volume_confirmation_score":    20.0,
        "environment_alignment_score":  50.0,
        "has_clean_retest":             False,
        "closed_beyond_level":          False,
    })
    return evt
