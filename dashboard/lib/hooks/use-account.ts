import useSWR from "swr";
import type { AccountData } from "@/lib/types";
import { REFRESH_INTERVALS } from "@/lib/constants";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useAccount() {
  const { data, error, isLoading } = useSWR<AccountData>(
    "/api/account",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.ACCOUNT }
  );
  return { account: data, error, isLoading };
}
