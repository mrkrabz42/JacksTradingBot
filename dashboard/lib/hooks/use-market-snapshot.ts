import useSWR from "swr";
import type { MarketSnapshot } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useMarketSnapshot() {
  const { data, error, isLoading } = useSWR<MarketSnapshot>(
    "/api/market-snapshot",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.MARKET_SNAPSHOT }
  );
  return { snapshot: data, error, isLoading };
}
