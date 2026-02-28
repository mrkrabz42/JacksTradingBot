"""Tests for bot/context/context_formatter.py — 4 scenario tests, no API calls."""
from __future__ import annotations

import pytest

from bot.context.context_formatter import build_context_flags, build_environment_summary
from bot.structure.config import ContextFormatterConfig


# ── Shared config ─────────────────────────────────────────────────────────────

CFG = ContextFormatterConfig()


# ── Scenario 1: Strong Bull A+ Setup ─────────────────────────────────────────

STRONG_BULL_SNAP = {
    "regime": "TREND",
    "trend_direction": "UP",
    "trend_strength_score": 80.0,
    "volatility_state": "MEDIUM",
    "liquidity_draw_direction": "ABOVE",
    "liquidity_magnet_score": 75.0,
    "dist_session_high": 1.5,  # not near session high
    "dist_session_low": None,
    "mtf_alignment_state": "FULL_ALIGN_UP",
    "mtf_alignment_score": 90.0,
    "participation_state": "ELEVATED",
    "rvol_ratio": 1.4,
    "volume_state": "IN_VALUE",
    "volume_spike_flag": False,
    "breakout_type": "CONTINUATION",
    "breakout_quality_score": 78.0,
    "setup_grade": "A_PLUS_SETUP",
    "confluence_score": 88.0,
    "bar_trade_bias": "LONG",
    "session": "NY",
}

STRONG_BULL_EVENT = {
    "direction": "BULL",
    "setup_grade": "A_PLUS_SETUP",
    "confluence_score": 88.0,
}


def test_strong_bull_aplus():
    flags = build_context_flags(STRONG_BULL_SNAP, STRONG_BULL_EVENT, CFG)
    assert "TRENDING UP" in flags
    assert "LIQUIDITY PULL ABOVE" in flags
    assert "MTF ALIGN UP" in flags
    assert "BREAKOUT CONTINUATION" in flags
    assert "A+ CONTEXT" in flags
    assert "NEW YORK SESSION" in flags
    assert len(flags) <= CFG.max_flags

    summary = build_environment_summary(STRONG_BULL_SNAP, STRONG_BULL_EVENT, CFG)
    assert "uptrend" in summary.lower()
    assert "liquidity" in summary.lower()
    assert "alignment" in summary.lower() or "multi-timeframe" in summary.lower()
    assert "A+" in summary


# ── Scenario 2: Bear B setup ──────────────────────────────────────────────────

BEAR_B_SNAP = {
    "regime": "TREND",
    "trend_direction": "DOWN",
    "trend_strength_score": 72.0,
    "volatility_state": "MEDIUM",
    "liquidity_draw_direction": "BELOW",
    "liquidity_magnet_score": 55.0,
    "dist_session_high": None,
    "dist_session_low": -1.2,
    "mtf_alignment_state": "PARTIAL_ALIGN_DOWN",
    "mtf_alignment_score": 58.0,
    "participation_state": "LOW_ACTIVITY",
    "rvol_ratio": 0.6,
    "volume_state": "IN_VALUE",
    "volume_spike_flag": False,
    "breakout_type": "UNCLEAR",
    "breakout_quality_score": 35.0,
    "setup_grade": "NO_TRADE",
    "confluence_score": 42.0,
    "bar_trade_bias": "SHORT",
    "session": "NY",
}

BEAR_B_EVENT = {
    "direction": "BEAR",
    "setup_grade": "NO_TRADE",
    "confluence_score": 42.0,
}


def test_bear_b_setup():
    flags = build_context_flags(BEAR_B_SNAP, BEAR_B_EVENT, CFG)
    assert "TRENDING DOWN" in flags
    assert "MILD LIQUIDITY PULL BELOW" in flags
    assert "QUIET TAPE" in flags

    summary = build_environment_summary(BEAR_B_SNAP, BEAR_B_EVENT, CFG)
    assert "downtrend" in summary.lower()
    assert "below" in summary.lower()


# ── Scenario 3: Range / Low Volatility ───────────────────────────────────────

RANGE_SNAP = {
    "regime": "RANGE",
    "trend_direction": "NEUTRAL",
    "trend_strength_score": 20.0,
    "volatility_state": "LOW",
    "liquidity_draw_direction": "NEUTRAL",
    "liquidity_magnet_score": 15.0,
    "dist_session_high": None,
    "dist_session_low": None,
    "mtf_alignment_state": "WEAK_ALIGN",
    "mtf_alignment_score": 35.0,
    "participation_state": "NORMAL",
    "rvol_ratio": 1.0,
    "volume_state": "IN_VALUE",
    "volume_spike_flag": False,
    "breakout_type": None,
    "breakout_quality_score": None,
    "setup_grade": "MEDIUM_SETUP",
    "confluence_score": 58.0,
    "bar_trade_bias": "NEUTRAL",
    "session": "LONDON",
}


def test_range_low_volatility():
    flags = build_context_flags(RANGE_SNAP, {}, CFG)
    assert "RANGE-BOUND" in flags
    assert "LOW VOLATILITY" in flags
    # No trending flag
    assert "TRENDING UP" not in flags
    assert "TRENDING DOWN" not in flags


# ── Scenario 4: Missing fields graceful ──────────────────────────────────────

SPARSE_SNAP = {
    "regime": "TREND",
    "trend_direction": "UP",
}


def test_missing_fields_graceful():
    flags = build_context_flags(SPARSE_SNAP, None, CFG)
    assert isinstance(flags, list)

    summary = build_environment_summary(SPARSE_SNAP, None, CFG)
    assert isinstance(summary, str)
