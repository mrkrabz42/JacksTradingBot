"""Calculate session and daily highs/lows with ownership tagging."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from bot.data.market_data import get_historical_bars
from bot.sessions.classifier import get_session, get_all_sessions, SessionName


def calculate_session_extremes(
    symbol: str,
    date: Optional[datetime] = None,
) -> List[dict]:
    """Compute high/low for each session on the given date.

    Args:
        symbol: Ticker symbol.
        date: Trading day (defaults to today UTC).

    Returns list of dicts, one per session, with keys:
        session, label, high, high_time, low, low_time, bar_count
    """
    if date is None:
        date = datetime.utcnow()

    start = datetime(date.year, date.month, date.day, 0, 0)
    end = start + timedelta(days=1)

    try:
        df = get_historical_bars(symbol, timeframe="minute", start=start, end=end)
    except Exception as e:
        logger.error(f"Failed to fetch minute bars for {symbol}: {e}")
        return []

    if df.empty:
        logger.warning(f"No minute bars for {symbol} on {date.date()}")
        return []

    sessions_info = get_all_sessions()
    results: List[dict] = []

    for sess_name, info in sessions_info.items():
        # Filter bars belonging to this session
        mask = df.index.map(lambda ts: get_session(ts.to_pydatetime()) == sess_name)
        sess_df = df[mask]

        if sess_df.empty:
            results.append({
                "session": sess_name,
                "label": info["label"],
                "high": None,
                "high_time": None,
                "low": None,
                "low_time": None,
                "bar_count": 0,
            })
            continue

        high_idx = sess_df["High"].idxmax()
        low_idx = sess_df["Low"].idxmin()

        results.append({
            "session": sess_name,
            "label": info["label"],
            "high": float(sess_df.loc[high_idx, "High"]),
            "high_time": high_idx.isoformat(),
            "low": float(sess_df.loc[low_idx, "Low"]),
            "low_time": low_idx.isoformat(),
            "bar_count": len(sess_df),
        })

    logger.debug(f"Session extremes for {symbol} on {date.date()}: {len(results)} sessions")
    return results


def calculate_daily_extremes(
    symbol: str,
    date: Optional[datetime] = None,
) -> dict:
    """Compute the previous day high/low (PDH/PDL) with session ownership.

    Args:
        symbol: Ticker symbol.
        date: The reference date — computes extremes for the PREVIOUS day.

    Returns dict with keys: pdh, pdh_time, pdh_session, pdl, pdl_time, pdl_session, date.
    """
    if date is None:
        date = datetime.utcnow()

    prev_day = date - timedelta(days=1)
    # Skip weekends
    while prev_day.weekday() >= 5:
        prev_day -= timedelta(days=1)

    start = datetime(prev_day.year, prev_day.month, prev_day.day, 0, 0)
    end = start + timedelta(days=1)

    try:
        df = get_historical_bars(symbol, timeframe="minute", start=start, end=end)
    except Exception as e:
        logger.error(f"Failed to fetch minute bars for {symbol}: {e}")
        return {"pdh": None, "pdl": None, "date": prev_day.date().isoformat()}

    if df.empty:
        logger.warning(f"No bars for {symbol} on {prev_day.date()}")
        return {"pdh": None, "pdl": None, "date": prev_day.date().isoformat()}

    high_idx = df["High"].idxmax()
    low_idx = df["Low"].idxmin()

    pdh_session = get_session(high_idx.to_pydatetime())
    pdl_session = get_session(low_idx.to_pydatetime())

    result = {
        "pdh": float(df.loc[high_idx, "High"]),
        "pdh_time": high_idx.isoformat(),
        "pdh_session": pdh_session,
        "pdl": float(df.loc[low_idx, "Low"]),
        "pdl_time": low_idx.isoformat(),
        "pdl_session": pdl_session,
        "date": prev_day.date().isoformat(),
    }
    logger.debug(f"Daily extremes for {symbol}: PDH={result['pdh']} ({pdh_session}), PDL={result['pdl']} ({pdl_session})")
    return result


def get_full_session_report(
    symbol: str,
    date: Optional[datetime] = None,
) -> dict:
    """Combined session extremes + PDH/PDL for a symbol on a given date."""
    if date is None:
        date = datetime.utcnow()

    return {
        "symbol": symbol,
        "date": date.date().isoformat(),
        "sessions": calculate_session_extremes(symbol, date),
        "daily": calculate_daily_extremes(symbol, date),
    }
