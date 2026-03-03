import useSWR from "swr";
import { useNewsCalendar } from "./use-news-calendar";
import type { EventReaction } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

/**
 * Hook that:
 * 1. Polls the capture endpoint every 60s with current RED events
 * 2. Fetches recent event reactions for display
 */
export function useEventReactions() {
  const { events } = useNewsCalendar();

  // Filter to RED events that are imminent or recently released (within 2h)
  const relevantEvents = events.filter((e) => {
    if (e.impact !== "RED") return false;
    if (e.status === "imminent") return true;
    if (e.status === "released") {
      const releasedAt = new Date(e.scheduledAt).getTime();
      return Date.now() - releasedAt < 2 * 60 * 60 * 1000;
    }
    if (e.status === "upcoming") {
      const scheduledAt = new Date(e.scheduledAt).getTime();
      return scheduledAt - Date.now() < 15 * 60 * 1000;
    }
    return false;
  });

  // Trigger capture for relevant events
  const capturePayload = relevantEvents.length > 0
    ? encodeURIComponent(JSON.stringify(relevantEvents.map((e) => ({
        id: e.id,
        name: e.name,
        scheduledAt: e.scheduledAt,
        status: e.status,
        impact: e.impact,
      }))))
    : null;

  useSWR(
    capturePayload ? `/api/news/reactions?action=capture&events=${capturePayload}` : null,
    fetcher,
    { refreshInterval: 60_000 },
  );

  // Fetch all recent reactions
  const { data, error, isLoading } = useSWR<EventReaction[]>(
    "/api/news/reactions",
    fetcher,
    { refreshInterval: 60_000 },
  );

  return {
    reactions: Array.isArray(data) ? data : [],
    error,
    isLoading,
  };
}
