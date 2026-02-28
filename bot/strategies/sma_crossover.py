"""Simple Moving Average crossover strategy.

BUY when 10-period SMA crosses above 50-period SMA.
SELL when 10-period SMA crosses below 50-period SMA.
HOLD otherwise.
"""

import pandas as pd
from ta.trend import SMAIndicator
from loguru import logger

from bot.strategies.base_strategy import BaseStrategy, Signal
from bot.config import SMA_FAST_PERIOD, SMA_SLOW_PERIOD


class SMACrossover(BaseStrategy):
    """SMA Crossover strategy using fast/slow moving averages."""

    def __init__(self, symbol: str, timeframe: str = "day", fast_period: int = SMA_FAST_PERIOD, slow_period: int = SMA_SLOW_PERIOD):
        super().__init__(symbol, timeframe)
        self.fast_period = fast_period
        self.slow_period = slow_period

    @property
    def name(self) -> str:
        return f"SMA Crossover ({self.fast_period}/{self.slow_period})"

    def evaluate(self, df: pd.DataFrame) -> Signal:
        """Evaluate SMA crossover on the given price data.

        Args:
            df: DataFrame with at least a 'Close' column and enough rows for the slow period.

        Returns:
            Signal.BUY, Signal.SELL, or Signal.HOLD
        """
        if len(df) < self.slow_period + 2:
            logger.warning(f"{self.symbol}: Not enough data for SMA crossover (need {self.slow_period + 2}, got {len(df)})")
            return Signal.HOLD

        close = df["Close"]

        sma_fast = SMAIndicator(close, window=self.fast_period).sma_indicator()
        sma_slow = SMAIndicator(close, window=self.slow_period).sma_indicator()

        # Current and previous values
        fast_now = sma_fast.iloc[-1]
        fast_prev = sma_fast.iloc[-2]
        slow_now = sma_slow.iloc[-1]
        slow_prev = sma_slow.iloc[-2]

        # Crossover detection
        if fast_prev <= slow_prev and fast_now > slow_now:
            logger.info(f"{self.symbol}: BUY signal — SMA{self.fast_period} crossed above SMA{self.slow_period}")
            return Signal.BUY
        elif fast_prev >= slow_prev and fast_now < slow_now:
            logger.info(f"{self.symbol}: SELL signal — SMA{self.fast_period} crossed below SMA{self.slow_period}")
            return Signal.SELL
        else:
            logger.debug(f"{self.symbol}: HOLD — SMA{self.fast_period}={fast_now:.2f}, SMA{self.slow_period}={slow_now:.2f}")
            return Signal.HOLD
