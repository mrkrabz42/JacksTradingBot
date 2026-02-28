import useSWR from "swr";
import type { PortfolioHistory } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function usePortfolioHistory() {
  const { data, error, isLoading } = useSWR<PortfolioHistory>(
    "/api/portfolio-history",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.PORTFOLIO_HISTORY }
  );
  return { history: data, error, isLoading };
}
