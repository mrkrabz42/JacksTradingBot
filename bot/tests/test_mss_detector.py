"""Unit tests for the MSS (Market Structure Shift) detector."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from bot.strategy.structure.control_points import ControlPoint
from bot.strategy.structure.mss_detector import MSS, detect_mss


def _ts(minute: int) -> datetime:
    """Helper — return a UTC datetime at a given minute offset on a fixed day."""
    return datetime(2026, 2, 13, 14, minute, tzinfo=timezone.utc)


def _candle(minute: int, o: float, h: float, l: float, c: float) -> dict:
    return {"time": _ts(minute), "open": o, "high": h, "low": l, "close": c}


class TestDetectMSS(unittest.TestCase):
    """Core detection logic."""

    def _make_atr(self) -> float:
        """ATR that makes a $1.50 range candle pass displacement (1.5 / 1.2 = 1.25)."""
        return 1.0

    def test_bull_mss_detected(self):
        """Body close above swing high with displacement → bull MSS."""
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        cp_low = ControlPoint(price=99.0, time=_ts(3), type="LOW")
        cps = [cp_low, cp_high]

        # Strong bullish candle closing above 102.0
        candles = [_candle(10, 101.5, 103.5, 101.5, 103.2)]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].direction, "BULL")
        self.assertGreater(events[0].displacement_quality, 0.0)
        self.assertEqual(events[0].control_point, cp_high)

    def test_bear_mss_detected(self):
        """Body close below swing low with displacement → bear MSS."""
        cp_high = ControlPoint(price=102.0, time=_ts(3), type="HIGH")
        cp_low = ControlPoint(price=100.0, time=_ts(5), type="LOW")
        cps = [cp_high, cp_low]

        # Strong bearish candle closing below 100.0
        candles = [_candle(10, 100.2, 100.2, 98.5, 98.6)]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].direction, "BEAR")
        self.assertEqual(events[0].control_point, cp_low)

    def test_wick_only_no_mss(self):
        """Wick touches above swing high but body closes below → no MSS."""
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        cps = [cp_high]

        # Wick above 102 but body closes at 101.8
        candles = [_candle(10, 101.0, 102.5, 101.0, 101.8)]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 0)

    def test_no_displacement_no_mss(self):
        """Body closes above CP but candle is too small → no MSS."""
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        cps = [cp_high]

        # Tiny candle that closes above 102 — fails displacement
        candles = [_candle(10, 102.0, 102.15, 101.95, 102.10)]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 0)

    def test_cp_not_yet_active(self):
        """A CP in the future is not used for detection."""
        # CP is at minute 20, candle is at minute 10 — CP not yet active
        cp_high = ControlPoint(price=102.0, time=_ts(20), type="HIGH")
        cps = [cp_high]

        candles = [_candle(10, 101.5, 103.5, 101.5, 103.2)]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 0)

    def test_same_cp_not_triggered_twice(self):
        """Once a CP fires an MSS, subsequent candles closing beyond it don't re-trigger."""
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        cps = [cp_high]

        candles = [
            _candle(10, 101.5, 103.5, 101.5, 103.2),  # triggers MSS
            _candle(11, 103.0, 104.5, 103.0, 104.2),   # also above — should NOT trigger again
        ]
        events = detect_mss(candles, cps, atr_value=self._make_atr())

        self.assertEqual(len(events), 1)

    def test_empty_inputs(self):
        self.assertEqual(detect_mss([], [], atr_value=1.0), [])
        cp = ControlPoint(price=100.0, time=_ts(5), type="HIGH")
        self.assertEqual(detect_mss([], [cp], atr_value=1.0), [])
        self.assertEqual(detect_mss([_candle(10, 100, 101, 100, 101)], [], atr_value=1.0), [])


class TestMSSContext(unittest.TestCase):
    """Context fields: session, PDH/PDL distances."""

    def test_pdh_pdl_distances(self):
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        candles = [_candle(10, 101.5, 103.5, 101.5, 103.2)]

        events = detect_mss(
            candles, [cp_high], atr_value=1.0,
            pdh=105.0, pdl=98.0,
        )
        self.assertEqual(len(events), 1)
        mss = events[0]
        self.assertAlmostEqual(mss.distance_to_pdh, 103.2 - 105.0, places=2)
        self.assertAlmostEqual(mss.distance_to_pdl, 103.2 - 98.0, places=2)

    def test_session_context_populated(self):
        # 14:30 UTC is NY session
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        candles = [_candle(30, 101.5, 103.5, 101.5, 103.2)]

        events = detect_mss(candles, [cp_high], atr_value=1.0)
        self.assertEqual(events[0].session_context, "NY")

    def test_session_extremes_distances(self):
        cp_high = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        candles = [_candle(30, 101.5, 103.5, 101.5, 103.2)]

        sess = [{"session": "NY", "high": 104.0, "low": 99.5, "bar_count": 100}]
        events = detect_mss(candles, [cp_high], atr_value=1.0, session_extremes=sess)
        mss = events[0]
        self.assertAlmostEqual(mss.distance_to_session_high, 103.2 - 104.0, places=2)
        self.assertAlmostEqual(mss.distance_to_session_low, 103.2 - 99.5, places=2)


class TestMSSDataclass(unittest.TestCase):
    """Verify MSS object shape."""

    def test_is_accepted_defaults_none(self):
        cp = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        candles = [_candle(10, 101.5, 103.5, 101.5, 103.2)]
        events = detect_mss(candles, [cp], atr_value=1.0)
        self.assertIsNone(events[0].is_accepted)

    def test_id_format(self):
        cp = ControlPoint(price=102.0, time=_ts(5), type="HIGH")
        candles = [_candle(10, 101.5, 103.5, 101.5, 103.2)]
        events = detect_mss(candles, [cp], atr_value=1.0)
        self.assertTrue(events[0].id.startswith("MSS_"))


if __name__ == "__main__":
    unittest.main()
