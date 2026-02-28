import useSWR, { mutate } from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export interface UserFeedback {
  id: number;
  trade_id: string;
  user_name: string;
  comment: string | null;
  sentiment: "good" | "bad" | "questionable" | null;
  tags: string | null; // JSON string
  created_at: string;
}

export function useUserFeedback(tradeId: string | null) {
  const { data, error, isLoading } = useSWR<UserFeedback[]>(
    tradeId ? `/api/user-feedback?trade_id=${tradeId}` : null,
    fetcher
  );
  return { feedback: Array.isArray(data) ? data : [], error, isLoading };
}

export function useAllFeedback() {
  const { data, error, isLoading } = useSWR<UserFeedback[]>(
    "/api/user-feedback",
    fetcher
  );
  return { feedback: Array.isArray(data) ? data : [], error, isLoading };
}

export async function submitFeedback(
  tradeId: string,
  comment: string,
  sentiment: string,
  tags?: string[]
) {
  await fetch("/api/user-feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trade_id: tradeId,
      comment,
      sentiment,
      tags: tags && tags.length > 0 ? tags : undefined,
    }),
  });
  mutate(`/api/user-feedback?trade_id=${tradeId}`);
  mutate("/api/user-feedback");
}
