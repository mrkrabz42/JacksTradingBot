"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { toast } from "sonner";
import { useMSS, type MSSEvent } from "./use-mss";

export interface MSSAlert extends MSSEvent {
  alertedAt: string;
}

export function useMSSAlerts() {
  const { mss, error, isLoading } = useMSS();
  const seenIds = useRef<Set<string>>(new Set());
  const isFirstLoad = useRef(true);
  const [alerts, setAlerts] = useState<MSSAlert[]>([]);

  useEffect(() => {
    if (!mss?.events) return;

    const now = new Date().toISOString();

    if (isFirstLoad.current) {
      // Seed seen IDs and populate history silently (no toasts)
      isFirstLoad.current = false;
      for (const event of mss.events) {
        seenIds.current.add(event.id);
      }
      setAlerts(
        mss.events
          .map((e) => ({ ...e, alertedAt: now }))
          .reverse()
      );
      return;
    }

    // Diff: find new events
    const newEvents: MSSEvent[] = [];
    for (const event of mss.events) {
      if (!seenIds.current.has(event.id)) {
        seenIds.current.add(event.id);
        newEvents.push(event);
      }
    }

    if (newEvents.length === 0) return;

    // Fire toasts and prepend to alert history
    const newAlerts: MSSAlert[] = [];
    for (const event of newEvents) {
      const qualPct = Math.round(event.displacement_quality * 100);
      const title = `${event.direction} MSS — $${event.price.toFixed(2)} (${event.session}, ${qualPct}%)`;
      const desc = event.is_accepted
        ? `Broke ${event.direction === "BULL" ? "above" : "below"} CP $${event.control_point_price.toFixed(2)} — Accepted`
        : `Broke ${event.direction === "BULL" ? "above" : "below"} CP $${event.control_point_price.toFixed(2)} — Rejected`;

      if (event.is_accepted) {
        toast.success(title, { description: desc });
      } else {
        toast.warning(title, { description: desc });
      }

      newAlerts.push({ ...event, alertedAt: now });
    }

    setAlerts((prev) => [...newAlerts.reverse(), ...prev]);
  }, [mss?.events]);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  return { alerts, mss, isLoading, error, clearAlerts };
}

/** Mount in layout to activate toasts on any page */
export function MSSAlertProvider() {
  useMSSAlerts();
  return null;
}
