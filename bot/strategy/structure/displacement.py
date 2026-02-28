"""Displacement candle validator — Bonsai framework.

A displacement candle is a strong directional move that validates
Market Structure Shifts. Only MSS accompanied by proper displacement
produce valid trading signals.

Three rules must ALL pass:
  1. Candle range >= 1.2 * ATR(14)
  2. Body >= 60% of candle range
  3. Opposing wick <= 20% of candle range
"""
from __future__ import annotations

from dataclasses import dataclass

# Thresholds (Bonsai defaults)
ATR_MULTIPLIER = 1.2
MIN_BODY_RATIO = 0.60
MAX_WICK_RATIO = 0.20


@dataclass
class DisplacementResult:
    is_displacement: bool
    quality_score: float   # 0.0-1.0
    range_ratio: float     # actual_range / (ATR_MULTIPLIER * atr)
    body_ratio: float      # body / range
    wick_ratio: float      # opposing_wick / range
    meets_size: bool       # Rule 1
    meets_body: bool       # Rule 2
    meets_wick: bool       # Rule 3


def is_displacement(candle: dict, atr_value: float) -> bool:
    """Return True if *candle* meets all three displacement criteria.

    Args:
        candle: Dict with keys ``open``, ``high``, ``low``, ``close``.
        atr_value: Current ATR(14) value for context.
    """
    return analyze_displacement(candle, atr_value).is_displacement


def displacement_quality(candle: dict, atr_value: float) -> float:
    """Return 0.0-1.0 score indicating displacement strength.

    1.0 = perfect displacement, 0.0 = not displacement at all.
    """
    return analyze_displacement(candle, atr_value).quality_score


def analyze_displacement(candle: dict, atr_value: float) -> DisplacementResult:
    """Full displacement analysis with per-rule breakdown.

    Args:
        candle: Dict with keys ``open``, ``high``, ``low``, ``close``.
        atr_value: Current ATR(14) value for context.

    Returns:
        DisplacementResult with pass/fail for each rule and quality score.
    """
    high = candle["high"]
    low = candle["low"]
    open_ = candle["open"]
    close = candle["close"]

    candle_range = high - low
    body_size = abs(close - open_)
    is_bullish = close > open_

    if is_bullish:
        opposing_wick = open_ - low   # lower wick (below body) works against bulls
    else:
        opposing_wick = high - open_  # upper wick (above body) works against bears

    # Avoid division by zero on doji / zero-range candles
    if candle_range <= 0 or atr_value <= 0:
        return DisplacementResult(
            is_displacement=False,
            quality_score=0.0,
            range_ratio=0.0,
            body_ratio=0.0,
            wick_ratio=1.0,
            meets_size=False,
            meets_body=False,
            meets_wick=False,
        )

    # --- Rule evaluation ---
    size_threshold = ATR_MULTIPLIER * atr_value
    range_ratio = candle_range / size_threshold
    body_ratio = body_size / candle_range
    wick_ratio = opposing_wick / candle_range

    meets_size = candle_range >= size_threshold   # Rule 1
    meets_body = body_ratio >= MIN_BODY_RATIO     # Rule 2
    meets_wick = wick_ratio <= MAX_WICK_RATIO     # Rule 3

    passed = meets_size and meets_body and meets_wick

    # --- Quality score (0.0 - 1.0) ---
    # Each component contributes a third of the score.
    # Score how far beyond (or below) threshold each metric is.
    size_score = min(range_ratio / 2.0, 1.0)                         # 2x ATR = perfect
    body_score = min((body_ratio - MIN_BODY_RATIO) / 0.40 + 0.5, 1.0)  # 100% body = perfect
    body_score = max(body_score, 0.0)
    wick_score = max(1.0 - wick_ratio / MAX_WICK_RATIO, 0.0)         # 0% wick = perfect

    quality = (size_score + body_score + wick_score) / 3.0
    # Clamp to zero if not a displacement candle
    if not passed:
        quality = min(quality, 0.49)

    return DisplacementResult(
        is_displacement=passed,
        quality_score=round(quality, 3),
        range_ratio=round(range_ratio, 3),
        body_ratio=round(body_ratio, 3),
        wick_ratio=round(wick_ratio, 3),
        meets_size=meets_size,
        meets_body=meets_body,
        meets_wick=meets_wick,
    )
