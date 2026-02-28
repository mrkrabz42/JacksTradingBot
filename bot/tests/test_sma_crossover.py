"""Unit tests for the enhanced SMA Crossover strategy."""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from bot.strategy.sma_crossover import SMACrossoverStrategy


def _make_df(prices: list[float], start: datetime | None = None) -> pd.DataFrame:
    """Build a minimal price DataFrame from a list of close prices."""
    if start is None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    idx = pd.DatetimeIndex([start + timedelta(hours=i) for i in range(len(prices))])
    return pd.DataFrame(
        {"Open": prices, "High": prices, "Low": prices, "Close": prices, "Volume": [1000] * len(prices)},
        index=idx,
    )


class TestSMACrossoverSignals(unittest.TestCase):
    """Core signal generation tests."""

    def test_golden_cross_detected(self):
        """When short SMA crosses above long SMA → BUY signal."""
        # Build data: first 50 values trending down, then a sharp uptick
        # so the 20-SMA crosses above the 50-SMA.
        prices = [100.0 - i * 0.1 for i in range(55)]  # declining
        prices += [100.0 + i * 2.0 for i in range(20)]  # sharp rise
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        buy_signals = [s for s in signals if s["type"] == "BUY"]
        self.assertGreater(len(buy_signals), 0, "Expected at least one BUY (golden cross)")

    def test_death_cross_detected(self):
        """When short SMA crosses below long SMA → SELL signal."""
        prices = [100.0 + i * 0.1 for i in range(55)]  # rising
        prices += [100.0 - i * 2.0 for i in range(20)]  # sharp drop
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        sell_signals = [s for s in signals if s["type"] == "SELL"]
        self.assertGreater(len(sell_signals), 0, "Expected at least one SELL (death cross)")

    def test_flat_market_no_crossover(self):
        """Flat prices → no crossover signals."""
        prices = [100.0] * 80
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        self.assertEqual(len(signals), 0, "Flat market should produce no signals")

    def test_insufficient_data_returns_empty(self):
        """Fewer candles than long_period + 2 → empty signals."""
        prices = [100.0] * 10
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=20, long_period=50)
        signals = strat.generate_signals(df)
        self.assertEqual(len(signals), 0)

    def test_signal_structure(self):
        """Each signal dict has the required keys."""
        prices = [100.0 - i * 0.1 for i in range(55)]
        prices += [100.0 + i * 2.0 for i in range(20)]
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        self.assertGreater(len(signals), 0)

        sig = signals[0]
        for key in ("timestamp", "type", "sma_short", "sma_long", "strength", "close"):
            self.assertIn(key, sig, f"Missing key: {key}")
        self.assertIn(sig["type"], ("BUY", "SELL"))
        self.assertIsInstance(sig["strength"], float)
        self.assertGreaterEqual(sig["strength"], 0.0)


class TestGetLatestSignal(unittest.TestCase):
    def test_latest_after_generate(self):
        prices = [100.0 - i * 0.1 for i in range(55)]
        prices += [100.0 + i * 2.0 for i in range(20)]
        df = _make_df(prices)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        strat.generate_signals(df)
        latest = strat.get_latest_signal()
        self.assertIsNotNone(latest)

    def test_latest_none_before_generate(self):
        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        self.assertIsNone(strat.get_latest_signal())

    def test_latest_none_with_no_signals(self):
        prices = [100.0] * 80
        df = _make_df(prices)
        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        strat.generate_signals(df)
        self.assertIsNone(strat.get_latest_signal())


class TestCrossoverStrength(unittest.TestCase):
    def test_sharp_move_has_higher_strength(self):
        """A violent cross should have higher strength than a gentle one."""
        # Gentle decline then gentle rise
        gentle = [100.0 - 0.02 * i for i in range(55)] + [99.0 + 0.05 * i for i in range(20)]
        # Same decline then sharp rise
        sharp = [100.0 - 0.02 * i for i in range(55)] + [99.0 + 1.0 * i for i in range(20)]

        strat = SMACrossoverStrategy(short_period=5, long_period=20)

        strat.generate_signals(_make_df(gentle))
        gentle_sigs = [s for s in strat.get_signals() if s["type"] == "BUY"]

        strat.generate_signals(_make_df(sharp))
        sharp_sigs = [s for s in strat.get_signals() if s["type"] == "BUY"]

        if gentle_sigs and sharp_sigs:
            max_gentle = max(s["strength"] for s in gentle_sigs)
            max_sharp = max(s["strength"] for s in sharp_sigs)
            self.assertGreater(max_sharp, max_gentle)


class TestEdgeCases(unittest.TestCase):
    def test_gap_up_triggers_cross(self):
        """A large gap should still trigger a cross if SMAs cross."""
        prices = [100.0] * 55 + [80.0] * 5 + [120.0] * 15
        df = _make_df(prices)
        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        # After the gap up, short SMA recovers above long SMA → BUY
        buy_signals = [s for s in signals if s["type"] == "BUY"]
        self.assertGreater(len(buy_signals), 0)

    def test_invalid_periods_raises(self):
        with self.assertRaises(ValueError):
            SMACrossoverStrategy(short_period=50, long_period=20)

    def test_timestamp_extracted_from_index(self):
        """Timestamps should come from the DatetimeIndex."""
        prices = [100.0 - i * 0.1 for i in range(55)]
        prices += [100.0 + i * 2.0 for i in range(20)]
        start = datetime(2026, 2, 13, 14, 0, tzinfo=timezone.utc)
        df = _make_df(prices, start=start)

        strat = SMACrossoverStrategy(short_period=5, long_period=20)
        signals = strat.generate_signals(df)
        self.assertGreater(len(signals), 0)
        # Should be a parseable ISO timestamp from the Feb 13+ range
        ts = signals[0]["timestamp"]
        self.assertIn("2026-02-", ts)


if __name__ == "__main__":
    unittest.main()
