"""Identify swing high/low control points for Market Structure Shift detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ControlPoint:
    price: float
    time: datetime
    type: str  # 'HIGH' or 'LOW'


def identify_control_points(
    candles: List[dict],
    lookback: int = 5,
) -> List[ControlPoint]:
    """Detect swing highs and lows using pivot-point logic.

    A swing high at index *i* means ``candles[i]['high']`` is the maximum
    high in the window ``[i - lookback, i + lookback]``.  Swing lows are
    defined symmetrically on the ``low`` field.

    Args:
        candles: List of candle dicts with keys ``high``, ``low``, ``close``,
                 ``time`` (ISO string or datetime).
        lookback: Number of candles on each side of the pivot.

    Returns:
        Control points sorted by time ascending.
    """
    points: List[ControlPoint] = []

    for i in range(lookback, len(candles) - lookback):
        window = candles[i - lookback : i + lookback + 1]

        # Swing High: candle i has the highest high in the window
        if candles[i]["high"] == max(c["high"] for c in window):
            ts = _parse_time(candles[i]["time"])
            points.append(ControlPoint(price=candles[i]["high"], time=ts, type="HIGH"))

        # Swing Low: candle i has the lowest low in the window
        if candles[i]["low"] == min(c["low"] for c in window):
            ts = _parse_time(candles[i]["time"])
            points.append(ControlPoint(price=candles[i]["low"], time=ts, type="LOW"))

    points.sort(key=lambda cp: cp.time)
    return points


def _parse_time(value: object) -> datetime:
    """Coerce a time value to datetime."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
