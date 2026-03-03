"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useNewsCalendar } from "./use-news-calendar";

/**
 * Watches for events entering the "imminent" window (15 min before).
 * Fires toast.warning() with event name, time, and impact level.
 * Tracks seen IDs to avoid duplicate toasts.
 */
export function useNewsAlerts() {
  const { events } = useNewsCalendar();
  const seenIds = useRef<Set<string>>(new Set());
  const isFirstLoad = useRef(true);

  useEffect(() => {
    if (!events || events.length === 0) return;

    if (isFirstLoad.current) {
      // Seed seen IDs silently on first load — no toasts for already-imminent events
      isFirstLoad.current = false;
      for (const event of events) {
        if (event.status === "imminent" || event.status === "released") {
          seenIds.current.add(event.id);
        }
      }
      return;
    }

    // Find newly imminent events
    for (const event of events) {
      if (event.status !== "imminent") continue;
      if (seenIds.current.has(event.id)) continue;

      seenIds.current.add(event.id);

      const scheduledAt = new Date(event.scheduledAt);
      const msUntil = scheduledAt.getTime() - Date.now();
      const minUntil = Math.max(0, Math.round(msUntil / 60_000));

      const flag = event.country === "US" ? "\uD83C\uDDFA\uD83C\uDDF8" : "\uD83C\uDDEC\uD83C\uDDE7";
      const title = `${flag} ${event.name}`;
      const desc = `${event.impact === "RED" ? "HIGH" : "MEDIUM"} impact — in ${minUntil} min`;

      if (event.impact === "RED") {
        toast.error(title, { description: desc, duration: 10_000 });
      } else {
        toast.warning(title, { description: desc, duration: 8_000 });
      }
    }
  }, [events]);
}

/** Mount in layout to activate toasts on any page */
export function NewsAlertProvider() {
  useNewsAlerts();
  return null;
}
