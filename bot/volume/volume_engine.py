"""Volume Engine — VWAP, Volume Profile (POC/VAH/VAL), and acceptance/rejection classification."""
from __future__ import annotations

import numpy as np
import pandas as pd

from bot.structure.config import VolumeConfig


# ── Public interface ──────────────────────────────────────────────────────────

def compute_vwap_and_profile(
    df: pd.DataFrame, config: VolumeConfig | None = None
) -> pd.DataFrame:
    """Add ``vwap``, ``poc``, ``vah``, ``val`` columns to *df*.

    Expects columns: ``high``, ``low``, ``close``, ``volume``
    (or ``h``, ``l``, ``c``, ``v``).
    Returns a copy with the new columns appended.

    Config options:
    - ``profile_mode = "session"`` — reset VWAP/profile at each calendar day.
    - ``profile_mode = "rolling"`` — use a sliding window of ``profile_window_bars``.
    """
    if config is None:
        config = VolumeConfig()

    out = df.copy()

    h = out["high"] if "high" in out.columns else out["h"]
    l = out["low"] if "low" in out.columns else out["l"]
    c = out["close"] if "close" in out.columns else out["c"]
    v = out["volume"] if "volume" in out.columns else out["v"]

    typical_price = (h + l + c) / 3

    if config.profile_mode == "session":
        return _compute_session_vwap_and_profile(out, typical_price, v, config)
    else:
        return _compute_rolling_vwap_and_profile(out, typical_price, v, config)


def classify_volume_state_series(
    df: pd.DataFrame, config: VolumeConfig | None = None
) -> pd.Series:
    """Return a Series of volume/value state labels per bar.

    States: ``IN_VALUE``, ``ACCEPTING_ABOVE``, ``ACCEPTING_BELOW``,
    ``REJECTING_ABOVE``, ``REJECTING_BELOW``.

    Requires *df* to have ``poc``, ``vah``, ``val`` columns (or they will be
    computed automatically from ``close``/``volume``).
    """
    if config is None:
        config = VolumeConfig()

    if "vwap" not in df.columns:
        df = compute_vwap_and_profile(df, config)

    acc_bars = config.acceptance_min_bars
    c = df["close"].values if "close" in df.columns else df["c"].values
    poc_vals = df["poc"].values
    vah_vals = df["vah"].values
    val_vals = df["val"].values

    n = len(df)
    states: list[str] = []
    above_counter = 0
    below_counter = 0

    for i in range(n):
        close = c[i]
        p = poc_vals[i]
        h = vah_vals[i]
        l = val_vals[i]

        if np.isnan(p) or np.isnan(h) or np.isnan(l):
            above_counter = 0
            below_counter = 0
            states.append("IN_VALUE")
            continue

        in_value = l <= close <= h
        above_value = close > h
        below_value = close < l

        if in_value:
            above_counter = 0
            below_counter = 0
            states.append("IN_VALUE")
        elif above_value:
            above_counter += 1
            below_counter = 0
            states.append("ACCEPTING_ABOVE" if above_counter >= acc_bars else "REJECTING_ABOVE")
        elif below_value:
            below_counter += 1
            above_counter = 0
            states.append("ACCEPTING_BELOW" if below_counter >= acc_bars else "REJECTING_BELOW")
        else:
            states.append("IN_VALUE")

    return pd.Series(states, index=df.index, name="volume_state")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _compute_session_vwap_and_profile(
    df: pd.DataFrame,
    typical_price: pd.Series,
    volume: pd.Series,
    config: VolumeConfig,
) -> pd.DataFrame:
    """Session-based VWAP and profile (reset per calendar day)."""
    out = df.copy()

    # Determine which day each bar belongs to
    if isinstance(df.index, pd.DatetimeIndex):
        dates = df.index.normalize().values
    elif "time" in df.columns:
        dates = pd.to_datetime(df["time"]).dt.normalize().values
    else:
        dates = np.zeros(len(df))  # treat as single session

    tp_vals = typical_price.values
    vol_vals = volume.values

    vwap_arr = np.full(len(df), np.nan)
    poc_arr = np.full(len(df), np.nan)
    vah_arr = np.full(len(df), np.nan)
    val_arr = np.full(len(df), np.nan)

    unique_dates: list = list(dict.fromkeys(dates))  # preserves insertion order

    for date in unique_dates:
        mask = dates == date
        idxs = np.where(mask)[0]
        if len(idxs) == 0:
            continue

        tp_win = tp_vals[idxs]
        vol_win = vol_vals[idxs]

        # Session VWAP — cumulative
        cumnum = np.cumsum(tp_win * vol_win)
        cumden = np.cumsum(vol_win)
        with np.errstate(divide="ignore", invalid="ignore"):
            session_vwap = np.where(cumden > 0, cumnum / cumden, np.nan)
        vwap_arr[idxs] = session_vwap

        # Volume profile for the whole session (forward-filled to each bar)
        stats = _compute_profile_stats(tp_win, vol_win, config.num_profile_bins, config.value_area_fraction)
        if stats is not None:
            poc_arr[idxs] = stats["poc"]
            vah_arr[idxs] = stats["vah"]
            val_arr[idxs] = stats["val"]

    out["vwap"] = vwap_arr
    out["poc"] = poc_arr
    out["vah"] = vah_arr
    out["val"] = val_arr
    return out


def _compute_rolling_vwap_and_profile(
    df: pd.DataFrame,
    typical_price: pd.Series,
    volume: pd.Series,
    config: VolumeConfig,
) -> pd.DataFrame:
    """Rolling VWAP and profile over a sliding window."""
    out = df.copy()

    n = len(df)
    window = config.profile_window_bars
    tp_vals = typical_price.values
    vol_vals = volume.values

    vwap_arr = np.full(n, np.nan)
    poc_arr = np.full(n, np.nan)
    vah_arr = np.full(n, np.nan)
    val_arr = np.full(n, np.nan)

    for i in range(n):
        start = max(0, i - window + 1)
        tp_win = tp_vals[start : i + 1]
        vol_win = vol_vals[start : i + 1]

        denom = vol_win.sum()
        if denom > 0:
            vwap_arr[i] = (tp_win * vol_win).sum() / denom

        if len(tp_win) >= 2:
            stats = _compute_profile_stats(tp_win, vol_win, config.num_profile_bins, config.value_area_fraction)
            if stats is not None:
                poc_arr[i] = stats["poc"]
                vah_arr[i] = stats["vah"]
                val_arr[i] = stats["val"]

    out["vwap"] = vwap_arr
    out["poc"] = poc_arr
    out["vah"] = vah_arr
    out["val"] = val_arr
    return out


def _compute_profile_stats(
    tp: np.ndarray,
    vol: np.ndarray,
    num_bins: int,
    value_area_fraction: float,
) -> dict[str, float] | None:
    """Compute POC, VAH, VAL for a given typical-price / volume window."""
    if len(tp) == 0 or vol.sum() == 0:
        return None

    price_min = tp.min()
    price_max = tp.max()

    if price_min == price_max:
        return {"poc": float(price_min), "vah": float(price_min), "val": float(price_min)}

    bins = np.linspace(price_min, price_max, num_bins + 1)
    bin_indices = np.digitize(tp, bins) - 1
    bin_indices = np.clip(bin_indices, 0, num_bins - 1)

    bin_volumes = np.zeros(num_bins)
    for bi, vi in zip(bin_indices, vol):
        bin_volumes[bi] += vi

    poc_bin = int(np.argmax(bin_volumes))
    poc = float(bins[poc_bin])

    total_vol = bin_volumes.sum()
    target = total_vol * value_area_fraction

    sorted_bins = list(np.argsort(bin_volumes)[::-1])
    cum_vol = 0.0
    va_bins: list[int] = []
    for bi in sorted_bins:
        if cum_vol >= target:
            break
        va_bins.append(bi)
        cum_vol += bin_volumes[bi]

    if not va_bins:
        return {"poc": poc, "vah": poc, "val": poc}

    vah = float(bins[max(va_bins)])
    val = float(bins[min(va_bins)])

    return {"poc": poc, "vah": vah, "val": val}
