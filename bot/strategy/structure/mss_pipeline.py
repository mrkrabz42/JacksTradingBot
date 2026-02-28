"""Master MSS pipeline — integrates all Phase 3 sessions.

Runs the full Market Structure Shift analysis:
  1. Load 1-min candles for date
  2. Calculate ATR(14)           (Session 1)
  3. Identify control points     (Session 2)
  4. Detect displacement candles (Session 3)
  5. Detect MSS events           (Session 4)
  6. Validate acceptance          (Session 5)
  7. Integrate session liquidity context
  8. Log to CSV
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger

from bot.data.market_data import get_historical_bars
from bot.indicators.atr import calculate_atr
from bot.sessions.classifier import get_session
from bot.sessions.extremes import calculate_daily_extremes, calculate_session_extremes
from bot.strategy.structure.acceptance import validate_mss_acceptance
from bot.strategy.structure.control_points import identify_control_points
from bot.strategy.structure.displacement import analyze_displacement
from bot.strategy.structure.mss_detector import detect_mss, log_mss_events


def run_mss_pipeline(
    symbol: str = "SPY",
    date: Optional[str] = None,
) -> dict:
    """Run the complete MSS analysis pipeline for a given date.

    Args:
        symbol: Ticker symbol.
        date: YYYY-MM-DD string.  If None, walks backward from today to
              find the most recent trading day.

    Returns:
        Dict with full pipeline results (JSON-serialisable).
    """
    # Resolve date
    if date:
        day = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Walk backward to find a trading day
    df = None
    for offset in range(10):
        d = day - timedelta(days=offset)
        d_end = d + timedelta(days=1)
        df = get_historical_bars(symbol, timeframe="minute", start=d, end=d_end)
        if len(df) > 0:
            day = d
            break
    else:
        return _empty_result(symbol, date or "unknown")

    date_str = day.strftime("%Y-%m-%d")

    # Build candle dicts
    candles: list[dict] = []
    for ts, row in df.iterrows():
        ts_dt = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
        if ts_dt.tzinfo is None:
            ts_dt = ts_dt.replace(tzinfo=timezone.utc)
        candles.append({
            "time": ts_dt,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        })

    if len(candles) < 15:
        return _empty_result(symbol, date_str)

    # 1. ATR
    atr_value = calculate_atr(candles, period=14)

    # 2. Control points
    cps = identify_control_points(candles, lookback=5)

    # 3. Context
    naive_day = day.replace(tzinfo=None)
    sess_extremes = calculate_session_extremes(symbol, naive_day)
    daily = calculate_daily_extremes(symbol, naive_day)
    pdh = daily.get("pdh")
    pdl = daily.get("pdl")

    # 4. Detect MSS
    events = detect_mss(
        candles, cps, atr_value,
        pdh=pdh, pdl=pdl, session_extremes=sess_extremes,
    )

    # 5. Acceptance
    validate_mss_acceptance(events, candles)

    # 6. Log
    if events:
        log_mss_events(events)

    # 7. Build result
    accepted = [m for m in events if m.is_accepted]
    rejected = [m for m in events if not m.is_accepted]
    scores = [m.displacement_quality for m in events]
    avg_quality = round(sum(scores) / len(scores), 3) if scores else 0.0

    mss_list = []
    for m in events:
        mss_list.append({
            "id": m.id,
            "timestamp": m.timestamp.isoformat(),
            "direction": m.direction,
            "price": m.trigger_candle["close"],
            "control_point_price": m.control_point.price,
            "displacement_quality": m.displacement_quality,
            "is_accepted": m.is_accepted,
            "rejection_reason": m.rejection_reason,
            "session": m.session_context,
            "distance_to_pdh": m.distance_to_pdh,
            "distance_to_pdl": m.distance_to_pdl,
        })

    return {
        "symbol": symbol,
        "date": date_str,
        "total_candles": len(candles),
        "atr": round(atr_value, 4),
        "control_points": len(cps),
        "total_mss": len(events),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "avg_displacement_quality": avg_quality,
        "pdh": pdh,
        "pdl": pdl,
        "events": mss_list,
    }


def _empty_result(symbol: str, date: str) -> dict:
    return {
        "symbol": symbol,
        "date": date,
        "total_candles": 0,
        "atr": 0.0,
        "control_points": 0,
        "total_mss": 0,
        "accepted": 0,
        "rejected": 0,
        "avg_displacement_quality": 0.0,
        "pdh": None,
        "pdl": None,
        "events": [],
    }
