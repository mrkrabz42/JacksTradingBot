"""Unit tests for the MSS acceptance validator."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from bot.strategy.structure.acceptance import (
    AcceptanceResult,
    check_acceptance,
    validate_mss_acceptance,
)
from bot.strategy.structure.control_points import ControlPoint
from bot.strategy.structure.mss_detector import MSS


def _ts(minute: int) -> datetime:
    return datetime(2026, 2, 13, 14, minute, tzinfo=timezone.utc)


def _candle(minute: int, o: float, h: float, l: float, c: float) -> dict:
    return {"time": _ts(minute), "open": o, "high": h, "low": l, "close": c}


def _make_mss(direction: str, minute: int, cp_price: float) -> MSS:
    """Helper to build a minimal MSS for testing."""
    cp_type = "HIGH" if direction == "BULL" else "LOW"
    return MSS(
        id="MSS_T01",
        timestamp=_ts(minute),
        direction=direction,
        trigger_candle=_candle(minute, 100.0, 103.0, 100.0, 102.5),
        control_point=ControlPoint(price=cp_price, time=_ts(minute - 5), type=cp_type),
        displacement_quality=0.9,
        session_context="NY",
    )


class TestCheckAcceptance(unittest.TestCase):
    """Tests for the core check_acceptance function."""

    def test_bull_accepted_both_above(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        next_candles = [
            _candle(11, 102.0, 103.0, 101.5, 102.5),  # above 101
            _candle(12, 102.3, 103.5, 102.0, 103.0),   # above 101
        ]
        result = check_acceptance(mss, next_candles)
        self.assertTrue(result.is_accepted)
        self.assertEqual(result.checked_candles, 2)
        self.assertIsNone(result.rejection_reason)

    def test_bull_rejected_first_candle_below(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        next_candles = [
            _candle(11, 101.5, 102.0, 100.0, 100.5),  # closes below 101
            _candle(12, 101.0, 103.0, 101.0, 102.0),
        ]
        result = check_acceptance(mss, next_candles)
        self.assertFalse(result.is_accepted)
        self.assertEqual(result.rejection_candle_index, 0)
        self.assertIn("below CP", result.rejection_reason)

    def test_bull_rejected_second_candle_below(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        next_candles = [
            _candle(11, 102.0, 103.0, 101.5, 102.0),  # above
            _candle(12, 101.5, 102.0, 100.0, 100.8),   # closes below 101
        ]
        result = check_acceptance(mss, next_candles)
        self.assertFalse(result.is_accepted)
        self.assertEqual(result.rejection_candle_index, 1)

    def test_bear_accepted_both_below(self):
        mss = _make_mss("BEAR", 10, cp_price=100.0)
        next_candles = [
            _candle(11, 99.5, 99.8, 98.5, 99.0),  # below 100
            _candle(12, 99.0, 99.5, 98.0, 98.5),   # below 100
        ]
        result = check_acceptance(mss, next_candles)
        self.assertTrue(result.is_accepted)
        self.assertEqual(result.checked_candles, 2)

    def test_bear_rejected_closes_above(self):
        mss = _make_mss("BEAR", 10, cp_price=100.0)
        next_candles = [
            _candle(11, 99.5, 100.5, 99.0, 100.2),  # closes above 100
            _candle(12, 100.0, 100.5, 99.0, 99.5),
        ]
        result = check_acceptance(mss, next_candles)
        self.assertFalse(result.is_accepted)
        self.assertIn("above CP", result.rejection_reason)

    def test_no_candles_available(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        result = check_acceptance(mss, [])
        self.assertFalse(result.is_accepted)
        self.assertEqual(result.checked_candles, 0)
        self.assertIn("no candles", result.rejection_reason)

    def test_only_one_candle_available_accepted(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        next_candles = [_candle(11, 102.0, 103.0, 101.5, 102.5)]
        result = check_acceptance(mss, next_candles)
        self.assertTrue(result.is_accepted)
        self.assertEqual(result.checked_candles, 1)

    def test_close_exactly_at_cp_bull_accepted(self):
        """Close == CP price: not below, so bull MSS holds."""
        mss = _make_mss("BULL", 10, cp_price=101.0)
        next_candles = [
            _candle(11, 101.0, 102.0, 100.5, 101.0),  # exactly at CP
            _candle(12, 101.0, 102.0, 101.0, 101.5),
        ]
        result = check_acceptance(mss, next_candles)
        self.assertTrue(result.is_accepted)

    def test_close_exactly_at_cp_bear_accepted(self):
        """Close == CP price: not above, so bear MSS holds."""
        mss = _make_mss("BEAR", 10, cp_price=100.0)
        next_candles = [
            _candle(11, 100.0, 100.5, 99.0, 100.0),  # exactly at CP
            _candle(12, 100.0, 100.2, 99.0, 99.5),
        ]
        result = check_acceptance(mss, next_candles)
        self.assertTrue(result.is_accepted)


class TestValidateMSSAcceptance(unittest.TestCase):
    """Tests for the batch validate_mss_acceptance function."""

    def test_updates_mss_in_place(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        candles = [
            _candle(10, 100.0, 103.0, 100.0, 102.5),  # trigger
            _candle(11, 102.0, 103.0, 101.5, 102.5),   # hold
            _candle(12, 102.3, 103.5, 102.0, 103.0),   # hold
        ]
        validate_mss_acceptance([mss], candles)
        self.assertTrue(mss.is_accepted)
        self.assertIsNone(mss.rejection_reason)

    def test_rejection_populates_reason(self):
        mss = _make_mss("BULL", 10, cp_price=101.0)
        candles = [
            _candle(10, 100.0, 103.0, 100.0, 102.5),  # trigger
            _candle(11, 101.0, 102.0, 100.0, 100.5),   # fails
        ]
        validate_mss_acceptance([mss], candles)
        self.assertFalse(mss.is_accepted)
        self.assertIn("below CP", mss.rejection_reason)

    def test_trigger_at_end_of_list(self):
        """MSS trigger is the last candle — no candles to check."""
        mss = _make_mss("BULL", 10, cp_price=101.0)
        candles = [_candle(10, 100.0, 103.0, 100.0, 102.5)]
        validate_mss_acceptance([mss], candles)
        self.assertFalse(mss.is_accepted)


if __name__ == "__main__":
    unittest.main()
