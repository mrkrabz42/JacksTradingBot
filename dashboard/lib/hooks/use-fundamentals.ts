import useSWR from "swr";
import { REFRESH_INTERVALS } from "@/lib/constants";
import type { FundamentalsData } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useFundamentals(symbol?: string) {
  const url = symbol
    ? `/api/fundamentals?symbol=${symbol}`
    : "/api/fundamentals";

  const { data, error, isLoading } = useSWR<FundamentalsData | FundamentalsData[]>(
    url,
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.FUNDAMENTALS },
  );

  if (symbol) {
    return { fundamentals: (data as FundamentalsData) ?? null, error, isLoading };
  }

  return { fundamentals: data ?? null, error, isLoading };
}

export function useAllFundamentals() {
  const { data, error, isLoading } = useSWR<FundamentalsData[]>(
    "/api/fundamentals",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.FUNDAMENTALS },
  );
  return { fundamentals: Array.isArray(data) ? data : [], error, isLoading };
}
