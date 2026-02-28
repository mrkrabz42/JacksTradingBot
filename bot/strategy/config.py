"""Strategy configuration for the enhanced SMA Crossover system."""
from __future__ import annotations

# SMA Crossover parameters
SMA_SHORT_PERIOD: int = 20
SMA_LONG_PERIOD: int = 50

# Timeframe for bar data
DEFAULT_TIMEFRAME: str = "hour"  # 1-hour bars
DEFAULT_LOOKBACK_DAYS: int = 30  # fetch 30 days of history

# Minimum data requirements
MIN_CANDLES: int = SMA_LONG_PERIOD + 2  # need at least slow + 2 for crossover

# Crossover strength thresholds
STRENGTH_STRONG: float = 0.005    # 0.5% separation = strong signal
STRENGTH_MODERATE: float = 0.002  # 0.2% separation = moderate signal
