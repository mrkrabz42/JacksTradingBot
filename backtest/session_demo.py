"""Session + Control Point pipeline demo.

Walks backward from today to find the last trading day with actual bars,
classifies each bar into ASIA/LONDON/NY sessions, detects swing control
points, and prints a formatted report.

Usage:
    PYTHONPATH=. python3 backtest/session_demo.py [SYMBOL]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from loguru import logger

from bot.data.market_data import get_historical_bars
from bot.sessions.classifier import get_session, get_session_info
from bot.strategy.structure.control_points import identify_control_points

logger.remove()
logger.add(sys.stderr, level="WARNING")

SESSIONS_ORDER = ["ASIA", "LONDON", "NY", "OUTSIDE"]


def find_last_trading_day(symbol: str, max_lookback: int = 10) -> tuple[datetime, datetime]:
    """Walk backward from today to find a day with actual minute bars."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for offset in range(0, max_lookback):
        day = today - timedelta(days=offset)
        day_end = day + timedelta(days=1)
        df = get_historical_bars(symbol, timeframe="minute", start=day, end=day_end)
        if len(df) > 0:
            return day, day_end
    raise RuntimeError(f"No bars found for {symbol} in the last {max_lookback} days")


def run_demo(symbol: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Session + Control Point Pipeline Demo")
    print(f"  Symbol: {symbol}")
    print(f"{'='*60}\n")

    # Step 1: Find last trading day
    day_start, day_end = find_last_trading_day(symbol)
    date_str = day_start.strftime("%Y-%m-%d")
    print(f"Last trading day: {date_str}\n")

    # Step 2: Fetch 1-min bars
    df = get_historical_bars(symbol, timeframe="minute", start=day_start, end=day_end)
    print(f"Total bars fetched: {len(df)}\n")

    # Step 3: Classify bars into sessions
    session_bars: dict[str, list[dict]] = defaultdict(list)
    candles: list[dict] = []

    for ts, row in df.iterrows():
        ts_dt = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
        if ts_dt.tzinfo is None:
            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
        session = get_session(ts_dt)
        candle = {
            "time": ts_dt,
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "open": float(row["Open"]),
            "volume": int(row["Volume"]),
        }
        session_bars[session].append(candle)
        candles.append(candle)

    # Step 4: Print session breakdown
    print(f"{'Session':<12} {'Bars':>6} {'High':>10} {'Low':>10} {'Range':>8}")
    print("-" * 50)

    for sess_name in SESSIONS_ORDER:
        bars = session_bars.get(sess_name, [])
        if not bars:
            print(f"{sess_name:<12} {'0':>6} {'—':>10} {'—':>10} {'—':>8}")
            continue
        high = max(b["high"] for b in bars)
        low = min(b["low"] for b in bars)
        rng = high - low
        print(f"{sess_name:<12} {len(bars):>6} {high:>10.2f} {low:>10.2f} {rng:>8.2f}")

    total_high = max(c["high"] for c in candles)
    total_low = min(c["low"] for c in candles)
    print("-" * 50)
    print(f"{'DAY TOTAL':<12} {len(candles):>6} {total_high:>10.2f} {total_low:>10.2f} {total_high - total_low:>8.2f}")

    # Step 5: Detect control points
    cps = identify_control_points(candles, lookback=5)
    print(f"\n{'='*60}")
    print(f"  Control Points (lookback=5): {len(cps)} detected")
    print(f"{'='*60}\n")

    if cps:
        print(f"{'Type':<8} {'Price':>10} {'Time (UTC)':<22} {'Session':<10}")
        print("-" * 52)
        for cp in cps:
            cp_session = get_session(cp.time if cp.time.tzinfo else cp.time.replace(tzinfo=timezone.utc))
            time_str = cp.time.strftime("%H:%M")
            print(f"{cp.type:<8} {cp.price:>10.2f} {time_str:<22} {cp_session:<10}")
    else:
        print("No control points detected (need more bars or wider lookback).")

    # Summary
    highs = [cp for cp in cps if cp.type == "HIGH"]
    lows = [cp for cp in cps if cp.type == "LOW"]
    print(f"\nSummary: {len(highs)} swing highs, {len(lows)} swing lows")
    print(f"Day range: ${total_low:.2f} — ${total_high:.2f} (${total_high - total_low:.2f})")
    print()


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    run_demo(symbol)
