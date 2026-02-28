from __future__ import annotations


def calculate_atr(candles: list[dict], period: int = 14) -> float:
    """Calculate Average True Range over the given period.

    Args:
        candles: List of dicts with 'high', 'low', 'close' keys,
                 ordered oldest-first.
        period: Lookback window (default 14).

    Returns:
        ATR value as a float.

    Raises:
        ValueError: If not enough candles for the given period.
    """
    if len(candles) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} candles, got {len(candles)}"
        )

    true_ranges: list[float] = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    # SMA of the last `period` true ranges
    return sum(true_ranges[-period:]) / period
