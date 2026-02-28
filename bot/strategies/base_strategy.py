"""Abstract base class for all trading strategies."""

from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    """All strategies inherit from this and implement evaluate()."""

    def __init__(self, symbol: str, timeframe: str = "day"):
        self.symbol = symbol
        self.timeframe = timeframe

    @abstractmethod
    def evaluate(self, df: pd.DataFrame) -> Signal:
        """Analyze price data and return a trading signal."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...
