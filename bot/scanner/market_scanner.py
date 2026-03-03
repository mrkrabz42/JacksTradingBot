"""Scans a watchlist for trade opportunities using configured strategies.

Uses the MultiStrategyAggregator with scorecard-weighted confidence
when strategy scores are available.
"""

from __future__ import annotations

from loguru import logger

from bot.config import WATCHLIST
from bot.data.market_data import get_historical_bars
from bot.strategies.base_strategy import Signal
from bot.strategies.sma_crossover import SMACrossover
from bot.scanner.signal_generator import MultiStrategyAggregator


def scan_watchlist(
    symbols: list[str] | None = None,
    timeframe: str = "day",
    days_back: int = 100,
    strategy_scores: dict[str, float] | None = None,
) -> list[dict]:
    """Scan symbols and return those with BUY or SELL signals.

    Args:
        symbols: List of tickers to scan. Defaults to WATCHLIST.
        timeframe: Bar timeframe.
        days_back: Number of days of historical data.
        strategy_scores: Optional mapping of strategy_name → composite score (0–1)
                         from the scorecard. Enables confidence adjustment.

    Returns:
        List of dicts with keys: symbol, signal, strategy, confidence
    """
    if symbols is None:
        symbols = WATCHLIST

    aggregator = MultiStrategyAggregator(strategy_scores=strategy_scores)
    results = []

    for symbol in symbols:
        try:
            df = get_historical_bars(symbol, timeframe=timeframe, days_back=days_back)
            if df.empty:
                logger.warning(f"No data for {symbol}, skipping")
                continue

            # Build strategy list for this symbol
            strategies = [SMACrossover(symbol, timeframe)]

            # Run through aggregator (handles scoring + threshold)
            signals = aggregator.evaluate(symbol, strategies, df)
            results.extend(signals)

        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            continue

    logger.info(f"Scanner found {len(results)} signals from {len(symbols)} symbols")
    return results
