import useSWR from "swr";
import { REFRESH_INTERVALS } from "@/lib/constants";

export interface MSSEvent {
  id: string;
  timestamp: string;
  direction: "BULL" | "BEAR";
  price: number;
  control_point_price: number;
  displacement_quality: number;
  is_accepted: boolean;
  rejection_reason: string | null;
  session: string;
  distance_to_pdh: number | null;
  distance_to_pdl: number | null;
  regime: string | null;
  volatility_state: string | null;
  trend_strength_score: number | null;
  trend_direction: string | null;
  volume_state: string | null;
  vwap: number | null;
  poc: number | null;
  vah: number | null;
  val: number | null;
  liquidity_draw_direction: string | null;
  liquidity_magnet_score: number | null;
  htf_bias: string | null;
  mtf_structure_bias: string | null;
  ltf_direction: string | null;
  mtf_alignment_state: string | null;
  mtf_alignment_score: number | null;
  breakout_quality_score: number | null;
  breakout_type: string | null;
  break_strength_score: number | null;
  retest_quality_score: number | null;
  volume_confirmation_score: number | null;
  environment_alignment_score: number | null;
  has_clean_retest: boolean | null;
  closed_beyond_level: boolean | null;
  confluence_score: number | null;
  setup_grade: string | null;
  event_trade_bias: string | null;
  confluence_components: {
    trend: number; regime: number; volatility: number; volume: number;
    liquidity: number; mtf: number; mss: number; breakout: number;
  } | null;
  rvol_ratio: number | null;
  participation_state: string | null;  // 'LOW_ACTIVITY' | 'NORMAL' | 'ELEVATED' | 'EXTREME'
  volume_spike_flag: boolean | null;
  session_high: number | null;
  session_low: number | null;
  dist_session_high: number | null;
  dist_session_low: number | null;
  context_flags: string[];
  environment_summary: string;
}

export interface MSSData {
  symbol: string;
  date: string;
  total_candles: number;
  atr: number;
  control_points: number;
  total_mss: number;
  accepted: number;
  rejected: number;
  avg_displacement_quality: number;
  pdh: number | null;
  pdl: number | null;
  current_regime: string;
  regime_distribution: { TREND: number; RANGE: number; TRANSITION: number };
  current_volatility_state: string;
  volatility_distribution: { LOW: number; MEDIUM: number; HIGH: number };
  current_trend_direction: string;
  current_trend_score: number;
  trend_direction_distribution: { UP: number; DOWN: number; NEUTRAL: number };
  current_volume_state: string;
  current_vwap: number | null;
  current_poc: number | null;
  current_vah: number | null;
  current_val: number | null;
  volume_state_distribution: {
    IN_VALUE: number;
    ACCEPTING_ABOVE: number;
    ACCEPTING_BELOW: number;
    REJECTING_ABOVE: number;
    REJECTING_BELOW: number;
  };
  current_liquidity_draw_direction: string;
  current_liquidity_magnet_score: number;
  liquidity_draw_distribution: {
    ABOVE: number;
    BELOW: number;
    NEUTRAL: number;
  };
  current_htf_bias: string;
  current_mtf_structure_bias: string;
  current_mtf_alignment_state: string;
  current_mtf_alignment_score: number;
  mtf_alignment_distribution: {
    FULL_ALIGN_UP: number;
    FULL_ALIGN_DOWN: number;
    PARTIAL_ALIGN_UP: number;
    PARTIAL_ALIGN_DOWN: number;
    CONFLICT: number;
    WEAK_ALIGN: number;
  };
  current_confluence_score: number;
  current_setup_grade: string;
  current_trade_bias: string;
  current_confluence_components: {
    trend: number; regime: number; volatility: number; volume: number;
    liquidity: number; mtf: number; mss: number; breakout: number;
  } | null;
  confluence_distribution: {
    NO_TRADE: number; MEDIUM_SETUP: number; HIGH_SETUP: number; A_PLUS_SETUP: number;
  };
  current_participation_state: string;
  current_rvol_ratio: number;
  current_volume_spike: boolean;
  participation_state_distribution: {
    LOW_ACTIVITY: number; NORMAL: number; ELEVATED: number; EXTREME: number;
  };
  current_session_high: number | null;
  current_session_low: number | null;
  current_environment_summary: string;
  events: MSSEvent[];
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useMSS() {
  const { data, error, isLoading } = useSWR<MSSData>(
    "/api/bot/mss",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.BOT_STATUS }
  );
  return { mss: data ?? null, error, isLoading };
}
