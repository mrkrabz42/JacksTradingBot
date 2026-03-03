import useSWR from "swr";
import { REFRESH_INTERVALS } from "@/lib/constants";
import type { CalendarEvent } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useNewsCalendar() {
  const { data, error, isLoading } = useSWR<CalendarEvent[]>(
    "/api/news/calendar",
    fetcher,
    { refreshInterval: REFRESH_INTERVALS.NEWS_CALENDAR },
  );

  const events = Array.isArray(data) ? data : [];
  const upcoming = events.filter((e) => e.status === "upcoming" || e.status === "imminent");
  const released = events.filter((e) => e.status === "released");

  return { events, upcoming, released, error, isLoading };
}
