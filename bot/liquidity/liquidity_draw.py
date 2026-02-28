"""Liquidity Proximity / Draw Module.

Computes per-bar liquidity reference levels, scores their proximity,
and classifies which direction price is most likely drawn toward.

Public interface
----------------
compute_liquidity_reference_levels(df, swings, config) -> pd.DataFrame
    Adds session_high/low, PDH/PDL, nearest_equal_high/low, and all
    distance columns to *df*.

classify_liquidity_draw_series(df, config) -> pd.DataFrame
    Requires the distance columns above. Adds:
    - liquidity_draw_direction : 'ABOVE' | 'BELOW' | 'NEUTRAL'
    - liquidity_magnet_score   : float 0-100
    - up_liquidity_score       : float 0-100  (debugging)
    - down_liquidity_score     : float 0-100  (debugging)
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from bot.structure.config import LiquidityDrawConfig
from bot.structure.swing_engine import Swing


# ── Public interface ──────────────────────────────────────────────────────────

def compute_liquidity_reference_levels(
    df: pd.DataFrame,
    swings: List[Swing],
    config: LiquidityDrawConfig | None = None,
) -> pd.DataFrame:
    """Attach key reference levels and signed distances to every bar in *df*.

    Parameters
    ----------
    df:
        Must contain: ``time``, ``high``, ``low``, ``close``.
        Optionally: ``atr``, ``poc``, ``vah``, ``val`` (from Volume Engine).
    swings:
        Output of ``bot.structure.swing_engine.detect_swings()``.
    config:
        ``LiquidityDrawConfig``; defaults are used when ``None``.

    Returns
    -------
    pd.DataFrame with new columns:
        session_high, session_low,
        pdh, pdl,
        nearest_equal_high, nearest_equal_low,
        dist_session_high, dist_session_low,
        dist_pdh, dist_pdl,
        dist_equal_high, dist_equal_low,
        dist_poc, dist_vah, dist_val  (when poc/vah/val already present).
    """
    if config is None:
        config = LiquidityDrawConfig()

    out = df.copy()

    # Ensure time column is datetime
    if not pd.api.types.is_datetime64_any_dtype(out["time"]):
        out["time"] = pd.to_datetime(out["time"])

    close = out["close"]
    atr = out["atr"] if "atr" in out.columns else pd.Series(np.nan, index=out.index)

    # Compute date_key once — used in both session and PDH/PDL blocks
    date_key = out["time"].dt.date

    # ── 1. Session high / low ─────────────────────────────────────────────
    if "session_high" not in out.columns or "session_low" not in out.columns:
        # Fallback: whole-day high/low (backward compatible when
        # add_session_high_low() has not been run first)
        grouped = out.groupby(date_key)
        out["session_high"] = grouped["high"].transform("max")
        out["session_low"]  = grouped["low"].transform("min")

    # ── 2. Previous day high / low (PDH / PDL) ──────────────────────────
    if "pdh" not in out.columns or "pdl" not in out.columns:
        daily = out.groupby(date_key).agg(
            day_high=("high", "max"),
            day_low=("low", "min"),
        )
        daily_shifted = daily.shift(1)
        date_series = out["time"].dt.date
        out["pdh"] = date_series.map(daily_shifted["day_high"])
        out["pdl"] = date_series.map(daily_shifted["day_low"])

    # ── 3. Nearest equal high / low (no look-ahead) ─────────────────────
    max_age = config.max_equal_level_age_bars
    close_arr = close.values
    n = len(out)

    equal_high_arr = np.full(n, np.nan)
    equal_low_arr  = np.full(n, np.nan)

    swing_highs = [(s["index"], s["price"]) for s in swings if s["type"] == "high"]
    swing_lows  = [(s["index"], s["price"]) for s in swings if s["type"] == "low"]

    for i in range(n):
        price = close_arr[i]

        above = [
            p for idx, p in swing_highs
            if 0 <= idx < i and (i - idx) <= max_age and p > price
        ]
        if above:
            equal_high_arr[i] = min(above)

        below = [
            p for idx, p in swing_lows
            if 0 <= idx < i and (i - idx) <= max_age and p < price
        ]
        if below:
            equal_low_arr[i] = max(below)

    out["nearest_equal_high"] = equal_high_arr
    out["nearest_equal_low"]  = equal_low_arr

    # ── 4. Distance columns (signed: positive = level above close) ───────
    def _dist(level: pd.Series) -> pd.Series:
        raw = level - close
        if config.dist_metric == "atr":
            safe_atr = atr.copy()
            safe_atr[safe_atr == 0] = np.nan
            return raw / safe_atr
        return raw / close  # percent

    out["dist_session_high"] = _dist(out["session_high"])
    out["dist_session_low"]  = _dist(out["session_low"])
    out["dist_pdh"]          = _dist(out["pdh"])
    out["dist_pdl"]          = _dist(out["pdl"])
    out["dist_equal_high"]   = _dist(pd.Series(equal_high_arr, index=out.index))
    out["dist_equal_low"]    = _dist(pd.Series(equal_low_arr,  index=out.index))

    if "poc" in out.columns:
        out["dist_poc"] = _dist(out["poc"])
    if "vah" in out.columns:
        out["dist_vah"] = _dist(out["vah"])
    if "val" in out.columns:
        out["dist_val"] = _dist(out["val"])

    return out


def classify_liquidity_draw_series(
    df: pd.DataFrame,
    config: LiquidityDrawConfig | None = None,
) -> pd.DataFrame:
    """Compute per-bar draw direction and magnet score.

    Expects the distance columns produced by
    ``compute_liquidity_reference_levels``. If they are absent, this
    function will raise a ``KeyError`` — call the reference-level function
    first.

    Returns
    -------
    pd.DataFrame with added columns:
        liquidity_draw_direction : 'ABOVE' | 'BELOW' | 'NEUTRAL'
        liquidity_magnet_score   : float 0-100
        up_liquidity_score       : float 0-100
        down_liquidity_score     : float 0-100
    """
    if config is None:
        config = LiquidityDrawConfig()

    out = df.copy()
    cols = set(out.columns)

    clip        = config.dist_clip_atr
    neutral_b   = config.neutral_band_ratio
    min_score   = config.min_magnet_score_for_signal
    w_sess      = config.weights.session_high_low
    w_pdh       = config.weights.pdh_pdl
    w_equal     = config.weights.equal_high_low
    w_vol       = config.weights.volume_magnets

    def _level_score(d: float) -> float:
        """Invert distance: closer = higher score (0–100)."""
        return (1.0 - min(abs(d), clip) / clip) * 100.0

    def _safe(val: object) -> float | None:
        """Return float or None if NaN/None."""
        if val is None:
            return None
        try:
            f = float(val)
            return None if np.isnan(f) else f
        except (TypeError, ValueError):
            return None

    directions: list[str] = []
    magnets:    list[float] = []
    up_list:    list[float] = []
    dn_list:    list[float] = []

    for i in range(len(out)):
        row = out.iloc[i]
        up = 0.0
        dn = 0.0

        # ── Session high / low ──────────────────────────────────────────
        sh = _safe(row.get("dist_session_high") if "dist_session_high" in cols else None)
        sl = _safe(row.get("dist_session_low")  if "dist_session_low"  in cols else None)
        if sh is not None and sh > 0:
            up += _level_score(sh) * w_sess
        if sl is not None and sl < 0:
            dn += _level_score(sl) * w_sess

        # ── PDH / PDL ───────────────────────────────────────────────────
        pdh = _safe(row.get("dist_pdh") if "dist_pdh" in cols else None)
        pdl = _safe(row.get("dist_pdl") if "dist_pdl" in cols else None)
        if pdh is not None and pdh > 0:
            up += _level_score(pdh) * w_pdh
        if pdl is not None and pdl < 0:
            dn += _level_score(pdl) * w_pdh

        # ── Equal high / low ────────────────────────────────────────────
        eh = _safe(row.get("dist_equal_high") if "dist_equal_high" in cols else None)
        el = _safe(row.get("dist_equal_low")  if "dist_equal_low"  in cols else None)
        if eh is not None and eh > 0:
            up += _level_score(eh) * w_equal
        if el is not None and el < 0:
            dn += _level_score(el) * w_equal

        # ── Volume magnets (POC / VAH / VAL) ────────────────────────────
        poc = _safe(row.get("dist_poc") if "dist_poc" in cols else None)
        vah = _safe(row.get("dist_vah") if "dist_vah" in cols else None)
        val = _safe(row.get("dist_val") if "dist_val" in cols else None)

        vol_up = 0.0
        vol_dn = 0.0
        if poc is not None:
            if poc > 0:
                vol_up = max(vol_up, _level_score(poc))
            elif poc < 0:
                vol_dn = max(vol_dn, _level_score(poc))
        if vah is not None and vah > 0:
            vol_up = max(vol_up, _level_score(vah))
        if val is not None and val < 0:
            vol_dn = max(vol_dn, _level_score(val))

        up += vol_up * w_vol
        dn += vol_dn * w_vol

        up = round(min(max(up, 0.0), 100.0), 2)
        dn = round(min(max(dn, 0.0), 100.0), 2)
        total = up + dn

        if total < min_score:
            direction = "NEUTRAL"
            magnet    = total
        elif up > dn * (1.0 + neutral_b):
            direction = "ABOVE"
            magnet    = up
        elif dn > up * (1.0 + neutral_b):
            direction = "BELOW"
            magnet    = dn
        else:
            direction = "NEUTRAL"
            magnet    = max(up, dn)

        directions.append(direction)
        magnets.append(round(min(magnet, 100.0), 2))
        up_list.append(up)
        dn_list.append(dn)

    out["liquidity_draw_direction"] = directions
    out["liquidity_magnet_score"]   = magnets
    out["up_liquidity_score"]       = up_list
    out["down_liquidity_score"]     = dn_list

    return out
