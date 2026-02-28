"""MSS Acceptance Validator — Bonsai 2-candle rule.

After an MSS fires, the next 2 candles must NOT close back across the
broken control point.  If either candle closes back, the MSS is
rejected (false breakout).  If both hold, the MSS is accepted.

Bull MSS: next 2 candles must NOT close below the control point.
Bear MSS: next 2 candles must NOT close above the control point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from bot.strategy.structure.mss_detector import MSS

ACCEPTANCE_CANDLES = 2  # how many candles to check


@dataclass
class AcceptanceResult:
    is_accepted: bool
    checked_candles: int           # how many candles were available to check
    rejection_candle_index: Optional[int]  # 0-based index of the candle that caused rejection
    rejection_reason: Optional[str]


def check_acceptance(
    mss: MSS,
    next_candles: List[dict],
) -> AcceptanceResult:
    """Validate the 2-candle acceptance rule for an MSS event.

    Args:
        mss: The MSS event to validate.
        next_candles: The candles immediately following the trigger candle,
                      ordered oldest-first.  At most the first
                      ``ACCEPTANCE_CANDLES`` are inspected.

    Returns:
        AcceptanceResult with pass/fail and optional rejection reason.
    """
    cp_price = mss.control_point.price
    to_check = next_candles[:ACCEPTANCE_CANDLES]

    if not to_check:
        return AcceptanceResult(
            is_accepted=False,
            checked_candles=0,
            rejection_candle_index=None,
            rejection_reason="no candles available after MSS trigger",
        )

    for i, candle in enumerate(to_check):
        close = candle["close"]

        if mss.direction == "BULL" and close < cp_price:
            return AcceptanceResult(
                is_accepted=False,
                checked_candles=i + 1,
                rejection_candle_index=i,
                rejection_reason=f"candle {i+1} closed at {close:.2f}, below CP {cp_price:.2f}",
            )

        if mss.direction == "BEAR" and close > cp_price:
            return AcceptanceResult(
                is_accepted=False,
                checked_candles=i + 1,
                rejection_candle_index=i,
                rejection_reason=f"candle {i+1} closed at {close:.2f}, above CP {cp_price:.2f}",
            )

    return AcceptanceResult(
        is_accepted=True,
        checked_candles=len(to_check),
        rejection_candle_index=None,
        rejection_reason=None,
    )


def validate_mss_acceptance(
    events: List[MSS],
    candles: List[dict],
) -> List[MSS]:
    """Run acceptance checks on all MSS events and update them in-place.

    Finds the trigger candle index in the candle list for each MSS, then
    passes the next candles to ``check_acceptance``.

    Args:
        events: MSS events (from ``detect_mss``).
        candles: The full candle list used for detection, ordered oldest-first.

    Returns:
        The same list of MSS events with ``is_accepted`` and
        ``rejection_reason`` fields populated.
    """
    # Build a time→index lookup for O(1) trigger candle location
    time_index: dict = {}
    for idx, c in enumerate(candles):
        t = c["time"]
        key = t.isoformat() if hasattr(t, "isoformat") else str(t)
        time_index[key] = idx

    for mss in events:
        t = mss.timestamp
        key = t.isoformat() if hasattr(t, "isoformat") else str(t)
        trigger_idx = time_index.get(key)

        if trigger_idx is None:
            mss.is_accepted = False
            mss.rejection_reason = "trigger candle not found in candle list"
            continue

        following = candles[trigger_idx + 1: trigger_idx + 1 + ACCEPTANCE_CANDLES]
        result = check_acceptance(mss, following)
        mss.is_accepted = result.is_accepted
        mss.rejection_reason = result.rejection_reason

    return events
