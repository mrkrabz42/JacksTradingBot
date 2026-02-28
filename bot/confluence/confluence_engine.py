"""Weighted Confluence Engine — Core Brain.

Aggregates all environment signals into a single per-bar / per-event score:
  - ``confluence_score``  (0–100)
  - ``setup_grade``       (NO_TRADE / MEDIUM_SETUP / HIGH_SETUP / A_PLUS_SETUP)
  - ``trade_bias``        (LONG / SHORT / NEUTRAL)

Public interface
----------------
compute_confluence_for_bars(df, config) -> pd.DataFrame
    Adds confluence_score, setup_grade, bar_trade_bias to every row.

compute_confluence_for_events(df, events, config) -> list[dict]
    Enriches each event dict with confluence_score, setup_grade,
    event_trade_bias, and confluence_components.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from bot.structure.config import ConfluenceConfig

# ── Public interface ──────────────────────────────────────────────────────────


def compute_confluence_for_bars(
    df: pd.DataFrame,
    config: ConfluenceConfig | None = None,
) -> pd.DataFrame:
    """Compute confluence per execution-TF bar.

    Parameters
    ----------
    df:
        OHLCV + indicator DataFrame.  Expected columns (missing ones default
        to neutral values):
        ``trend_strength_score``, ``trend_direction``, ``regime``,
        ``volatility_state``, ``volume_state``, ``liquidity_magnet_score``,
        ``liquidity_draw_direction``, ``mtf_alignment_score``,
        ``mtf_alignment_state``.
    config:
        ``ConfluenceConfig``; defaults used when ``None``.

    Returns
    -------
    df with three new columns:
        ``confluence_score``, ``setup_grade``, ``bar_trade_bias``.
    """
    if config is None:
        config = ConfluenceConfig()

    df = df.copy()

    scores, grades, biases = [], [], []
    for _, row in df.iterrows():
        result = _compute_confluence(row=row, event=None, config=config)
        scores.append(result["confluence_score"])
        grades.append(result["setup_grade"])
        biases.append(result["trade_bias"])

    df["confluence_score"] = scores
    df["setup_grade"]      = grades
    df["bar_trade_bias"]   = biases
    return df


def compute_confluence_for_events(
    df: pd.DataFrame,
    events: list[dict[str, Any]],
    config: ConfluenceConfig | None = None,
) -> list[dict[str, Any]]:
    """Enrich MSS / break events with confluence fields.

    Looks up per-bar signals from ``df`` at each event's timestamp and
    merges them with event-specific data (MSS quality, breakout quality,
    direction).

    Parameters
    ----------
    df:
        Same indicator DataFrame used for ``compute_confluence_for_bars``.
    events:
        List of event dicts with at least ``time`` (or ``timestamp``) and
        ``direction``.
    config:
        ``ConfluenceConfig``; defaults used when ``None``.

    Returns
    -------
    Same list with ``confluence_score``, ``setup_grade``,
    ``event_trade_bias``, ``confluence_components`` added to each event.
    """
    if config is None:
        config = ConfluenceConfig()

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    time_idx: dict[Any, int] = {t: i for i, t in enumerate(df["time"])}

    enriched: list[dict[str, Any]] = []
    for evt in events:
        evt = dict(evt)
        raw_time = evt.get("time") or evt.get("timestamp")
        if raw_time is None:
            enriched.append(_attach_defaults(evt))
            continue
        ts  = pd.Timestamp(raw_time)
        idx = time_idx.get(ts)
        if idx is None:
            enriched.append(_attach_defaults(evt))
            continue

        row = df.iloc[idx]
        result = _compute_confluence(row=row, event=evt, config=config)
        evt["confluence_score"]       = result["confluence_score"]
        evt["setup_grade"]            = result["setup_grade"]
        evt["event_trade_bias"]       = result["trade_bias"]
        evt["confluence_components"]  = result["components"]
        enriched.append(evt)

    return enriched


# ── Component sub-scorers ─────────────────────────────────────────────────────


def score_trend_strength(row: Any, _cfg: ConfluenceConfig) -> float:
    ts  = float(getattr(row, "trend_strength_score", 0) or 0)
    dir_ = str(getattr(row, "trend_direction", "NEUTRAL") or "NEUTRAL")
    return ts * 0.5 if dir_ == "NEUTRAL" else ts


def score_regime(row: Any, _cfg: ConfluenceConfig) -> float:
    regime = str(getattr(row, "regime", "TRANSITION") or "TRANSITION")
    return {"TREND": 80.0, "TRANSITION": 60.0, "RANGE": 30.0}.get(regime, 60.0)


def score_volatility(row: Any, _cfg: ConfluenceConfig) -> float:
    vol = str(getattr(row, "volatility_state", "MEDIUM") or "MEDIUM")
    return {"MEDIUM": 80.0, "LOW": 60.0, "HIGH": 40.0}.get(vol, 60.0)


def score_volume_state(row: Any, _cfg: ConfluenceConfig) -> float:
    vs = str(getattr(row, "volume_state", "IN_VALUE") or "IN_VALUE")
    if vs in ("ACCEPTING_ABOVE", "ACCEPTING_BELOW"):
        return 80.0
    if vs == "IN_VALUE":
        return 60.0
    return 20.0  # REJECTING_*


def score_liquidity_alignment(
    row: Any,
    event_direction: str | None,
    _cfg: ConfluenceConfig,
) -> float:
    mag     = float(getattr(row, "liquidity_magnet_score", 50) or 50)
    liq_dir = str(getattr(row, "liquidity_draw_direction", "NEUTRAL") or "NEUTRAL")
    score   = mag

    if event_direction is not None:
        evt_up = event_direction.upper() in ("UP", "BULL", "BULL_MSS")
        if (evt_up and liq_dir == "ABOVE") or (not evt_up and liq_dir == "BELOW"):
            score = min(score * 1.1, 100.0)
        elif (evt_up and liq_dir == "BELOW") or (not evt_up and liq_dir == "ABOVE"):
            score = score * 0.8

    return min(max(score, 0.0), 100.0)


def score_mtf_alignment(
    row: Any,
    event_direction: str | None,
    _cfg: ConfluenceConfig,
) -> float:
    mtf_score = float(getattr(row, "mtf_alignment_score", 50) or 50)
    mtf_state = str(getattr(row, "mtf_alignment_state", "WEAK_ALIGN") or "WEAK_ALIGN")
    score     = mtf_score

    if event_direction is not None:
        evt_up = event_direction.upper() in ("UP", "BULL", "BULL_MSS")
        if (evt_up and "UP" in mtf_state) or (not evt_up and "DOWN" in mtf_state):
            score = min(score * 1.1, 100.0)
        elif (evt_up and "DOWN" in mtf_state) or (not evt_up and "UP" in mtf_state):
            score = score * 0.8

    return min(max(score, 0.0), 100.0)


def score_mss_quality(event: dict[str, Any] | None, _cfg: ConfluenceConfig) -> float:
    if event is None:
        return 50.0
    # displacement_quality is 0-1; mss_quality_score is 0-100
    raw = event.get("mss_quality_score") or event.get("displacement_quality")
    if raw is None:
        return 50.0
    val = float(raw)
    return val * 100.0 if val <= 1.0 else val


def score_breakout_quality(event: dict[str, Any] | None, _cfg: ConfluenceConfig) -> float:
    if event is None:
        return 50.0
    bkt_score = event.get("breakout_quality_score")
    bkt_type  = str(event.get("breakout_type") or "")
    if bkt_score is None:
        return 50.0
    score = float(bkt_score)
    if bkt_type == "FAKEOUT":
        score = min(score, 20.0)
    return score


# ── Trade bias ────────────────────────────────────────────────────────────────


def _compute_trade_bias(
    row: Any,
    event_direction: str | None,
    config: ConfluenceConfig,
) -> str:
    bias_cfg  = config.bias
    liq_dir   = str(getattr(row, "liquidity_draw_direction", "NEUTRAL") or "NEUTRAL")
    trend_dir = str(getattr(row, "trend_direction", "NEUTRAL") or "NEUTRAL")
    mtf_state = str(getattr(row, "mtf_alignment_state", "WEAK_ALIGN") or "WEAK_ALIGN")

    long_score  = 0.0
    short_score = 0.0

    # Event direction carries the most weight
    if event_direction is not None:
        evt_up = event_direction.upper() in ("UP", "BULL", "BULL_MSS")
        if evt_up:
            long_score  += 30.0
        else:
            short_score += 30.0

    # Trend alignment
    if trend_dir == "UP":
        long_score  += bias_cfg.trend_alignment_bonus
    elif trend_dir == "DOWN":
        short_score += bias_cfg.trend_alignment_bonus

    # MTF alignment
    if "UP" in mtf_state:
        long_score  += 20.0
    if "DOWN" in mtf_state:
        short_score += 20.0

    # Liquidity draw
    if liq_dir == "ABOVE":
        long_score  += bias_cfg.draw_alignment_bonus
    elif liq_dir == "BELOW":
        short_score += bias_cfg.draw_alignment_bonus

    min_bias = bias_cfg.min_bias_score
    if long_score >= min_bias and long_score > short_score:
        return "LONG"
    if short_score >= min_bias and short_score > long_score:
        return "SHORT"
    return "NEUTRAL"


# ── Grade classification ──────────────────────────────────────────────────────


def _classify_grade(score: float, config: ConfluenceConfig) -> str:
    thr = config.setup_thresholds
    if score >= thr.a_plus:
        return "A_PLUS_SETUP"
    if score >= thr.high:
        return "HIGH_SETUP"
    if score >= thr.medium:
        return "MEDIUM_SETUP"
    return "NO_TRADE"


# ── Core aggregator ───────────────────────────────────────────────────────────


def _compute_confluence(
    row: Any,
    event: dict[str, Any] | None,
    config: ConfluenceConfig,
) -> dict[str, Any]:
    evt_dir = None
    if event is not None:
        evt_dir = str(event.get("direction") or "")

    w = config.component_weights

    c_trend = score_trend_strength(row, config)
    c_reg   = score_regime(row, config)
    c_vol   = score_volatility(row, config)
    c_volume = score_volume_state(row, config)
    c_liq   = score_liquidity_alignment(row, evt_dir, config)
    c_mtf   = score_mtf_alignment(row, evt_dir, config)
    c_mss   = score_mss_quality(event, config)
    c_bkt   = score_breakout_quality(event, config)

    raw = (
        c_trend  * w.trend_strength +
        c_reg    * w.regime +
        c_vol    * w.volatility +
        c_volume * w.volume +
        c_liq    * w.liquidity +
        c_mtf    * w.mtf_alignment +
        c_mss    * w.mss_quality +
        c_bkt    * w.breakout_quality
    )
    score = round(min(max(raw, 0.0), 100.0), 2)
    grade = _classify_grade(score, config)
    bias  = _compute_trade_bias(row, evt_dir, config)

    return {
        "confluence_score": score,
        "setup_grade":      grade,
        "trade_bias":       bias,
        "components": {
            "trend":     round(c_trend),
            "regime":    round(c_reg),
            "volatility": round(c_vol),
            "volume":    round(c_volume),
            "liquidity": round(c_liq),
            "mtf":       round(c_mtf),
            "mss":       round(c_mss),
            "breakout":  round(c_bkt),
        },
    }


def _attach_defaults(evt: dict[str, Any]) -> dict[str, Any]:
    evt.update({
        "confluence_score":      0.0,
        "setup_grade":           "NO_TRADE",
        "event_trade_bias":      "NEUTRAL",
        "confluence_components": {
            "trend": 0, "regime": 0, "volatility": 0, "volume": 0,
            "liquidity": 0, "mtf": 0, "mss": 0, "breakout": 0,
        },
    })
    return evt
