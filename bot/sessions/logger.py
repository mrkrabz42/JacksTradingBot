"""CSV logger for session levels — writes to bot/logs/session_levels.csv."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

_LOG_DIR = Path(__file__).parent.parent / "logs"
_CSV_PATH = _LOG_DIR / "session_levels.csv"

_FIELDNAMES = [
    "timestamp",
    "symbol",
    "date",
    "session",
    "high",
    "high_time",
    "low",
    "low_time",
    "bar_count",
    "pdh",
    "pdl",
    "pdh_session",
    "pdl_session",
]


def _ensure_csv() -> None:
    """Create the CSV with headers if it doesn't exist."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not _CSV_PATH.exists():
        with open(_CSV_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
            writer.writeheader()


def log_session_levels(
    symbol: str,
    date: str,
    sessions: List[dict],
    daily: dict,
) -> None:
    """Append session level data to the CSV log.

    Args:
        symbol: Ticker symbol.
        date: Trading date string (YYYY-MM-DD).
        sessions: List of session extreme dicts from calculate_session_extremes().
        daily: Daily extremes dict from calculate_daily_extremes().
    """
    _ensure_csv()
    now = datetime.utcnow().isoformat()

    with open(_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        for sess in sessions:
            writer.writerow({
                "timestamp": now,
                "symbol": symbol,
                "date": date,
                "session": sess["session"],
                "high": sess.get("high"),
                "high_time": sess.get("high_time"),
                "low": sess.get("low"),
                "low_time": sess.get("low_time"),
                "bar_count": sess.get("bar_count", 0),
                "pdh": daily.get("pdh"),
                "pdl": daily.get("pdl"),
                "pdh_session": daily.get("pdh_session"),
                "pdl_session": daily.get("pdl_session"),
            })

    logger.info(f"Logged {len(sessions)} session levels for {symbol} on {date}")
