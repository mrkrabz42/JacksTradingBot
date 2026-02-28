import useSWR from "swr";
import { REFRESH_INTERVALS } from "@/lib/constants";

export type VolumeState =
  | "IN_VALUE"
  | "ACCEPTING_ABOVE"
  | "ACCEPTING_BELOW"
  | "REJECTING_ABOVE"
  | "REJECTING_BELOW";

export interface VolumeData {
  symbol: string;
  date: string;
  total_bars: number;
  current_vwap: number | null;
  current_poc: number | null;
  current_vah: number | null;
  current_val: number | null;
  current_volume_state: VolumeState;
  volume_state_distribution: {
    IN_VALUE: number;
    ACCEPTING_ABOVE: number;
    ACCEPTING_BELOW: number;
    REJECTING_ABOVE: number;
    REJECTING_BELOW: number;
  };
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useVolume() {
  const { data, error, isLoading } = useSWR<VolumeData>(
    "/api/bot/volume",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.BOT_STATUS }
  );
  return { volume: data ?? null, error, isLoading };
}
