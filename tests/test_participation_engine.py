"""Tests for bot.volume.participation_engine."""
from __future__ import annotations

import pandas as pd
import pytest

from bot.structure.config import ParticipationConfig
from bot.volume.participation_engine import apply_participation_metrics


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal DataFrame with timestamp_utc + volume."""
    df = pd.DataFrame(rows)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    return df


def _build_multi_day(
    days: int,
    buckets_per_day: int = 78,  # ~6.5 h of 5-min bars
    base_vol: float = 1_000_000.0,
    today_vol: float | None = None,
) -> pd.DataFrame:
    """
    Build a synthetic DataFrame spanning `days` trading days.

    Historical days (all except the last) have ``base_vol`` for every bucket.
    The last (current) day uses ``today_vol`` if provided, else ``base_vol``.
    """
    rows = []
    start_hour = 13  # 13:30 UTC ≈ NYSE open
    for day_offset in range(days):
        date_str = f"2026-01-{1 + day_offset:02d}"
        vol = base_vol if (day_offset < days - 1 or today_vol is None) else today_vol
        for b in range(buckets_per_day):
            minute = start_hour * 60 + b * 5
            h = minute // 60
            m = minute % 60
            ts = f"{date_str}T{h:02d}:{m:02d}:00+00:00"
            rows.append({"timestamp_utc": ts, "volume": vol})
    return _make_df(rows)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_output_columns_present():
    """All three new columns must exist after apply_participation_metrics."""
    df = _build_multi_day(days=5)
    cfg = ParticipationConfig(min_bars_per_bucket=1)
    result = apply_participation_metrics(df, cfg)
    for col in ("rvol_ratio", "participation_state", "volume_spike_flag"):
        assert col in result.columns, f"Missing column: {col}"


def test_rvol_ratio_correct():
    """Today's volume at 2× baseline should produce rvol_ratio ≈ 2.0."""
    base_vol = 1_000_000.0
    df = _build_multi_day(days=6, base_vol=base_vol, today_vol=base_vol * 2)
    cfg = ParticipationConfig(min_bars_per_bucket=1)
    result = apply_participation_metrics(df, cfg)

    today_date = result["timestamp_utc"].dt.date.max()
    today_rows = result[result["timestamp_utc"].dt.date == today_date]

    assert len(today_rows) > 0
    # All today bars that have a valid baseline should be ≈ 2.0
    for _, row in today_rows.iterrows():
        assert abs(row["rvol_ratio"] - 2.0) < 0.01, (
            f"Expected rvol_ratio ≈ 2.0, got {row['rvol_ratio']}"
        )


def test_participation_state_thresholds():
    """Bars at threshold boundaries should classify correctly."""
    cfg = ParticipationConfig(
        low_threshold=0.7,
        high_threshold=1.5,
        extreme_threshold=3.0,
        spike_threshold=3.0,
        min_bars_per_bucket=1,
    )
    base_vol = 1_000_000.0

    # Build history (5 days) + today with various multiples
    rows = []
    for day in range(5):
        date_str = f"2026-02-{1 + day:02d}"
        ts = f"{date_str}T14:00:00+00:00"
        rows.append({"timestamp_utc": ts, "volume": base_vol})

    test_cases = [
        (base_vol * 0.5,  "LOW_ACTIVITY"),
        (base_vol * 0.7,  "NORMAL"),           # exactly at boundary → NORMAL
        (base_vol * 1.0,  "NORMAL"),
        (base_vol * 1.5,  "ELEVATED"),         # exactly at high_threshold → ELEVATED
        (base_vol * 2.0,  "ELEVATED"),
        (base_vol * 3.0,  "EXTREME"),          # exactly at extreme_threshold → EXTREME
        (base_vol * 5.0,  "EXTREME"),
    ]

    for vol_mult, expected_state in test_cases:
        today_rows = [{"timestamp_utc": "2026-02-06T14:00:00+00:00", "volume": vol_mult}]
        df = _make_df(rows + today_rows)
        result = apply_participation_metrics(df, cfg)
        today = result[result["timestamp_utc"].dt.date.astype(str) == "2026-02-06"]
        assert len(today) == 1
        got = today.iloc[0]["participation_state"]
        assert got == expected_state, (
            f"vol_mult={vol_mult / base_vol:.1f}x → expected {expected_state}, got {got}"
        )


def test_spike_flag_flips():
    """spike_flag is False just below threshold, True at threshold."""
    cfg = ParticipationConfig(spike_threshold=3.0, min_bars_per_bucket=1)
    base_vol = 1_000_000.0

    history = [
        {"timestamp_utc": f"2026-02-{1+d:02d}T14:00:00+00:00", "volume": base_vol}
        for d in range(5)
    ]

    # Just below threshold
    df_below = _make_df(history + [{"timestamp_utc": "2026-02-06T14:00:00+00:00", "volume": base_vol * 2.999}])
    result_below = apply_participation_metrics(df_below, cfg)
    today_below = result_below[result_below["timestamp_utc"].dt.date.astype(str) == "2026-02-06"]
    assert not today_below.iloc[0]["volume_spike_flag"], "Expected no spike below threshold"

    # Exactly at threshold
    df_at = _make_df(history + [{"timestamp_utc": "2026-02-06T14:00:00+00:00", "volume": base_vol * 3.0}])
    result_at = apply_participation_metrics(df_at, cfg)
    today_at = result_at[result_at["timestamp_utc"].dt.date.astype(str) == "2026-02-06"]
    assert today_at.iloc[0]["volume_spike_flag"], "Expected spike at threshold"


def test_insufficient_history_fallback():
    """Single trading day → fallback: rvol=1.0, state=NORMAL, spike=False."""
    rows = [
        {"timestamp_utc": f"2026-02-01T{14 + i}:00:00+00:00", "volume": 500_000.0}
        for i in range(6)
    ]
    df = _make_df(rows)
    cfg = ParticipationConfig(min_bars_per_bucket=1)
    result = apply_participation_metrics(df, cfg)

    assert (result["rvol_ratio"] == 1.0).all()
    assert (result["participation_state"] == "NORMAL").all()
    assert (result["volume_spike_flag"] == False).all()


def test_low_sample_count_fallback():
    """Buckets with fewer samples than min_bars_per_bucket → rvol falls back to 1.0."""
    # 5 days, 1 bar per bucket per day, but min_bars_per_bucket=10
    df = _build_multi_day(days=6, buckets_per_day=1, base_vol=1_000_000.0, today_vol=5_000_000.0)
    cfg = ParticipationConfig(min_bars_per_bucket=10)
    result = apply_participation_metrics(df, cfg)

    today_date = result["timestamp_utc"].dt.date.max()
    today_rows = result[result["timestamp_utc"].dt.date == today_date]

    # With only 5 historical samples and min=10, all buckets fall back to 1.0
    assert (today_rows["rvol_ratio"] == 1.0).all(), (
        f"Expected rvol_ratio=1.0 due to low sample count, got: {today_rows['rvol_ratio'].tolist()}"
    )
