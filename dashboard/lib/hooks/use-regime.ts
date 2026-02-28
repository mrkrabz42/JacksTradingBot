import useSWR from "swr";
import { REFRESH_INTERVALS } from "@/lib/constants";

export interface RegimeData {
  symbol: string;
  date: string;
  current_regime: string;
  adx: number;
  bb_width: number;
  vwap_distance: number;
  regime_distribution: { TREND: number; RANGE: number; TRANSITION: number };
  total_bars: number;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useRegime() {
  const { data, error, isLoading } = useSWR<RegimeData>(
    "/api/bot/regime",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.BOT_STATUS }
  );
  return { regime: data ?? null, error, isLoading };
}
