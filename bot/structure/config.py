"""Configuration for the Order Flow & Liquidity framework."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SwingConfig:
    lookback_n: int = 2
    min_swings_for_trend: int = 4


@dataclass
class LiquidityConfig:
    equal_level_tolerance_pct: float = 0.003
    round_number_intervals: list[int] = field(default_factory=lambda: [5, 10, 50, 100])
    max_pool_age_bars: int = 500


@dataclass
class SweepConfig:
    proximity_atr: float = 0.5
    max_penetration_atr: float = 1.0
    min_quality: int = 50


@dataclass
class OrderFlowConfig:
    vol_sma_period: int = 20
    volume_spike_threshold: float = 2.0
    min_body_ratio_for_conviction: float = 0.6


@dataclass
class MSSConfig:
    min_displacement_atr: float = 1.5
    min_body_ratio: float = 0.65
    quality_threshold: int = 65
    sweep_lookback_bars: int = 10
    weight_displacement: float = 0.30
    weight_order_flow: float = 0.25
    weight_prior_sweep: float = 0.20
    weight_htf_alignment: float = 0.15
    weight_session: float = 0.10


@dataclass
class SessionWeights:
    NY: float = 1.0
    LONDON: float = 0.95
    ASIA: float = 0.70
    OUTSIDE: float = 0.60

    def get(self, session: str) -> float:
        return getattr(self, session, 0.50)


@dataclass
class RegimeConfig:
    adx_period: int = 14
    bb_period: int = 20
    bb_std_dev: float = 2.0
    adx_trend_threshold: float = 25.0
    adx_strong_trend_threshold: float = 35.0
    bb_width_range_threshold: float = 0.01
    bb_width_trend_threshold: float = 0.03
    vwap_range_band_pct: float = 0.003
    vwap_trend_band_pct: float = 0.01
    lookback_bars: int = 20


@dataclass
class VolatilityConfig:
    atr_period: int = 14
    baseline_lookback: int = 100
    low_vol_pct: float = 0.7
    high_vol_pct: float = 1.3
    min_bars_for_baseline: int = 150


@dataclass
class BacktestConfig:
    atr_period: int = 14
    forward_return_periods: list[int] = field(default_factory=lambda: [5, 10, 20, 50])
    walk_forward_train_months: int = 4
    walk_forward_test_months: int = 2


@dataclass
class TrendConfig:
    fast_ema_period: int = 20
    slow_ema_period: int = 50
    adx_period: int = 14
    regression_lookback: int = 50
    min_slope_strength: float = 0.0
    strong_slope_threshold: float = 0.0005
    adx_cap: float = 50.0
    weight_adx: float = 0.4
    weight_ema_slope: float = 0.3
    weight_reg_slope: float = 0.3
    min_bars: int = 60


@dataclass
class VolumeConfig:
    profile_mode: str = "session"          # "session" or "rolling"
    profile_window_bars: int = 200         # used if profile_mode = "rolling"
    num_profile_bins: int = 40
    value_area_fraction: float = 0.70
    acceptance_min_bars: int = 3
    rejection_max_bars: int = 2
    vwap_near_band_pct: float = 0.003


@dataclass
class MTFAlignmentScores:
    """Base alignment scores (0–100) for each pattern."""
    full_align: float = 90.0
    partial_align: float = 60.0
    weak_align: float = 40.0
    conflict: float = 10.0


@dataclass
class MTFConfig:
    htf_timeframe: str = "1H"
    mtf_timeframe: str = "15M"
    ltf_timeframe: str = "5M"
    htf_trend_min_strength: float = 50.0
    mtf_trend_min_strength: float = 40.0
    ltf_trend_min_strength: float = 30.0
    alignment_scores: MTFAlignmentScores = field(default_factory=MTFAlignmentScores)


@dataclass
class LiquidityDrawWeights:
    """Category weights for liquidity draw scoring. Must sum to 1.0."""
    session_high_low: float = 0.25
    pdh_pdl: float = 0.25
    equal_high_low: float = 0.25
    volume_magnets: float = 0.25


@dataclass
class LiquidityDrawConfig:
    equal_level_tolerance_pct: float = 0.003
    max_equal_level_age_bars: int = 500
    dist_metric: str = "atr"               # "atr" or "percent"
    dist_clip_atr: float = 3.0             # distances beyond this are ignored
    session_high_low_lookback: int = 1     # days for session reference
    neutral_band_ratio: float = 0.20       # up/down within 20% → NEUTRAL
    min_magnet_score_for_signal: float = 20.0
    weights: LiquidityDrawWeights = field(default_factory=LiquidityDrawWeights)


@dataclass
class ConfluenceWeights:
    """Weights for confluence sub-scores. Must sum to 1.0."""
    trend_strength: float = 0.20
    regime: float = 0.10
    volatility: float = 0.10
    volume: float = 0.10
    liquidity: float = 0.15
    mtf_alignment: float = 0.15
    mss_quality: float = 0.10
    breakout_quality: float = 0.10


@dataclass
class ConfluenceThresholds:
    no_trade: float = 40.0
    medium: float = 60.0
    high: float = 75.0
    a_plus: float = 85.0


@dataclass
class ConfluenceBiasConfig:
    min_bias_score: float = 55.0
    draw_alignment_bonus: float = 10.0
    trend_alignment_bonus: float = 10.0


@dataclass
class ConfluenceConfig:
    component_weights: ConfluenceWeights = field(default_factory=ConfluenceWeights)
    setup_thresholds: ConfluenceThresholds = field(default_factory=ConfluenceThresholds)
    bias: ConfluenceBiasConfig = field(default_factory=ConfluenceBiasConfig)


@dataclass
class BreakoutWeights:
    """Weights for breakout sub-scores. Must sum to 1.0."""
    break_strength: float = 0.40
    retest_quality: float = 0.30
    volume_confirmation: float = 0.20
    environment_alignment: float = 0.10


@dataclass
class BreakoutConfig:
    lookahead_bars_for_retest: int = 10
    min_close_beyond_atr: float = 0.25
    strong_close_beyond_atr: float = 0.75
    min_volume_relative: float = 1.2
    strong_volume_relative: float = 2.0
    max_retest_tolerance_atr: float = 0.5
    continuation_threshold: float = 65.0
    fakeout_threshold: float = 35.0
    weights: BreakoutWeights = field(default_factory=BreakoutWeights)


@dataclass
class ParticipationConfig:
    lookback_days: int = 20
    min_bars_per_bucket: int = 10
    bucket_size_minutes: int = 5
    low_threshold: float = 0.7
    high_threshold: float = 1.5
    extreme_threshold: float = 3.0
    spike_threshold: float = 3.0


@dataclass
class ContextFormatterConfig:
    """Thresholds and limits for the context flag / summary text layer."""
    # Trend
    trend_weak_max: float = 40.0
    trend_moderate_max: float = 70.0
    # Liquidity magnet
    liq_weak_max: float = 40.0
    liq_strong_min: float = 70.0
    # MTF alignment score
    mtf_weak_max: float = 40.0
    mtf_strong_min: float = 70.0
    # Breakout quality
    bkt_weak_max: float = 40.0
    bkt_strong_min: float = 70.0
    # Confluence
    conf_weak_max: float = 40.0
    conf_strong_min: float = 70.0
    # RVOL
    rvol_low_max: float = 0.8
    rvol_high_min: float = 1.2
    rvol_extreme_min: float = 2.0
    # Session proximity (ATR units — "NEAR SESSION HIGH/LOW" threshold)
    session_near_atr: float = 0.5
    # Bias strength threshold (count of supporting factors to qualify as STRONG)
    strong_bias_threshold: int = 3
    # Output limits
    max_flags: int = 8
    summary_max_chars: int = 220


@dataclass
class StructureConfig:
    swing: SwingConfig = field(default_factory=SwingConfig)
    liquidity: LiquidityConfig = field(default_factory=LiquidityConfig)
    sweep: SweepConfig = field(default_factory=SweepConfig)
    order_flow: OrderFlowConfig = field(default_factory=OrderFlowConfig)
    mss: MSSConfig = field(default_factory=MSSConfig)
    session_weights: SessionWeights = field(default_factory=SessionWeights)
    regime: RegimeConfig = field(default_factory=RegimeConfig)
    volatility: VolatilityConfig = field(default_factory=VolatilityConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    trend: TrendConfig = field(default_factory=TrendConfig)
    volume: VolumeConfig = field(default_factory=VolumeConfig)
    liquidity_draw: LiquidityDrawConfig = field(default_factory=LiquidityDrawConfig)
    mtf: MTFConfig = field(default_factory=MTFConfig)
    breakout: BreakoutConfig = field(default_factory=BreakoutConfig)
    confluence: ConfluenceConfig = field(default_factory=ConfluenceConfig)
    participation: ParticipationConfig = field(default_factory=ParticipationConfig)
    context_formatter: ContextFormatterConfig = field(default_factory=ContextFormatterConfig)
