"""Trade execution — DISABLED in v2 (analysis-only mode).

All functions are stubbed to log warnings. Import signatures are preserved
so that any code referencing these functions continues to work without errors.
"""

from loguru import logger


def place_bracket_order(
    symbol: str,
    qty: int,
    side: str,
    stop_loss_price: float,
    limit_price: float | None = None,
) -> dict | None:
    """Stub — logs warning instead of placing an order."""
    logger.warning(
        f"EXECUTION DISABLED: Would have placed {side.upper()} {qty}x {symbol} "
        f"(stop: ${stop_loss_price:.2f}) — v2 is analysis-only"
    )
    return None


def close_position(symbol: str) -> dict | None:
    """Stub — logs warning instead of closing a position."""
    logger.warning(
        f"EXECUTION DISABLED: Would have closed position {symbol} — v2 is analysis-only"
    )
    return None


def get_open_orders() -> list[dict]:
    """Stub — returns empty list."""
    logger.warning("EXECUTION DISABLED: get_open_orders called — v2 is analysis-only")
    return []
