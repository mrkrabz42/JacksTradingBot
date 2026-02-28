import useSWR from "swr";
import type { Trade } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useTrades() {
  const { data, error, isLoading } = useSWR<Trade[]>(
    "/api/trades",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.TRADES }
  );
  return { trades: Array.isArray(data) ? data : [], error, isLoading };
}
