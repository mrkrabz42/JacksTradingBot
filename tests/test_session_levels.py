"""Tests for bot.liquidity.session_levels.add_session_high_low()."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bot.liquidity.session_levels import add_session_high_low


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal test DataFrame from a list of row dicts."""
    df = pd.DataFrame(rows)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    return df


def _sample_df() -> pd.DataFrame:
    """Two-day frame with Asia/London/NY + one OUTSIDE bar per day."""
    return _make_df([
        # Day 1 — Asia
        {"timestamp_utc": "2026-02-10 01:00:00+00:00", "high": 501, "low": 499, "close": 500, "session": "ASIA"},
        {"timestamp_utc": "2026-02-10 02:00:00+00:00", "high": 503, "low": 498, "close": 501, "session": "ASIA"},
        # Day 1 — London
        {"timestamp_utc": "2026-02-10 07:00:00+00:00", "high": 505, "low": 497, "close": 502, "session": "LONDON"},
        {"timestamp_utc": "2026-02-10 08:00:00+00:00", "high": 507, "low": 496, "close": 503, "session": "LONDON"},
        # Day 1 — NY
        {"timestamp_utc": "2026-02-10 14:00:00+00:00", "high": 510, "low": 500, "close": 507, "session": "NY"},
        {"timestamp_utc": "2026-02-10 15:00:00+00:00", "high": 508, "low": 502, "close": 506, "session": "NY"},
        # Day 1 — OUTSIDE
        {"timestamp_utc": "2026-02-10 22:00:00+00:00", "high": 506, "low": 503, "close": 505, "session": "OUTSIDE"},
        # Day 2 — Asia (different extremes)
        {"timestamp_utc": "2026-02-11 01:00:00+00:00", "high": 512, "low": 508, "close": 510, "session": "ASIA"},
        {"timestamp_utc": "2026-02-11 02:00:00+00:00", "high": 515, "low": 507, "close": 513, "session": "ASIA"},
        # Day 2 — London
        {"timestamp_utc": "2026-02-11 07:00:00+00:00", "high": 520, "low": 509, "close": 515, "session": "LONDON"},
        # Day 2 — NY
        {"timestamp_utc": "2026-02-11 14:00:00+00:00", "high": 525, "low": 511, "close": 522, "session": "NY"},
        # Day 2 — OUTSIDE
        {"timestamp_utc": "2026-02-11 22:00:00+00:00", "high": 522, "low": 518, "close": 520, "session": "OUTSIDE"},
    ])


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_output_columns_present():
    df = add_session_high_low(_sample_df())
    expected = [
        "session_high", "session_low",
        "session_high_asia", "session_low_asia",
        "session_high_london", "session_low_london",
        "session_high_ny", "session_low_ny",
    ]
    for col in expected:
        assert col in df.columns, f"Missing column: {col}"


def test_session_high_low_correct():
    """Each bar should carry its own session's max/min for that day."""
    df = add_session_high_low(_sample_df())

    # Day 1 Asia bars — max high is 503, min low is 498
    asia_d1 = df[(df["session"] == "ASIA") & (df["timestamp_utc"].dt.date.astype(str) == "2026-02-10")]
    assert (asia_d1["session_high"] == 503).all()
    assert (asia_d1["session_low"] == 498).all()

    # Day 1 London bars — max high 507, min low 496
    lon_d1 = df[(df["session"] == "LONDON") & (df["timestamp_utc"].dt.date.astype(str) == "2026-02-10")]
    assert (lon_d1["session_high"] == 507).all()
    assert (lon_d1["session_low"] == 496).all()

    # Day 1 NY bars — max high 510, min low 500
    ny_d1 = df[(df["session"] == "NY") & (df["timestamp_utc"].dt.date.astype(str) == "2026-02-10")]
    assert (ny_d1["session_high"] == 510).all()
    assert (ny_d1["session_low"] == 500).all()


def test_per_session_columns_correct():
    """Per-session-type columns should match known session extremes for each day."""
    df = add_session_high_low(_sample_df())
    d1 = df[df["timestamp_utc"].dt.date.astype(str) == "2026-02-10"]
    d2 = df[df["timestamp_utc"].dt.date.astype(str) == "2026-02-11"]

    # Day 1
    assert (d1["session_high_asia"]   == 503).all()
    assert (d1["session_low_asia"]    == 498).all()
    assert (d1["session_high_london"] == 507).all()
    assert (d1["session_low_london"]  == 496).all()
    assert (d1["session_high_ny"]     == 510).all()
    assert (d1["session_low_ny"]      == 500).all()

    # Day 2
    assert (d2["session_high_asia"]   == 515).all()
    assert (d2["session_low_asia"]    == 507).all()
    assert (d2["session_high_london"] == 520).all()
    assert (d2["session_low_london"]  == 509).all()
    assert (d2["session_high_ny"]     == 525).all()
    assert (d2["session_low_ny"]      == 511).all()


def test_outside_bars_are_nan():
    """Bars with session='OUTSIDE' should have NaN for session_high/session_low."""
    df = add_session_high_low(_sample_df())
    outside = df[df["session"] == "OUTSIDE"]
    assert outside["session_high"].isna().all(), "OUTSIDE bars should have NaN session_high"
    assert outside["session_low"].isna().all(),  "OUTSIDE bars should have NaN session_low"


def test_multi_day_isolation():
    """Day 1 Asia high must differ from Day 2 Asia high — sessions are independent."""
    df = add_session_high_low(_sample_df())
    asia = df[df["session"] == "ASIA"]
    d1_highs = asia[asia["timestamp_utc"].dt.date.astype(str) == "2026-02-10"]["session_high_asia"].unique()
    d2_highs = asia[asia["timestamp_utc"].dt.date.astype(str) == "2026-02-11"]["session_high_asia"].unique()
    assert d1_highs[0] != d2_highs[0], "Each day's Asia high should be independent"


def test_missing_required_column_raises():
    df = _make_df([{"timestamp_utc": "2026-02-10 01:00:00+00:00", "high": 500, "low": 498, "session": "ASIA"}])
    df = df.drop(columns=["low"])
    with pytest.raises(ValueError, match="missing required columns"):
        add_session_high_low(df)


def test_single_session_only():
    """If only one session label is present, the other per-session columns should still be NaN."""
    df = _make_df([
        {"timestamp_utc": "2026-02-10 01:00:00+00:00", "high": 501, "low": 499, "close": 500, "session": "ASIA"},
        {"timestamp_utc": "2026-02-10 02:00:00+00:00", "high": 503, "low": 498, "close": 501, "session": "ASIA"},
    ])
    result = add_session_high_low(df)
    assert "session_high_london" in result.columns
    assert result["session_high_london"].isna().all()
    assert "session_high_ny" in result.columns
    assert result["session_high_ny"].isna().all()
    # Asia columns should be populated
    assert (result["session_high_asia"] == 503).all()
    assert (result["session_low_asia"] == 498).all()
