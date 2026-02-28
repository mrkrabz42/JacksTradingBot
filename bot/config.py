"""Configuration and environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# Alpaca API
ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
ALPACA_PAPER_TRADE: bool = os.getenv("ALPACA_PAPER_TRADE", "True").lower() == "true"

# Risk Management
MAX_RISK_PER_TRADE: float = 0.02      # 2% of portfolio per trade
MAX_OPEN_POSITIONS: int = 5            # Maximum simultaneous positions
DAILY_LOSS_LIMIT: float = 0.05         # 5% daily loss limit — kill switch triggers
ATR_STOP_LOSS_MULTIPLIER: float = 2.0  # Stop-loss at 2x ATR below entry

# Strategy Parameters
SMA_FAST_PERIOD: int = 10
SMA_SLOW_PERIOD: int = 50

# Scanner
WATCHLIST: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "MA", "HD", "DIS",
    "BAC", "XOM", "PFE", "KO", "PEP",
]

# Scheduling
SCAN_INTERVAL_MINUTES: int = 5

# Storage
STORAGE_ENABLED: bool = os.getenv("STORAGE_ENABLED", "true").lower() == "true"
STORAGE_DB_URL: str = os.getenv("STORAGE_DB_URL", "sqlite:///bot_snapshots.sqlite")

# Participation / RVOL
PARTICIPATION_LOOKBACK_DAYS: int = int(os.getenv("PARTICIPATION_LOOKBACK_DAYS", "20"))
PARTICIPATION_MIN_BARS_PER_BUCKET: int = int(os.getenv("PARTICIPATION_MIN_BARS_PER_BUCKET", "10"))
PARTICIPATION_BUCKET_SIZE_MINUTES: int = int(os.getenv("PARTICIPATION_BUCKET_SIZE_MINUTES", "5"))
PARTICIPATION_LOW_THRESHOLD: float = float(os.getenv("PARTICIPATION_LOW_THRESHOLD", "0.7"))
PARTICIPATION_HIGH_THRESHOLD: float = float(os.getenv("PARTICIPATION_HIGH_THRESHOLD", "1.5"))
PARTICIPATION_EXTREME_THRESHOLD: float = float(os.getenv("PARTICIPATION_EXTREME_THRESHOLD", "3.0"))
PARTICIPATION_SPIKE_THRESHOLD: float = float(os.getenv("PARTICIPATION_SPIKE_THRESHOLD", "3.0"))
