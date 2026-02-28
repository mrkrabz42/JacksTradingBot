"""MSS (Market Structure Shift) Detector — Bonsai framework.

Detects when a candle BODY closes beyond a control point, creating a
Market Structure Shift.  Only body closes count — wick touches are
liquidity sweeps, not structure shifts.

Bull MSS: body close ABOVE the most recent swing high control point,
          with valid displacement.
Bear MSS: body close BELOW the most recent swing low control point,
          with valid displacement.
"""
from __future__ import annotations

import csv
import itertools
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from bot.sessions.classifier import get_session
from bot.strategy.structure.control_points import ControlPoint
from bot.strategy.structure.displacement import (
    analyze_displacement,
    displacement_quality,
    is_displacement,
)

_COUNTER = itertools.count(1)

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_FILE = _LOG_DIR / "mss_history.csv"

_CSV_FIELDS = [
    "mss_id",
    "timestamp",
    "direction",
    "trigger_close",
    "control_point_price",
    "control_point_time",
    "displacement_score",
    "session",
    "accepted",
    "rejection_reason",
    "distance_to_pdh",
    "distance_to_pdl",
]


@dataclass
class MSS:
    id: str
    timestamp: datetime
    direction: str  # 'BULL' or 'BEAR'
    trigger_candle: dict
    control_point: ControlPoint
    displacement_quality: float
    session_context: str  # 'ASIA', 'LONDON', 'NY', 'OUTSIDE'
    distance_to_pdh: Optional[float] = None
    distance_to_pdl: Optional[float] = None
    distance_to_session_high: Optional[float] = None
    distance_to_session_low: Optional[float] = None
    is_accepted: Optional[bool] = field(default=None)
    rejection_reason: Optional[str] = field(default=None)


def _parse_time(value: object) -> datetime:
    """Coerce a time value to a timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _next_id() -> str:
    return f"MSS_{next(_COUNTER):03d}"


def detect_mss(
    candles: List[dict],
    control_points: List[ControlPoint],
    atr_value: float,
    *,
    pdh: Optional[float] = None,
    pdl: Optional[float] = None,
    session_extremes: Optional[List[dict]] = None,
) -> List[MSS]:
    """Detect all MSS events in the candle data.

    For each candle, checks whether its body close crosses the most
    recent swing high (bull MSS) or swing low (bear MSS).  A valid
    displacement on the trigger candle is required.

    Args:
        candles: 1-min candle dicts with keys ``open``, ``high``, ``low``,
                 ``close``, ``time``.  Ordered oldest-first.
        control_points: Sorted list of ControlPoints (from
                        ``identify_control_points``).
        atr_value: ATR(14) for displacement validation.
        pdh: Previous Day High (for distance context).
        pdl: Previous Day Low (for distance context).
        session_extremes: List of session dicts (from
                          ``calculate_session_extremes``) for distance context.

    Returns:
        List of MSS objects sorted by timestamp.
    """
    if not control_points or not candles:
        return []

    # Build a lookup for session highs/lows
    sess_hl: Dict[str, dict] = {}
    if session_extremes:
        for s in session_extremes:
            sess_hl[s["session"]] = s

    events: List[MSS] = []

    # Track the latest HIGH and LOW control points seen so far.
    # A CP is "active" once the candle time is past the CP time.
    latest_high: Optional[ControlPoint] = None
    latest_low: Optional[ControlPoint] = None
    cp_idx = 0  # pointer into the sorted control_points list

    # Track which CPs have already been used to fire an MSS so we
    # don't trigger duplicates on the same CP.
    used_cp_ids: set = set()

    for candle in candles:
        candle_time = _parse_time(candle["time"])

        # Advance the CP pointer: activate any CP whose time <= candle_time
        while cp_idx < len(control_points) and _parse_time(control_points[cp_idx].time) <= candle_time:
            cp = control_points[cp_idx]
            if cp.type == "HIGH":
                latest_high = cp
            else:
                latest_low = cp
            cp_idx += 1

        body_close = candle["close"]

        # --- Bull MSS: body close above last swing high ---
        if latest_high is not None and id(latest_high) not in used_cp_ids:
            if body_close > latest_high.price:
                if is_displacement(candle, atr_value):
                    mss = _build_mss(
                        direction="BULL",
                        candle=candle,
                        cp=latest_high,
                        atr_value=atr_value,
                        candle_time=candle_time,
                        pdh=pdh,
                        pdl=pdl,
                        sess_hl=sess_hl,
                    )
                    events.append(mss)
                    used_cp_ids.add(id(latest_high))

        # --- Bear MSS: body close below last swing low ---
        if latest_low is not None and id(latest_low) not in used_cp_ids:
            if body_close < latest_low.price:
                if is_displacement(candle, atr_value):
                    mss = _build_mss(
                        direction="BEAR",
                        candle=candle,
                        cp=latest_low,
                        atr_value=atr_value,
                        candle_time=candle_time,
                        pdh=pdh,
                        pdl=pdl,
                        sess_hl=sess_hl,
                    )
                    events.append(mss)
                    used_cp_ids.add(id(latest_low))

    events.sort(key=lambda m: m.timestamp)
    return events


def _build_mss(
    *,
    direction: str,
    candle: dict,
    cp: ControlPoint,
    atr_value: float,
    candle_time: datetime,
    pdh: Optional[float],
    pdl: Optional[float],
    sess_hl: Dict[str, dict],
) -> MSS:
    """Construct an MSS object with all context fields."""
    session = get_session(candle_time)
    dq = displacement_quality(candle, atr_value)
    close = candle["close"]

    # Distance to PDH/PDL
    dist_pdh = round(close - pdh, 4) if pdh is not None else None
    dist_pdl = round(close - pdl, 4) if pdl is not None else None

    # Distance to current session high/low
    dist_sh: Optional[float] = None
    dist_sl: Optional[float] = None
    if session in sess_hl:
        sh = sess_hl[session].get("high")
        sl = sess_hl[session].get("low")
        if sh is not None:
            dist_sh = round(close - sh, 4)
        if sl is not None:
            dist_sl = round(close - sl, 4)

    return MSS(
        id=_next_id(),
        timestamp=candle_time,
        direction=direction,
        trigger_candle=candle,
        control_point=cp,
        displacement_quality=dq,
        session_context=session,
        distance_to_pdh=dist_pdh,
        distance_to_pdl=dist_pdl,
        distance_to_session_high=dist_sh,
        distance_to_session_low=dist_sl,
    )


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------

def log_mss_events(events: List[MSS]) -> Path:
    """Append MSS events to the history CSV.  Returns the log file path."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not _LOG_FILE.exists()

    with open(_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for mss in events:
            writer.writerow({
                "mss_id": mss.id,
                "timestamp": mss.timestamp.isoformat(),
                "direction": mss.direction,
                "trigger_close": mss.trigger_candle["close"],
                "control_point_price": mss.control_point.price,
                "control_point_time": mss.control_point.time.isoformat(),
                "displacement_score": mss.displacement_quality,
                "session": mss.session_context,
                "accepted": mss.is_accepted,
                "rejection_reason": mss.rejection_reason or "",
                "distance_to_pdh": mss.distance_to_pdh,
                "distance_to_pdl": mss.distance_to_pdl,
            })

    return _LOG_FILE
