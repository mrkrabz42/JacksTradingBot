import useSWR from "swr";
import type { Order } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useOrders() {
  const { data, error, isLoading } = useSWR<Order[]>(
    "/api/orders",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.ORDERS }
  );
  return { orders: Array.isArray(data) ? data : [], error, isLoading };
}
