"""Backtest the SMA Crossover strategy on SPY for 2 years of daily data.

Uses the backtesting.py library.
Outputs: total return, max drawdown, win rate, Sharpe ratio, and saves a chart.
"""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import SMAIndicator
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import SMA_FAST_PERIOD, SMA_SLOW_PERIOD
from bot.data.market_data import get_historical_bars

# Import logger setup
import bot.utils.logger  # noqa: F401


class SMACrossoverBacktest(Strategy):
    """SMA Crossover strategy adapted for backtesting.py."""

    fast_period = SMA_FAST_PERIOD
    slow_period = SMA_SLOW_PERIOD

    def init(self):
        close = pd.Series(self.data.Close)
        self.sma_fast = self.I(
            lambda c: SMAIndicator(c, window=self.fast_period).sma_indicator(),
            close,
            name=f"SMA{self.fast_period}",
        )
        self.sma_slow = self.I(
            lambda c: SMAIndicator(c, window=self.slow_period).sma_indicator(),
            close,
            name=f"SMA{self.slow_period}",
        )

    def next(self):
        if crossover(self.sma_fast, self.sma_slow):
            self.buy()
        elif crossover(self.sma_slow, self.sma_fast):
            self.position.close()


def run():
    """Run the backtest on SPY."""
    symbol = "SPY"
    days_back = 730  # ~2 years

    logger.info(f"Fetching {days_back} days of data for {symbol}...")
    df = get_historical_bars(symbol, timeframe="day", days_back=days_back)

    if df.empty:
        logger.error("No data returned — cannot run backtest")
        return

    # backtesting.py needs a DatetimeIndex without timezone
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    logger.info(f"Running backtest: SMA Crossover ({SMA_FAST_PERIOD}/{SMA_SLOW_PERIOD}) on {symbol}")
    logger.info(f"Data range: {df.index[0].date()} to {df.index[-1].date()} ({len(df)} bars)")

    bt = Backtest(
        df,
        SMACrossoverBacktest,
        cash=10_000,
        commission=0.0,  # Alpaca is commission-free
        exclusive_orders=True,
    )

    stats = bt.run()

    # Print key metrics
    logger.info("=" * 50)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"Total Return:    {stats['Return [%]']:.2f}%")
    logger.info(f"Buy & Hold:      {stats['Buy & Hold Return [%]']:.2f}%")
    logger.info(f"Max Drawdown:    {stats['Max. Drawdown [%]']:.2f}%")
    logger.info(f"Win Rate:        {stats['Win Rate [%]']:.2f}%")
    logger.info(f"Sharpe Ratio:    {stats['Sharpe Ratio']:.2f}")
    logger.info(f"# Trades:        {stats['# Trades']}")
    logger.info(f"Avg Trade:       {stats['Avg. Trade [%]']:.2f}%")
    logger.info("=" * 50)

    # Save chart
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    chart_path = os.path.join(results_dir, f"sma_crossover_{symbol}.html")
    bt.plot(filename=chart_path, open_browser=False)
    logger.info(f"Chart saved to: {chart_path}")

    return stats


if __name__ == "__main__":
    run()
