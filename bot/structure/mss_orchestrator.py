"""Module 5: MSS Orchestrator — consumes all upstream modules to produce MSS events."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from bot.structure.config import MSSConfig, SessionWeights, StructureConfig
from bot.structure.sweep_detector import SweepEvent, detect_sweeps
from bot.structure.order_flow import score_order_flow
from bot.structure.swing_engine import Swing
from bot.structure.liquidity_map import LiquidityPool


class Displacement(TypedDict):
    is_valid: bool
    atr_multiple: float
    body_ratio: float
    score: float


class MSSResult(TypedDict, total=False):
    direction: str          # "BULL_MSS" or "BEAR_MSS"
    time: str
    session: str
    close: float
    broken_level: float
    displacement: Displacement
    flow_score: int
    prior_sweep: Optional[SweepEvent]
    htf_bias: str
    quality_score: int
    status: str             # "accepted" or "rejected"
    forward_returns: Dict[str, Optional[float]]


class MSSOrchestrator:
    """Orchestrates the full Liquidity -> Sweep -> Order Flow -> MSS pipeline."""

    def __init__(self, config: Optional[StructureConfig] = None) -> None:
        if config is None:
            config = StructureConfig()
        self.config = config
        self.mss_cfg = config.mss
        self.session_weights = config.session_weights
        self.recent_sweeps: List[SweepEvent] = []

    def evaluate(
        self,
        candle: Dict[str, Any],
        swings: List[Swing],
        trend: str,
        liquidity_pools: List[LiquidityPool],
        volume_sma_20: float,
        atr_14: float,
        htf_bias: str,
        session: str,
    ) -> Optional[MSSResult]:
        """Main evaluation: check if current candle creates an MSS.

        Consumes outputs from Modules 1-4 and produces a scored MSS event
        or None if no MSS occurred.
        """
        # Step 1: Check for sweeps (Module 3)
        sweep_events = detect_sweeps(
            candle, liquidity_pools, atr_14, self.config.sweep
        )
        for sweep in sweep_events:
            if sweep.get("sweep_type") == "liquidity_sweep":
                self.recent_sweeps.append(sweep)

        # Step 2: Check for structure break (requires Module 1 swings + trend)
        mss = self._check_structure_break(candle, swings, trend)
        if mss is None:
            return None

        # Step 3: Check displacement (body size relative to ATR)
        displacement = self._check_displacement(candle, atr_14)
        if not displacement["is_valid"]:
            return None  # No displacement = not an MSS

        # Step 4: Score order flow (Module 4)
        flow_score = score_order_flow(
            candle, volume_sma_20, atr_14, self.config.order_flow
        )

        # Step 5: Check if a sweep preceded this MSS
        prior_sweep = self._find_prior_sweep(mss["direction"])

        # Step 6: Calculate composite quality score
        quality = self._calculate_quality(
            displacement, flow_score, prior_sweep,
            htf_bias, mss["direction"], session,
        )

        # Step 7: Accept or reject
        status = "accepted" if quality >= self.mss_cfg.quality_threshold else "rejected"

        return {
            "direction": mss["direction"],
            "time": str(candle.get("time", "")),
            "session": session,
            "close": float(candle["close"]),
            "broken_level": mss["broken_level"],
            "displacement": displacement,
            "flow_score": flow_score,
            "prior_sweep": prior_sweep,
            "htf_bias": htf_bias,
            "quality_score": quality,
            "status": status,
        }

    def reset(self) -> None:
        """Clear sweep buffer (e.g. between backtest days)."""
        self.recent_sweeps.clear()

    # ── Private helpers ──────────────────────────────────────────────

    def _check_structure_break(
        self, candle: Dict[str, Any], swings: List[Swing], trend: str,
    ) -> Optional[Dict[str, Any]]:
        """Detect if candle breaks a swing level against the trend."""
        recent_lows = [s for s in swings if s["type"] == "low"]
        recent_highs = [s for s in swings if s["type"] == "high"]

        if trend == "UPTREND" and recent_lows:
            last_swing_low = recent_lows[-1]["price"]
            if candle["close"] < last_swing_low:  # Body close below
                return {"direction": "BEAR_MSS", "broken_level": last_swing_low}

        elif trend == "DOWNTREND" and recent_highs:
            last_swing_high = recent_highs[-1]["price"]
            if candle["close"] > last_swing_high:  # Body close above
                return {"direction": "BULL_MSS", "broken_level": last_swing_high}

        return None

    def _check_displacement(
        self, candle: Dict[str, Any], atr: float,
    ) -> Displacement:
        """Verify the break candle has displacement characteristics."""
        body = abs(candle["close"] - candle["open"])
        total_range = candle["high"] - candle["low"]
        body_ratio = body / total_range if total_range > 0 else 0.0
        atr_multiple = body / atr if atr > 0 else 0.0

        is_valid = (
            atr_multiple >= self.mss_cfg.min_displacement_atr
            and body_ratio >= self.mss_cfg.min_body_ratio
        )

        return {
            "is_valid": is_valid,
            "atr_multiple": round(atr_multiple, 2),
            "body_ratio": round(body_ratio, 2),
            "score": min(atr_multiple / 2.0, 1.0) * 100,
        }

    def _find_prior_sweep(self, mss_direction: str) -> Optional[SweepEvent]:
        """Check if a liquidity sweep preceded this MSS in the expected direction."""
        expected = "bullish_sweep" if mss_direction == "BULL_MSS" else "bearish_sweep"
        lookback = self.mss_cfg.sweep_lookback_bars
        for sweep in reversed(self.recent_sweeps[-lookback:]):
            if sweep.get("direction") == expected:
                return sweep
        return None

    def _calculate_quality(
        self,
        displacement: Displacement,
        flow_score: int,
        prior_sweep: Optional[SweepEvent],
        htf_bias: str,
        direction: str,
        session: str,
    ) -> int:
        """Weighted quality formula combining all signal components."""
        w = self.mss_cfg

        # Displacement strength (30%)
        disp_score = displacement["score"]

        # Order flow conviction (25%)
        of_score = float(flow_score)

        # Prior liquidity sweep (20%)
        sweep_score = float(prior_sweep.get("sweep_quality", 0)) if prior_sweep else 0.0

        # HTF alignment (15%)
        aligned = (
            (htf_bias == "UPTREND" and direction == "BULL_MSS")
            or (htf_bias == "DOWNTREND" and direction == "BEAR_MSS")
        )
        htf_score = 100.0 if aligned else 0.0

        # Session weight (10%)
        session_score = self.session_weights.get(session) * 100

        quality = (
            disp_score * w.weight_displacement
            + of_score * w.weight_order_flow
            + sweep_score * w.weight_prior_sweep
            + htf_score * w.weight_htf_alignment
            + session_score * w.weight_session
        )

        return round(quality)
