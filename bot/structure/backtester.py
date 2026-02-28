"""Backtester for the Order Flow & Liquidity MSS framework."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from bot.structure.config import StructureConfig
from bot.structure.swing_engine import detect_swings, classify_trend
from bot.structure.liquidity_map import build_liquidity_map
from bot.structure.mss_orchestrator import MSSOrchestrator


# Session definitions (UTC hours)
_SESSIONS = [
    ("ASIA", 0, 6),
    ("LONDON", 7, 12),
    ("NY", 13, 21),
]


def _detect_session(timestamp: Any) -> str:
    """Map a timestamp to its trading session."""
    hour = timestamp.hour if hasattr(timestamp, "hour") else 0
    for name, start, end in _SESSIONS:
        if start <= hour <= end:
            return name
    return "OUTSIDE"


def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR(period) from OHLCV DataFrame."""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


class MSSBacktester:
    """Run the full MSS pipeline over historical OHLCV data.

    Usage:
        config = StructureConfig()
        bt = MSSBacktester(config)
        results = bt.run(df_5min, htf_df=df_4h)
        metrics = bt.analyze()
    """

    def __init__(self, config: Optional[StructureConfig] = None) -> None:
        if config is None:
            config = StructureConfig()
        self.config = config
        self.orchestrator = MSSOrchestrator(config)
        self.results: List[Dict[str, Any]] = []

    def run(
        self,
        df: pd.DataFrame,
        htf_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, Any]]:
        """Run backtest over historical OHLCV data.

        Args:
            df: Execution-timeframe bars (e.g. 5M). Must have lowercase columns:
                time, open, high, low, close, volume
            htf_df: Higher-timeframe bars (e.g. 4H) for trend bias. Same columns.

        Returns:
            List of MSS results with forward returns attached.
        """
        cfg = self.config
        atr_period = cfg.backtest.atr_period
        vol_sma_period = cfg.order_flow.vol_sma_period
        warmup = max(atr_period, vol_sma_period) + 5

        # Pre-calculate rolling indicators
        df = df.copy()
        df["atr"] = _calculate_atr(df, atr_period)
        df["vol_sma"] = df["volume"].rolling(vol_sma_period).mean()

        # Pre-calculate HTF bias per date
        htf_bias_map: Dict[Any, str] = {}
        if htf_df is not None:
            htf_swings = detect_swings(htf_df, cfg.swing)
            for i in range(len(htf_df)):
                recent = [s for s in htf_swings if s["index"] <= i][-6:]
                date_key = htf_df["time"].iloc[i]
                if hasattr(date_key, "date"):
                    date_key = date_key.date()
                htf_bias_map[date_key] = classify_trend(recent, cfg.swing)

        # Pre-calculate PDH/PDL per day
        df_dates = df.copy()
        df_dates["_date"] = pd.to_datetime(df_dates["time"]).dt.date
        daily = df_dates.groupby("_date").agg(
            pdh=("high", "max"), pdl=("low", "min")
        ).shift(1)

        self.orchestrator.reset()
        self.results = []
        total_bars = len(df)

        logger.info(f"Starting backtest: {total_bars} bars, warmup={warmup}")

        for i in range(warmup, total_bars):
            candle = df.iloc[i].to_dict()

            # Module 1: Detect swings on a rolling window
            window_start = max(0, i - 200)
            window_df = df.iloc[window_start : i + 1].copy()
            window_df = window_df.reset_index(drop=True)
            swings = detect_swings(window_df, cfg.swing)
            trend = classify_trend(swings, cfg.swing)

            # Get date for PDH/PDL and HTF bias lookup
            candle_time = candle.get("time")
            today = candle_time.date() if hasattr(candle_time, "date") else candle_time

            if today not in daily.index:
                continue
            pdh = daily.loc[today, "pdh"]
            pdl = daily.loc[today, "pdl"]
            if pd.isna(pdh) or pd.isna(pdl):
                continue

            # Module 2: Build liquidity map
            pools = build_liquidity_map(
                swings, candle["close"], float(pdh), float(pdl), config=cfg.liquidity
            )

            session = _detect_session(candle_time)
            htf_bias = htf_bias_map.get(today, "RANGING")

            # Module 5: Orchestrate (internally calls Modules 3 & 4)
            vol_sma = candle.get("vol_sma", 0)
            if pd.isna(vol_sma):
                vol_sma = 0
            atr_val = candle.get("atr", 0)
            if pd.isna(atr_val):
                atr_val = 0

            mss = self.orchestrator.evaluate(
                candle=candle,
                swings=swings,
                trend=trend,
                liquidity_pools=pools,
                volume_sma_20=float(vol_sma),
                atr_14=float(atr_val),
                htf_bias=htf_bias,
                session=session,
            )

            if mss is not None:
                mss["forward_returns"] = self._calculate_forward_returns(
                    df, i, cfg.backtest.forward_return_periods
                )
                self.results.append(mss)

        logger.info(
            f"Backtest complete: {len(self.results)} MSS events detected "
            f"({sum(1 for r in self.results if r.get('status') == 'accepted')} accepted)"
        )
        return self.results

    def analyze(self) -> Dict[str, Any]:
        """Analyze backtest results for accuracy and quality correlation."""
        return analyze_backtest_results(self.results)

    def _calculate_forward_returns(
        self, df: pd.DataFrame, index: int, periods: List[int],
    ) -> Dict[str, Optional[float]]:
        """Calculate price change after MSS for validation."""
        returns: Dict[str, Optional[float]] = {}
        current_close = df["close"].iloc[index]
        for p in periods:
            if index + p < len(df):
                future_close = df["close"].iloc[index + p]
                pct = (future_close - current_close) / current_close * 100
                returns[f"{p}_bar"] = round(pct, 4)
            else:
                returns[f"{p}_bar"] = None
        return returns


def analyze_backtest_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze MSS detection accuracy and profitability.

    Computes directional accuracy by quality tier, session, and sweep presence.
    """
    if not results:
        return {"total_mss_detected": 0, "error": "No results to analyze"}

    df = pd.DataFrame(results)
    accepted = df[df["status"] == "accepted"]
    rejected = df[df["status"] == "rejected"]

    metrics: Dict[str, Any] = {
        "total_mss_detected": len(df),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "acceptance_rate": round(len(accepted) / len(df) * 100, 1) if len(df) > 0 else 0,
        "avg_quality": round(float(accepted["quality_score"].mean()), 1) if len(accepted) > 0 else 0,
    }

    # Directional accuracy for accepted MSS
    for direction in ["BULL_MSS", "BEAR_MSS"]:
        subset = accepted[accepted["direction"] == direction]
        for period_bars in [5, 20]:
            key_suffix = f"{direction.lower()}_{period_bars}bar"
            if len(subset) == 0:
                metrics[f"accuracy_{key_suffix}"] = None
                continue
            returns = subset["forward_returns"].apply(
                lambda x: x.get(f"{period_bars}_bar") if isinstance(x, dict) else None
            ).dropna()
            if len(returns) == 0:
                metrics[f"accuracy_{key_suffix}"] = None
                continue
            if direction == "BULL_MSS":
                accuracy = (returns > 0).mean() * 100
            else:
                accuracy = (returns < 0).mean() * 100
            metrics[f"accuracy_{key_suffix}"] = round(accuracy, 1)

    # Quality tier breakdown
    if len(accepted) > 0:
        high_q = accepted[accepted["quality_score"] >= 75]
        low_q = accepted[(accepted["quality_score"] >= 50) & (accepted["quality_score"] < 75)]
        metrics["high_quality_count"] = len(high_q)
        metrics["low_quality_count"] = len(low_q)

    # Session breakdown
    for session in ["NY", "LONDON", "ASIA", "OUTSIDE"]:
        sess_subset = accepted[accepted["session"] == session]
        metrics[f"session_{session.lower()}_count"] = len(sess_subset)

    # Sweep correlation
    has_sweep = accepted[accepted["prior_sweep"].notna()]
    no_sweep = accepted[accepted["prior_sweep"].isna()]
    metrics["with_sweep_count"] = len(has_sweep)
    metrics["without_sweep_count"] = len(no_sweep)

    return metrics
