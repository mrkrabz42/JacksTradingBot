"""Strategy Scorecard — rolling performance metrics per strategy.

Reads closed trades from the trade journal, computes rolling metrics,
and stores composite scores + Kelly fractions in the strategy_scores table.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from bot.storage.trade_journal import TradeJournal


# ── Constants ────────────────────────────────────────────────────────────────

ROLLING_WINDOW = 50   # last N closed trades per strategy
MIN_TRADES = 10       # use defaults until this many trades
DEFAULT_SCORE = 0.5   # neutral score before enough data
DEFAULT_KELLY = 0.0   # no Kelly adjustment before enough data


class StrategyScorecard:
    """Computes and caches rolling performance metrics per strategy."""

    def __init__(self, journal: TradeJournal):
        self._journal = journal
        self._scores: dict[str, dict] = {}  # keyed by "strategy_name:regime"

    # ── Public API ───────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Recompute all strategy scores from closed trades. Called once per scan cycle."""
        strategy_names = self._journal.get_all_strategy_names()
        if not strategy_names:
            logger.debug("Scorecard: no closed trades yet — using defaults")
            return

        for name in strategy_names:
            # Overall score (regime=ALL)
            trades = self._journal.get_closed_trades_for_strategy(name, limit=ROLLING_WINDOW)
            self._compute_and_store(name, "ALL", trades)

            # Per-regime scores
            regimes = set(t.get("regime") for t in trades if t.get("regime"))
            for regime in regimes:
                regime_trades = self._journal.get_closed_trades_for_strategy(
                    name, limit=ROLLING_WINDOW, regime=regime
                )
                self._compute_and_store(name, regime, regime_trades)

        logger.info(f"Scorecard: refreshed {len(strategy_names)} strategies")

    def get_score(self, strategy_name: str, regime: str = "ALL") -> float:
        """Get composite score for a strategy (0–1). Returns DEFAULT_SCORE if insufficient data."""
        key = f"{strategy_name}:{regime}"
        entry = self._scores.get(key)
        if entry is None or entry["trade_count"] < MIN_TRADES:
            return DEFAULT_SCORE
        return entry["composite_score"]

    def get_kelly_fraction(self, strategy_name: str, regime: str = "ALL") -> float:
        """Get half-Kelly fraction for a strategy (0–1). Returns DEFAULT_KELLY if insufficient data."""
        key = f"{strategy_name}:{regime}"
        entry = self._scores.get(key)
        if entry is None or entry["trade_count"] < MIN_TRADES:
            return DEFAULT_KELLY
        return entry["kelly_fraction"]

    def get_trade_count(self, strategy_name: str) -> int:
        """Get number of closed trades for a strategy."""
        key = f"{strategy_name}:ALL"
        entry = self._scores.get(key)
        return entry["trade_count"] if entry else 0

    def get_all_scores(self) -> dict[str, dict]:
        """Return all cached scores for dashboard display."""
        return dict(self._scores)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _compute_and_store(self, strategy_name: str, regime: str, trades: list[dict]) -> None:
        """Compute metrics for a strategy+regime and persist to DB + cache."""
        trade_count = len(trades)
        if trade_count == 0:
            return

        # ── Compute metrics ──────────────────────────────────────────────────

        wins = [t for t in trades if (t.get("pnl") or 0) > 0]
        losses = [t for t in trades if (t.get("pnl") or 0) <= 0]

        win_rate = len(wins) / trade_count if trade_count > 0 else 0.0

        # Average PnL %
        pnl_pcts = [t.get("pnl_pct") or 0.0 for t in trades]
        avg_pnl_pct = sum(pnl_pcts) / len(pnl_pcts) if pnl_pcts else 0.0

        # Profit factor: gross_wins / gross_losses
        gross_wins = sum(t.get("pnl") or 0 for t in wins) if wins else 0.0
        gross_losses = abs(sum(t.get("pnl") or 0 for t in losses)) if losses else 0.0
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else (3.0 if gross_wins > 0 else 1.0)

        # Average R-multiple
        r_multiples = [t.get("r_multiple") or 0.0 for t in trades]
        avg_r_multiple = sum(r_multiples) / len(r_multiples) if r_multiples else 0.0

        # ── Composite score (0–1) ───────────────────────────────────────────

        pf_norm = min(profit_factor, 3.0) / 3.0                          # 0–1
        r_norm = min(max(avg_r_multiple, 0.0), 3.0) / 3.0                # 0–1
        pnl_sigmoid = avg_pnl_pct / (avg_pnl_pct + 0.02) if avg_pnl_pct > 0 else 0.0  # 0–1
        consistency = min(trade_count / ROLLING_WINDOW, 1.0)              # 0–1

        composite_score = (
            win_rate * 0.30
            + pf_norm * 0.25
            + r_norm * 0.25
            + pnl_sigmoid * 0.15
            + consistency * 0.05
        )
        composite_score = max(0.0, min(1.0, composite_score))

        # ── Kelly fraction (half-Kelly, clipped 0–1) ────────────────────────

        loss_rate = 1.0 - win_rate
        avg_win = (gross_wins / len(wins)) if wins else 0.0
        avg_loss = (gross_losses / len(losses)) if losses else 1.0  # avoid div-by-zero
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0

        kelly_f = win_rate - (loss_rate / win_loss_ratio) if win_loss_ratio > 0 else 0.0
        half_kelly = kelly_f * 0.5
        half_kelly = max(0.0, min(1.0, half_kelly))

        # ── Store ────────────────────────────────────────────────────────────

        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "strategy_name": strategy_name,
            "regime": regime,
            "win_rate": round(win_rate, 4),
            "avg_pnl_pct": round(avg_pnl_pct, 6),
            "profit_factor": round(profit_factor, 4),
            "avg_r_multiple": round(avg_r_multiple, 4),
            "trade_count": trade_count,
            "composite_score": round(composite_score, 4),
            "kelly_fraction": round(half_kelly, 4),
            "updated_at": now,
        }

        # Cache
        key = f"{strategy_name}:{regime}"
        self._scores[key] = entry

        # Persist to strategy_scores table
        self._journal.conn.execute(
            """INSERT INTO strategy_scores
               (strategy_name, regime, win_rate, avg_pnl_pct, profit_factor,
                avg_r_multiple, trade_count, composite_score, kelly_fraction, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(strategy_name, regime)
               DO UPDATE SET
                 win_rate = excluded.win_rate,
                 avg_pnl_pct = excluded.avg_pnl_pct,
                 profit_factor = excluded.profit_factor,
                 avg_r_multiple = excluded.avg_r_multiple,
                 trade_count = excluded.trade_count,
                 composite_score = excluded.composite_score,
                 kelly_fraction = excluded.kelly_fraction,
                 updated_at = excluded.updated_at""",
            (strategy_name, regime, entry["win_rate"], entry["avg_pnl_pct"],
             entry["profit_factor"], entry["avg_r_multiple"], entry["trade_count"],
             entry["composite_score"], entry["kelly_fraction"], now),
        )
        self._journal.conn.commit()

        logger.debug(
            f"Scorecard [{strategy_name}/{regime}]: "
            f"WR={win_rate:.0%} PF={profit_factor:.2f} R={avg_r_multiple:.2f} "
            f"Score={composite_score:.2f} Kelly={half_kelly:.2f} ({trade_count} trades)"
        )
