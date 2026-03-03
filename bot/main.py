"""Entry point — Market Analysis Assistant (v2).

On startup: logs account info and current positions for context.
Every 5 minutes during market hours:
  1. Run market scanner on watchlist
  2. For each signal — run enriched snapshot pipeline:
       OHLCV → MarketSnapshot → session → volatility → regime → trend
       → volume → liquidity → participation → MTF → confluence → context
  3. Log context flags, environment summary, setup grade
  4. Report analysis results (no trade execution)
"""

import signal
import sys
import time

import schedule
from loguru import logger

from bot.config import SCAN_INTERVAL_MINUTES, ALPACA_PAPER_TRADE
from bot.data.market_data import get_account_info, get_positions, get_historical_bars, get_latest_quote
from bot.scanner.market_scanner import scan_watchlist
from bot.strategies.base_strategy import Signal
from bot.utils.helpers import is_market_open
from bot.pipeline.snapshot_pipeline import build_enriched_snapshot, get_latest_context

# Feedback loop
from bot.storage.trade_journal import TradeJournal
from bot.feedback.strategy_scorecard import StrategyScorecard
from bot.feedback import adaptive_sizer

# Initialize logger (triggers log file setup)
import bot.utils.logger  # noqa: F401


_shutdown = False


def handle_shutdown(signum, frame):
    """Graceful shutdown on Ctrl+C."""
    global _shutdown
    logger.info("Shutdown signal received — stopping analysis...")
    _shutdown = True


def log_startup_info():
    """Log account summary on startup."""
    logger.info("=" * 60)
    logger.info("ROAD TO 10K v2 — Market Analysis Assistant")
    logger.info("Mode: ANALYSIS ONLY (execution disabled)")
    logger.info("=" * 60)

    try:
        account = get_account_info()
        positions = get_positions()

        logger.info(f"Portfolio Value: ${account['portfolio_value']:,.2f}")
        logger.info(f"Buying Power:   ${account['buying_power']:,.2f}")
        logger.info(f"Open Positions: {len(positions)}")

        for pos in positions:
            logger.info(
                f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['entry_price']:.2f} "
                f"(P&L: ${pos['unrealized_pnl']:.2f})"
            )
    except Exception as e:
        logger.warning(f"Could not fetch account info: {e}")


def _run_pipeline_for_signal(symbol: str, df_bars) -> dict:
    """Run the full enriched snapshot pipeline for a signal symbol.

    Returns a context dict (empty dict on failure so caller can proceed safely).
    """
    try:
        snap_df = build_enriched_snapshot(symbol, df_bars, timeframe="day", store=True)
        ctx = get_latest_context(snap_df)

        logger.info(f"[{symbol}] ── Analysis ─────────────────────────────────────")
        logger.info(f"[{symbol}] {ctx['environment_summary']}")
        logger.info(f"[{symbol}] Flags: {' | '.join(ctx['context_flags']) if ctx['context_flags'] else 'none'}")
        logger.info(
            f"[{symbol}] Setup: {ctx['setup_grade']} | "
            f"Confluence: {ctx.get('confluence_score', 0):.0f} | "
            f"Bias: {ctx['bar_trade_bias']}"
        )
        logger.info(
            f"[{symbol}] Regime: {ctx['regime']} | "
            f"Vol: {ctx['volatility_state']} | "
            f"Trend: {ctx['trend_direction']} ({ctx.get('trend_strength_score', 0):.0f})"
        )
        logger.info(
            f"[{symbol}] Liquidity draw: {ctx['liquidity_draw_direction']} | "
            f"MTF: {ctx['mtf_alignment_state']}"
        )
        if ctx.get("nearest_liquidity"):
            logger.info(f"[{symbol}] Nearest liquidity: {ctx['nearest_liquidity']}")
        logger.info(f"[{symbol}] ─────────────────────────────────────────────────")

        return ctx

    except Exception as exc:
        logger.warning(f"[{symbol}] Pipeline failed — proceeding without context: {exc}")
        return {}


# ── Module-level feedback components ─────────────────────────────────────────

_journal = TradeJournal()
_scorecard = StrategyScorecard(_journal)


def run_scan_cycle():
    """One full scan → analyze → report cycle (no execution)."""
    if not is_market_open():
        logger.debug("Market is closed — skipping scan")
        return

    logger.info("--- Starting analysis cycle ---")

    # Refresh strategy scorecard from closed trades
    _scorecard.refresh()

    # Build strategy scores dict for the aggregator
    all_scores = _scorecard.get_all_scores()
    strategy_scores = {
        k.split(":")[0]: v["composite_score"]
        for k, v in all_scores.items()
        if k.endswith(":ALL")
    }

    # 1. Scan watchlist for signals (with scorecard weighting)
    signals = scan_watchlist(strategy_scores=strategy_scores)

    if not signals:
        logger.info("No actionable signals this cycle")
        return

    # 2. Run analysis pipeline for each signal
    for sig in signals:
        symbol = sig["symbol"]
        signal_type = sig["signal"]
        strategy_name = sig.get("strategy", "unknown")
        confidence = sig.get("confidence", 0.7)

        try:
            if signal_type == Signal.SELL.value:
                logger.info(f"[{symbol}] SELL signal detected — logging for review (no execution)")
                continue

            if signal_type == Signal.BUY.value:
                logger.info(f"[{symbol}] BUY signal detected — running full analysis pipeline")

                # Compute Kelly-adjusted risk for this strategy
                kelly_f = _scorecard.get_kelly_fraction(strategy_name)
                trade_count = _scorecard.get_trade_count(strategy_name)
                effective_risk = adaptive_sizer.effective_risk_pct(kelly_f, trade_count)

                logger.info(
                    f"[{symbol}] Adaptive sizing: Kelly={kelly_f:.2f} "
                    f"trades={trade_count} → risk={effective_risk:.1%} "
                    f"confidence={confidence:.2f}"
                )

                # Fetch bars for pipeline
                df_bars = get_historical_bars(symbol, timeframe="day", days_back=200)

                # Run full enriched snapshot pipeline
                ctx = _run_pipeline_for_signal(symbol, df_bars)
                regime = ctx.get("regime", "TRANSITION") if ctx else "TRANSITION"

                if ctx:
                    logger.info(
                        f"[{symbol}] ANALYSIS COMPLETE — "
                        f"Grade: {ctx.get('setup_grade', 'N/A')} | "
                        f"Bias: {ctx.get('bar_trade_bias', 'N/A')} | "
                        f"Risk: {effective_risk:.1%}"
                    )

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            continue

    logger.info("--- Analysis cycle complete ---")


def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    log_startup_info()

    # Schedule analysis cycle
    schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(run_scan_cycle)

    # Run once immediately
    run_scan_cycle()

    logger.info(f"Analyzer running — scanning every {SCAN_INTERVAL_MINUTES} minutes during market hours")
    logger.info("Press Ctrl+C to stop")

    while not _shutdown:
        schedule.run_pending()
        time.sleep(1)

    _journal.close()
    logger.info("Analyzer stopped. Goodbye.")


if __name__ == "__main__":
    main()
