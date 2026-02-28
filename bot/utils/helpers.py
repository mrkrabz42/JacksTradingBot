"""Common helper functions."""

from datetime import datetime, time
import pytz


def is_market_open() -> bool:
    """Check if US stock market is currently open (9:30 AM - 4:00 PM ET, weekdays)."""
    et = pytz.timezone("US/Eastern")
    now = datetime.now(et)

    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now.time() <= market_close
