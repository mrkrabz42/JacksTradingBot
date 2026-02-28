"""CLI entry point for bot tooling.

Usage:
    PYTHONPATH=. python3 bot/cli.py test-displacement [--date YYYY-MM-DD] [--symbol SYMBOL]
    PYTHONPATH=. python3 bot/cli.py detect-mss [--date YYYY-MM-DD] [--symbol SYMBOL] [--verbose]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="WARNING")


def cmd_test_displacement(args: argparse.Namespace) -> None:
    """Run displacement analysis on a day's 1-min candles."""
    from bot.data.market_data import get_historical_bars
    from bot.indicators.atr import calculate_atr
    from bot.strategy.structure.displacement import analyze_displacement

    symbol = args.symbol
    target = args.date

    # Resolve date — walk backward if needed to find a trading day
    if target:
        day = datetime.strptime(target, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    print(f"\n{'='*62}")
    print(f"  Displacement Candle Analysis")
    print(f"  Symbol: {symbol}")
    print(f"{'='*62}\n")

    # Walk back to find a day with data
    for offset in range(10):
        d = day - timedelta(days=offset)
        d_end = d + timedelta(days=1)
        df = get_historical_bars(symbol, timeframe="minute", start=d, end=d_end)
        if len(df) > 0:
            day = d
            break
    else:
        print("No trading data found in the last 10 days.")
        return

    date_str = day.strftime("%Y-%m-%d")
    print(f"Date: {date_str}")
    print(f"Total 1-min candles: {len(df)}\n")

    # Build candle dicts
    candles: list[dict] = []
    for ts, row in df.iterrows():
        candles.append({
            "time": ts,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        })

    if len(candles) < 15:
        print("Not enough candles to compute ATR(14).")
        return

    # Compute ATR(14) using the first 15+ candles, then roll forward
    atr_value = calculate_atr(candles, period=14)
    print(f"ATR(14): ${atr_value:.4f}\n")

    # Analyze every candle
    displacements = []
    for c in candles:
        result = analyze_displacement(c, atr_value)
        if result.is_displacement:
            displacements.append((c, result))

    print(f"Displacement candles: {len(displacements)} / {len(candles)}")
    print(f"Hit rate: {len(displacements) / len(candles) * 100:.1f}%\n")

    if not displacements:
        print("No displacement candles found.")
        return

    # Quality distribution
    scores = [r.quality_score for _, r in displacements]
    avg_score = sum(scores) / len(scores)
    buckets = {"0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0, "0.9-1.0": 0}
    for s in scores:
        if s >= 0.9:
            buckets["0.9-1.0"] += 1
        elif s >= 0.8:
            buckets["0.8-0.9"] += 1
        elif s >= 0.7:
            buckets["0.7-0.8"] += 1
        elif s >= 0.6:
            buckets["0.6-0.7"] += 1
        else:
            buckets["0.5-0.6"] += 1

    print(f"Average quality: {avg_score:.3f}")
    print(f"\nQuality distribution:")
    for bucket, count in buckets.items():
        bar = "#" * count
        print(f"  {bucket}: {count:>3}  {bar}")

    # Top 10 displacement candles by quality
    displacements.sort(key=lambda x: x[1].quality_score, reverse=True)
    top = displacements[:10]

    print(f"\n{'='*62}")
    print(f"  Top {len(top)} displacement candles")
    print(f"{'='*62}\n")

    header = f"{'Time (UTC)':<18} {'Dir':<5} {'Range':>7} {'Body%':>6} {'Wick%':>6} {'Score':>6}"
    print(header)
    print("-" * len(header))

    for candle, result in top:
        ts = candle["time"]
        time_str = ts.strftime("%H:%M") if hasattr(ts, "strftime") else str(ts)[:16]
        direction = "BULL" if candle["close"] > candle["open"] else "BEAR"
        rng = candle["high"] - candle["low"]
        print(
            f"{time_str:<18} {direction:<5} ${rng:>5.2f} "
            f"{result.body_ratio * 100:>5.1f}% "
            f"{result.wick_ratio * 100:>5.1f}% "
            f"{result.quality_score:>6.3f}"
        )

    print()


def cmd_detect_mss(args: argparse.Namespace) -> None:
    """Detect MSS events using the full pipeline."""
    from collections import Counter

    from bot.strategy.structure.mss_pipeline import run_mss_pipeline

    symbol = args.symbol
    verbose = args.verbose

    print(f"\n{'='*62}")
    print(f"  MSS (Market Structure Shift) Detection")
    print(f"  Symbol: {symbol}")
    print(f"{'='*62}\n")

    result = run_mss_pipeline(symbol=symbol, date=args.date)

    print(f"Date: {result['date']}")
    print(f"Total 1-min candles: {result['total_candles']}")
    print(f"ATR(14): ${result['atr']:.4f}")
    print(f"Control points: {result['control_points']}")
    if result["pdh"] is not None:
        print(f"PDH: ${result['pdh']:.2f}  PDL: ${result['pdl']:.2f}")

    events = result["events"]
    print(f"\n{'='*62}")
    print(f"  Results: {result['total_mss']} MSS events ({result['accepted']} accepted, {result['rejected']} rejected)")
    print(f"{'='*62}\n")

    if not events:
        print("No MSS events found.")
        return

    # Direction breakdown
    dir_counts = Counter(e["direction"] for e in events)
    print(f"Direction:  BULL={dir_counts.get('BULL', 0)}  BEAR={dir_counts.get('BEAR', 0)}")

    # Session distribution
    sess_counts = Counter(e["session"] for e in events)
    sess_parts = [f"{k}={v}" for k, v in sorted(sess_counts.items())]
    print(f"Sessions:   {', '.join(sess_parts)}")

    print(f"Avg displacement quality: {result['avg_displacement_quality']:.3f}\n")

    # Detail table
    header = f"{'ID':<10} {'Time':<8} {'Dir':<5} {'Close':>8} {'CP':>8} {'Displ':>6} {'Session':<8} {'Status':<10}"
    print(header)
    print("-" * len(header))

    for e in events:
        ts = e["timestamp"]
        try:
            time_str = datetime.fromisoformat(ts).strftime("%H:%M")
        except Exception:
            time_str = ts[:5]
        status = "ACCEPTED" if e["is_accepted"] else "REJECTED"
        print(
            f"{e['id']:<10} {time_str:<8} {e['direction']:<5} "
            f"${e['price']:>6.2f} "
            f"${e['control_point_price']:>6.2f} "
            f"{e['displacement_quality']:>6.3f} "
            f"{e['session']:<8} "
            f"{status:<10}"
        )
        if not e["is_accepted"] and e.get("rejection_reason"):
            print(f"{'':>10} -> {e['rejection_reason']}")

        if verbose:
            dp = f"{e['distance_to_pdh']:+.2f}" if e.get("distance_to_pdh") is not None else "—"
            dl = f"{e['distance_to_pdl']:+.2f}" if e.get("distance_to_pdl") is not None else "—"
            print(f"{'':>10}    dPDH={dp}  dPDL={dl}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(prog="bot-cli", description="Bot tooling CLI")
    sub = parser.add_subparsers(dest="command")

    # test-displacement
    td = sub.add_parser("test-displacement", help="Analyse displacement candles for a date")
    td.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: last trading day)")
    td.add_argument("--symbol", type=str, default="SPY", help="Ticker symbol (default: SPY)")

    # detect-mss
    dm = sub.add_parser("detect-mss", help="Detect MSS events for a date")
    dm.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: last trading day)")
    dm.add_argument("--symbol", type=str, default="SPY", help="Ticker symbol (default: SPY)")
    dm.add_argument("--verbose", action="store_true", help="Show PDH/PDL distances for each event")

    args = parser.parse_args()
    if args.command == "test-displacement":
        cmd_test_displacement(args)
    elif args.command == "detect-mss":
        cmd_detect_mss(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
