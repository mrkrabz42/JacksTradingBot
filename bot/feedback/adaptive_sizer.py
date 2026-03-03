"""Adaptive position sizer — converts Kelly fraction to effective risk percentage.

Safety invariant: Kelly can only REDUCE risk from the 2% cap, never exceed it.
"""

from bot.config import MAX_RISK_PER_TRADE

# Hard limits — NEVER breached
FLOOR_RISK_PCT = 0.005   # 0.5% — always have skin in the game
CAP_RISK_PCT = MAX_RISK_PER_TRADE  # 2% — existing hard cap

# Minimum trades before adaptation kicks in
MIN_TRADES_FOR_ADAPTATION = 10


def effective_risk_pct(kelly_fraction: float, trade_count: int) -> float:
    """Convert Kelly fraction to an effective risk percentage.

    Args:
        kelly_fraction: Half-Kelly fraction from scorecard (0–1).
        trade_count: Number of closed trades for this strategy.

    Returns:
        Effective risk as a decimal (e.g. 0.015 = 1.5%).
        Clamped to [0.5%, 2.0%]. Returns 2% if trade_count < 10.
    """
    # Not enough data — use full default risk (no adaptation)
    if trade_count < MIN_TRADES_FOR_ADAPTATION:
        return CAP_RISK_PCT

    # Scale: effective = cap × kelly_fraction
    risk = CAP_RISK_PCT * kelly_fraction

    # Clamp to [floor, cap]
    risk = max(FLOOR_RISK_PCT, min(CAP_RISK_PCT, risk))

    return risk
