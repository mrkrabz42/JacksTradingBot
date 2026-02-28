"""Unit tests for the displacement candle validator."""
from __future__ import annotations

import unittest

from bot.strategy.structure.displacement import (
    DisplacementResult,
    analyze_displacement,
    displacement_quality,
    is_displacement,
)


class TestIsDisplacement(unittest.TestCase):
    """Tests for the boolean is_displacement helper."""

    def test_strong_bullish_candle_passes(self):
        # Range = 3.0, body = 2.5 (83%), opposing wick = 0.1 (3%), ATR = 2.0
        candle = {"open": 100.1, "high": 103.0, "low": 100.0, "close": 102.6}
        self.assertTrue(is_displacement(candle, atr_value=2.0))

    def test_strong_bearish_candle_passes(self):
        # Range = 3.0, body = 2.5 (83%), opposing wick = 0.1 (3%)
        candle = {"open": 102.9, "high": 103.0, "low": 100.0, "close": 100.4}
        self.assertTrue(is_displacement(candle, atr_value=2.0))

    def test_small_candle_fails_size(self):
        # Range = 1.0, threshold = 1.2 * 2.0 = 2.4
        candle = {"open": 100.0, "high": 101.0, "low": 100.0, "close": 100.9}
        self.assertFalse(is_displacement(candle, atr_value=2.0))

    def test_doji_fails(self):
        candle = {"open": 100.5, "high": 101.0, "low": 100.0, "close": 100.5}
        self.assertFalse(is_displacement(candle, atr_value=0.5))

    def test_big_opposing_wick_fails(self):
        # Range = 3.0, body = 2.0 (67%), opposing wick = 0.8 (27% > 20%)
        candle = {"open": 100.8, "high": 103.0, "low": 100.0, "close": 102.8}
        self.assertFalse(is_displacement(candle, atr_value=2.0))

    def test_small_body_fails(self):
        # Range = 3.0, body = 1.0 (33% < 60%), opposing wick = 0.0
        candle = {"open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0}
        self.assertFalse(is_displacement(candle, atr_value=2.0))

    def test_zero_range_candle(self):
        candle = {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}
        self.assertFalse(is_displacement(candle, atr_value=1.0))

    def test_zero_atr(self):
        candle = {"open": 100.0, "high": 103.0, "low": 100.0, "close": 103.0}
        self.assertFalse(is_displacement(candle, atr_value=0.0))


class TestAnalyzeDisplacement(unittest.TestCase):
    """Tests for the full DisplacementResult breakdown."""

    def test_result_fields(self):
        candle = {"open": 100.0, "high": 103.0, "low": 100.0, "close": 102.8}
        result = analyze_displacement(candle, atr_value=2.0)
        self.assertIsInstance(result, DisplacementResult)
        self.assertTrue(result.meets_size)
        self.assertTrue(result.meets_body)
        self.assertTrue(result.meets_wick)
        self.assertTrue(result.is_displacement)
        self.assertGreater(result.quality_score, 0.5)

    def test_partial_fail_shows_which_rules(self):
        # Big wick — only size and body pass, wick fails
        candle = {"open": 100.8, "high": 103.0, "low": 100.0, "close": 102.8}
        result = analyze_displacement(candle, atr_value=2.0)
        self.assertTrue(result.meets_size)
        self.assertTrue(result.meets_body)
        self.assertFalse(result.meets_wick)
        self.assertFalse(result.is_displacement)

    def test_quality_capped_when_not_displacement(self):
        # Fails at least one rule → quality capped at 0.49
        candle = {"open": 100.0, "high": 101.0, "low": 100.0, "close": 100.9}
        result = analyze_displacement(candle, atr_value=2.0)
        self.assertFalse(result.is_displacement)
        self.assertLessEqual(result.quality_score, 0.49)

    def test_ratios_computed_correctly(self):
        candle = {"open": 100.0, "high": 104.0, "low": 100.0, "close": 104.0}
        result = analyze_displacement(candle, atr_value=2.0)
        # range = 4.0, threshold = 2.4, range_ratio = 4.0 / 2.4 ≈ 1.667
        self.assertAlmostEqual(result.range_ratio, 4.0 / 2.4, places=2)
        # body = 4.0, body_ratio = 1.0
        self.assertAlmostEqual(result.body_ratio, 1.0, places=2)
        # opposing wick = 0.0, wick_ratio = 0.0
        self.assertAlmostEqual(result.wick_ratio, 0.0, places=2)


class TestDisplacementQuality(unittest.TestCase):
    """Tests for the quality scoring function."""

    def test_perfect_candle_near_one(self):
        # Range = 2x ATR threshold, 100% body, 0% wick
        candle = {"open": 100.0, "high": 104.8, "low": 100.0, "close": 104.8}
        score = displacement_quality(candle, atr_value=2.0)
        self.assertGreater(score, 0.9)

    def test_marginal_candle_lower_score(self):
        # Just barely passes all thresholds
        # Range = 2.4 = exactly 1.2 * 2.0, body = 60%, wick = 20%
        candle = {"open": 100.48, "high": 102.4, "low": 100.0, "close": 101.92}
        score = displacement_quality(candle, atr_value=2.0)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 0.7)


if __name__ == "__main__":
    unittest.main()
