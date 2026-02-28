"""Participation / Relative Volume (RVOL) Engine.

Computes time-of-day adjusted relative volume, participation state,
and volume spike flag for each bar in a snapshot DataFrame.

Usage
-----
    from bot.volume.participation_engine import apply_participation_metrics

    df = apply_participation_metrics(df)   # uses default ParticipationConfig
    # df now has columns: rvol_ratio, participation_state, volume_spike_flag
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from bot.structure.config import ParticipationConfig


def apply_participation_metrics(
    df: pd.DataFrame,
    config: ParticipationConfig | None = None,
) -> pd.DataFrame:
    """Compute RVOL-based participation metrics for every bar in *df*.

    Parameters
    ----------
    df:
        DataFrame with at least ``timestamp_utc`` and ``volume`` columns.
        ``timestamp_utc`` must be parseable by ``pd.to_datetime``.
    config:
        Optional config; defaults to ``ParticipationConfig()`` if not supplied.

    Returns
    -------
    *df* with three new columns appended (in-place copy):

    ``rvol_ratio``
        Current bar volume divided by the time-of-day baseline mean.
        1.0 when no baseline is available.
    ``participation_state``
        One of ``"LOW_ACTIVITY"``, ``"NORMAL"``, ``"ELEVATED"``, ``"EXTREME"``.
    ``volume_spike_flag``
        ``True`` when ``rvol_ratio >= config.spike_threshold``.
    """
    if config is None:
        config = ParticipationConfig()

    df = df.copy()

    # ── Validate required columns ─────────────────────────────────────────────
    for col in ("timestamp_utc", "volume"):
        if col not in df.columns:
            raise ValueError(
                f"apply_participation_metrics: required column '{col}' not found. "
                f"Available: {list(df.columns)}"
            )

    # ── Normalize timestamp_utc to UTC ────────────────────────────────────────
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)

    # ── Derive helper columns ─────────────────────────────────────────────────
    bsz = config.bucket_size_minutes
    minutes = df["timestamp_utc"].dt.hour * 60 + df["timestamp_utc"].dt.minute
    df["_tod_bucket"] = (minutes // bsz) * bsz
    df["_trading_date"] = df["timestamp_utc"].dt.date

    # ── Identify trading dates and split historical / current ─────────────────
    all_dates_sorted = sorted(df["_trading_date"].unique())

    if len(all_dates_sorted) < 2:
        # Insufficient history — fall back to neutral values
        logger.warning(
            "apply_participation_metrics: only 1 distinct trading date — "
            "insufficient history for RVOL baseline; defaulting to neutral."
        )
        df["rvol_ratio"] = 1.0
        df["participation_state"] = "NORMAL"
        df["volume_spike_flag"] = False
        df.drop(columns=["_tod_bucket", "_trading_date"], inplace=True)
        return df

    # Exclude the last (current) date from the baseline
    historical_dates = all_dates_sorted[:-1]
    # Take only the last `lookback_days` historical dates
    historical_dates = historical_dates[-config.lookback_days :]

    # ── Build baseline from historical bars ───────────────────────────────────
    hist_mask = df["_trading_date"].isin(set(historical_dates))
    hist_df = df.loc[hist_mask, ["_trading_date", "_tod_bucket", "volume"]].copy()

    # One volume per (date, bucket) — take last value to handle any duplicates
    per_day_bucket = (
        hist_df.groupby(["_trading_date", "_tod_bucket"])["volume"]
        .last()
        .reset_index()
    )

    # Aggregate across days: mean + count per bucket
    bucket_stats = (
        per_day_bucket.groupby("_tod_bucket")["volume"]
        .agg(mean_vol="mean", count="count")
        .reset_index()
    )

    # Discard buckets with fewer samples than min_bars_per_bucket
    valid_buckets = bucket_stats[
        bucket_stats["count"] >= config.min_bars_per_bucket
    ].set_index("_tod_bucket")["mean_vol"]

    # ── Merge baseline onto full DataFrame ────────────────────────────────────
    df["_baseline_vol"] = df["_tod_bucket"].map(valid_buckets)

    # ── Vectorised RVOL ratio ─────────────────────────────────────────────────
    has_baseline = df["_baseline_vol"].notna() & (df["_baseline_vol"] > 0)
    df["rvol_ratio"] = np.where(
        has_baseline,
        df["volume"] / df["_baseline_vol"],
        1.0,
    )
    df["rvol_ratio"] = df["rvol_ratio"].round(3)

    # ── Participation state ───────────────────────────────────────────────────
    conditions = [
        df["rvol_ratio"] < config.low_threshold,
        df["rvol_ratio"] < config.high_threshold,
        df["rvol_ratio"] < config.extreme_threshold,
    ]
    choices = ["LOW_ACTIVITY", "NORMAL", "ELEVATED"]
    df["participation_state"] = np.select(conditions, choices, default="EXTREME")

    # ── Volume spike flag ─────────────────────────────────────────────────────
    df["volume_spike_flag"] = df["rvol_ratio"] >= config.spike_threshold

    # ── Drop internal helpers ─────────────────────────────────────────────────
    df.drop(columns=["_tod_bucket", "_trading_date", "_baseline_vol"], inplace=True)

    return df
