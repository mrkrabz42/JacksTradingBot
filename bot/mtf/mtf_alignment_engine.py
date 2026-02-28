"""Multi-Timeframe (MTF) Alignment Engine.

Aligns HTF (1H), MTF (15M), and LTF (5M) trend signals onto the LTF
timeline and produces a discrete alignment state + numeric score (0-100).

Public interface
----------------
compute_mtf_alignment(df_ltf, df_mtf, df_htf, config) -> pd.DataFrame
    Attaches htf_bias, mtf_structure_bias, ltf_direction,
    mtf_alignment_state, and mtf_alignment_score to every row of df_ltf.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bot.structure.config import MTFConfig


# ── Public interface ──────────────────────────────────────────────────────────

def compute_mtf_alignment(
    df_ltf: pd.DataFrame,
    df_mtf: pd.DataFrame,
    df_htf: pd.DataFrame,
    config: MTFConfig | None = None,
) -> pd.DataFrame:
    """Compute per-LTF-bar multi-timeframe alignment fields.

    Parameters
    ----------
    df_ltf:
        Execution timeframe bars (e.g. 5M).
        Must have: ``time``, ``trend_direction``, ``trend_strength_score``.
    df_mtf:
        Middle timeframe bars (e.g. 15M).
        Must have: ``time``, ``trend_direction``, ``trend_strength_score``.
    df_htf:
        Higher timeframe bars (e.g. 1H).
        Must have: ``time``, ``trend_direction``, ``trend_strength_score``.
        Optionally: ``regime``.
    config:
        ``MTFConfig``; defaults are used when ``None``.

    Returns
    -------
    pd.DataFrame (copy of df_ltf) with added columns:
        htf_bias             : 'UP' | 'DOWN' | 'RANGE'
        mtf_structure_bias   : 'LONG_BIAS' | 'SHORT_BIAS' | 'NEUTRAL'
        ltf_direction        : 'UP' | 'DOWN' | 'NEUTRAL'
        trend_direction_ltf  : alias for ltf_direction
        mtf_alignment_state  : see Section 6.2 of spec
        mtf_alignment_score  : float 0–100
    """
    if config is None:
        config = MTFConfig()

    # ── 1. Normalise time columns ─────────────────────────────────────────
    def _to_dt(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = pd.to_datetime(df["time"])
        return df.sort_values("time").reset_index(drop=True)

    ltf = _to_dt(df_ltf)
    mtf = _to_dt(df_mtf)
    htf = _to_dt(df_htf)

    # ── 2. merge_asof: bring MTF + HTF onto LTF timeline ─────────────────
    mtf_cols = [c for c in ["time", "trend_direction", "trend_strength_score"] if c in mtf.columns]
    htf_cols = [c for c in ["time", "trend_direction", "trend_strength_score", "regime"] if c in htf.columns]

    merged = pd.merge_asof(
        ltf,
        mtf[mtf_cols],
        on="time",
        direction="backward",
        suffixes=("", "_mtf"),
    )
    merged = pd.merge_asof(
        merged,
        htf[htf_cols],
        on="time",
        direction="backward",
        suffixes=("", "_htf"),
    )

    # ── 3. Ensure consistent column names ─────────────────────────────────
    # LTF originals keep their names; merged adds _mtf / _htf suffixes.
    # Create _ltf aliases for the LTF trend columns.
    if "trend_direction" in merged.columns:
        merged["trend_direction_ltf"] = merged["trend_direction"]
    if "trend_strength_score" in merged.columns:
        merged["trend_strength_score_ltf"] = merged["trend_strength_score"]

    # Ensure all required cols exist (fill NaN if merge found no earlier bar)
    for col in ["trend_direction_mtf", "trend_strength_score_mtf",
                "trend_direction_htf", "trend_strength_score_htf"]:
        if col not in merged.columns:
            merged[col] = np.nan

    if "regime_htf" not in merged.columns:
        merged["regime_htf"] = "TRANSITION"

    # Fill missing strengths with 0
    for col in ["trend_strength_score_ltf", "trend_strength_score_mtf", "trend_strength_score_htf"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)

    # Fill missing directions with NEUTRAL
    for col in ["trend_direction_ltf", "trend_direction_mtf", "trend_direction_htf"]:
        merged[col] = merged[col].fillna("NEUTRAL")

    merged["regime_htf"] = merged["regime_htf"].fillna("TRANSITION")

    htf_min = config.htf_trend_min_strength
    mtf_min = config.mtf_trend_min_strength

    # ── 4. HTF bias ────────────────────────────────────────────────────────
    htf_conds = [
        merged["regime_htf"] == "RANGE",
        (merged["trend_direction_htf"] == "UP")   & (merged["trend_strength_score_htf"] >= htf_min),
        (merged["trend_direction_htf"] == "DOWN")  & (merged["trend_strength_score_htf"] >= htf_min),
    ]
    merged["htf_bias"] = np.select(htf_conds, ["RANGE", "UP", "DOWN"], default="RANGE")

    # ── 5. MTF structure bias ──────────────────────────────────────────────
    mtf_conds = [
        (merged["trend_direction_mtf"] == "UP")   & (merged["trend_strength_score_mtf"] >= mtf_min),
        (merged["trend_direction_mtf"] == "DOWN")  & (merged["trend_strength_score_mtf"] >= mtf_min),
    ]
    merged["mtf_structure_bias"] = np.select(mtf_conds, ["LONG_BIAS", "SHORT_BIAS"], default="NEUTRAL")

    # ── 6. LTF direction (already in trend_direction_ltf) ─────────────────
    merged["ltf_direction"] = merged["trend_direction_ltf"]

    # ── 7. Alignment state (vectorised) ───────────────────────────────────
    # Map everything to UP / DOWN / NEUTRAL
    def _simple(series: pd.Series, mapping: dict[str, str]) -> pd.Series:
        return series.map(mapping).fillna("NEUTRAL")

    h_simple = _simple(merged["htf_bias"],           {"UP": "UP", "DOWN": "DOWN", "RANGE": "NEUTRAL"})
    m_simple = _simple(merged["mtf_structure_bias"],  {"LONG_BIAS": "UP", "SHORT_BIAS": "DOWN", "NEUTRAL": "NEUTRAL"})
    l_simple = _simple(merged["ltf_direction"],       {"UP": "UP", "DOWN": "DOWN", "NEUTRAL": "NEUTRAL"})

    ups   = (h_simple == "UP").astype(int)   + (m_simple == "UP").astype(int)   + (l_simple == "UP").astype(int)
    downs = (h_simple == "DOWN").astype(int) + (m_simple == "DOWN").astype(int) + (l_simple == "DOWN").astype(int)

    state_conds = [
        ups == 3,
        downs == 3,
        (ups >= 2) & (downs == 0),
        (downs >= 2) & (ups == 0),
        (ups > 0) & (downs > 0),
    ]
    state_choices = [
        "FULL_ALIGN_UP",
        "FULL_ALIGN_DOWN",
        "PARTIAL_ALIGN_UP",
        "PARTIAL_ALIGN_DOWN",
        "CONFLICT",
    ]
    merged["mtf_alignment_state"] = np.select(state_conds, state_choices, default="WEAK_ALIGN")

    # ── 8. Alignment score ────────────────────────────────────────────────
    sc = config.alignment_scores
    score_map = {
        "FULL_ALIGN_UP":    sc.full_align,
        "FULL_ALIGN_DOWN":  sc.full_align,
        "PARTIAL_ALIGN_UP":  sc.partial_align,
        "PARTIAL_ALIGN_DOWN": sc.partial_align,
        "CONFLICT":         sc.conflict,
        "WEAK_ALIGN":       sc.weak_align,
    }
    base = merged["mtf_alignment_state"].map(score_map)
    avg_str = (
        merged["trend_strength_score_htf"] +
        merged["trend_strength_score_mtf"] +
        merged["trend_strength_score_ltf"]
    ) / 3.0

    merged["mtf_alignment_score"] = (
        base * (0.5 + 0.5 * avg_str / 100.0)
    ).clip(0.0, 100.0).round(2)

    return merged
