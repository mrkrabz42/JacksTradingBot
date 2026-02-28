import useSWR from "swr";
import type { Position } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function usePositions() {
  const { data, error, isLoading } = useSWR<Position[]>(
    "/api/positions",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.POSITIONS }
  );
  return { positions: Array.isArray(data) ? data : [], error, isLoading };
}
