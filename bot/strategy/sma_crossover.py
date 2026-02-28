"""Enhanced SMA Crossover strategy with signal history and strength scoring.

Generates timestamped BUY/SELL signals when the short-period SMA
crosses the long-period SMA, with a strength indicator showing how
far apart the two averages are.

This is the Phase 3 enhanced version.  The Phase 1 original lives at
``bot/strategies/sma_crossover.py``.
"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd
from loguru import logger

from bot.strategy.config import (
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_TIMEFRAME,
    MIN_CANDLES,
    SMA_LONG_PERIOD,
    SMA_SHORT_PERIOD,
)


def _sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average — avoids external dependency."""
    return series.rolling(window=period, min_periods=period).mean()


class SMACrossoverStrategy:
    """Enhanced SMA Crossover with signal history and strength scoring.

    Args:
        short_period: Fast SMA lookback window.
        long_period: Slow SMA lookback window.
        timeframe: Bar timeframe string (for metadata only).
    """

    def __init__(
        self,
        short_period: int = SMA_SHORT_PERIOD,
        long_period: int = SMA_LONG_PERIOD,
        timeframe: str = DEFAULT_TIMEFRAME,
    ) -> None:
        if short_period >= long_period:
            raise ValueError(f"short_period ({short_period}) must be < long_period ({long_period})")
        self.short_period = short_period
        self.long_period = long_period
        self.timeframe = timeframe
        self._signals: List[dict] = []

    @property
    def name(self) -> str:
        return f"SMA Crossover ({self.short_period}/{self.long_period})"

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def generate_signals(self, df: pd.DataFrame) -> List[dict]:
        """Scan a price DataFrame and return all crossover signals.

        Args:
            df: Must have columns ``Close`` (and ideally a
                DatetimeIndex or a ``timestamp`` column).
                Rows ordered oldest-first.

        Returns:
            List of signal dicts, each with keys:
              ``timestamp``, ``type`` ('BUY' | 'SELL'),
              ``sma_short``, ``sma_long``, ``strength``, ``close``.
        """
        if len(df) < MIN_CANDLES:
            logger.warning(
                f"{self.name}: Not enough data (need {MIN_CANDLES}, got {len(df)})"
            )
            self._signals = []
            return []

        close = df["Close"]
        sma_s = _sma(close, self.short_period)
        sma_l = _sma(close, self.long_period)

        signals: List[dict] = []

        # Start from index where both SMAs are valid
        start_idx = self.long_period
        for i in range(start_idx, len(df)):
            s_now = sma_s.iloc[i]
            s_prev = sma_s.iloc[i - 1]
            l_now = sma_l.iloc[i]
            l_prev = sma_l.iloc[i - 1]

            if pd.isna(s_now) or pd.isna(l_now) or pd.isna(s_prev) or pd.isna(l_prev):
                continue

            signal_type: Optional[str] = None

            # Golden cross: short crosses above long
            if s_prev <= l_prev and s_now > l_now:
                signal_type = "BUY"

            # Death cross: short crosses below long
            elif s_prev >= l_prev and s_now < l_now:
                signal_type = "SELL"

            if signal_type is not None:
                # Strength = percentage gap between the two SMAs
                mid = (s_now + l_now) / 2.0
                strength = abs(s_now - l_now) / mid if mid > 0 else 0.0

                ts = self._extract_timestamp(df, i)

                sig = {
                    "timestamp": ts,
                    "type": signal_type,
                    "sma_short": round(s_now, 4),
                    "sma_long": round(l_now, 4),
                    "strength": round(strength, 6),
                    "close": round(float(close.iloc[i]), 4),
                }
                signals.append(sig)
                logger.info(
                    f"{self.name}: {signal_type} @ {ts} | "
                    f"SMA{self.short_period}={s_now:.2f} "
                    f"SMA{self.long_period}={l_now:.2f} "
                    f"strength={strength:.4f}"
                )

        self._signals = signals
        return signals

    def get_latest_signal(self) -> Optional[dict]:
        """Return the most recent signal, or None if no signals exist."""
        return self._signals[-1] if self._signals else None

    def get_signals(self) -> List[dict]:
        """Return all generated signals (from last ``generate_signals`` call)."""
        return list(self._signals)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_timestamp(df: pd.DataFrame, idx: int) -> str:
        """Pull an ISO timestamp from the DataFrame index or a column."""
        if isinstance(df.index, pd.DatetimeIndex):
            return df.index[idx].isoformat()
        if "timestamp" in df.columns:
            val = df["timestamp"].iloc[idx]
            return val.isoformat() if hasattr(val, "isoformat") else str(val)
        return str(idx)
