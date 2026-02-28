import useSWR from "swr";
import type { BotStatus } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useBotStatus() {
  const { data, error, isLoading } = useSWR<BotStatus>(
    "/api/bot/status",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.BOT_STATUS }
  );
  return { status: data ?? null, error, isLoading };
}
