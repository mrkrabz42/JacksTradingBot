"""Multi-strategy signal aggregator with scorecard-weighted confidence.

Runs multiple strategies per symbol, adjusts confidence by strategy score,
and applies adaptive thresholds for hot/cold strategies.
"""

from __future__ import annotations

from loguru import logger

from bot.strategies.base_strategy import BaseStrategy, Signal


# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_CONFIDENCE_THRESHOLD = 0.7
MIN_THRESHOLD = 0.6        # floor for hot strategies
SCORE_ADJUSTMENT_RANGE = 0.2  # confidence adjustment: (score - 0.5) * 0.2 → [-0.1, +0.1]


class StrategyResult:
    """Result from a single strategy evaluation."""

    __slots__ = ("strategy_name", "signal", "confidence")

    def __init__(self, strategy_name: str, signal: Signal, confidence: float = 0.7):
        self.strategy_name = strategy_name
        self.signal = signal
        self.confidence = confidence


class MultiStrategyAggregator:
    """Aggregates signals from multiple strategies with scorecard weighting."""

    def __init__(self, strategy_scores: dict[str, float] | None = None):
        """
        Args:
            strategy_scores: Mapping of strategy_name → composite score (0–1).
                             None or empty dict = no adjustment (defaults).
        """
        self._scores = strategy_scores or {}

    def evaluate(
        self,
        symbol: str,
        strategies: list[BaseStrategy],
        df,
    ) -> list[dict]:
        """Run all strategies on a symbol and return scored results.

        Returns:
            List of dicts: {symbol, signal, strategy, confidence}
            Only includes non-HOLD signals that pass the adjusted threshold.
        """
        results: list[StrategyResult] = []

        for strat in strategies:
            try:
                sig = strat.evaluate(df)
                if sig == Signal.HOLD:
                    continue
                results.append(StrategyResult(strat.name, sig, confidence=0.7))
            except Exception as e:
                logger.warning(f"[{symbol}] Strategy {strat.name} failed: {e}")
                continue

        if not results:
            return []

        # Apply scorecard confidence adjustment per result
        for result in results:
            score = self._scores.get(result.strategy_name, 0.5)
            adjustment = (score - 0.5) * SCORE_ADJUSTMENT_RANGE  # range: [-0.1, +0.1]
            result.confidence += adjustment
            result.confidence = max(0.0, min(1.0, result.confidence))

        # Filter by adjusted threshold
        passing = []
        for result in results:
            threshold = self._adjusted_threshold(result.strategy_name)
            if result.confidence >= threshold:
                passing.append({
                    "symbol": symbol,
                    "signal": result.signal.value,
                    "strategy": result.strategy_name,
                    "confidence": round(result.confidence, 3),
                })
            else:
                logger.debug(
                    f"[{symbol}] {result.strategy_name} signal filtered: "
                    f"confidence={result.confidence:.2f} < threshold={threshold:.2f}"
                )

        return passing

    def _adjusted_threshold(self, strategy_name: str) -> float:
        """Lower threshold for strategies with score >= 0.7 (proven performers)."""
        score = self._scores.get(strategy_name, 0.5)
        if score >= 0.7:
            # Scale: score 0.7→threshold 0.7, score 1.0→threshold 0.6
            reduction = (score - 0.7) / 0.3 * 0.1  # up to 0.1 reduction
            return max(MIN_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD - reduction)
        return DEFAULT_CONFIDENCE_THRESHOLD
