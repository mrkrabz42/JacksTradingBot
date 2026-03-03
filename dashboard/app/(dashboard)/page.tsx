"use client";

import { useMemo } from "react";
import { PathwayCard, PathwaySkeleton } from "@/components/cards/pathway-card";
import { useAllPathways } from "@/lib/hooks/use-pathway";
import { useAllFundamentals } from "@/lib/hooks/use-fundamentals";
import { useNewsCalendar } from "@/lib/hooks/use-news-calendar";
import { INSTRUMENTS } from "@/lib/constants";

export default function DashboardPage() {
  const { pathways, isLoading } = useAllPathways();
  const { fundamentals } = useAllFundamentals();
  const { events } = useNewsCalendar();

  // Detect RED events that are imminent or released within 30min
  const volatilityWarning = useMemo(() => {
    const now = Date.now();
    return events.some((e) => {
      if (e.impact !== "RED") return false;
      if (e.status === "imminent") return true;
      if (e.status === "released") {
        const releasedAt = new Date(e.scheduledAt).getTime();
        return now - releasedAt < 30 * 60 * 1000; // within 30 min
      }
      // upcoming RED within 15 min
      if (e.status === "upcoming") {
        const scheduledAt = new Date(e.scheduledAt).getTime();
        return scheduledAt - now < 15 * 60 * 1000 && scheduledAt - now > 0;
      }
      return false;
    });
  }, [events]);

  return (
    <div className="space-y-6">
      {volatilityWarning && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-3 flex items-center gap-3 animate-pulse">
          <span className="w-3 h-3 rounded-full bg-red-500 flex-shrink-0" />
          <p className="text-sm font-semibold text-red-400">
            High-impact event active — expect elevated volatility. Fundamentals confidence dampened.
          </p>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {isLoading || pathways.length === 0
          ? INSTRUMENTS.map((inst) => <PathwaySkeleton key={inst.symbol} />)
          : pathways.map((pw) => (
              <PathwayCard
                key={pw.symbol}
                data={pw}
                fundamentals={fundamentals.find((f) => f.symbol === pw.symbol)}
                volatilityWarning={volatilityWarning}
              />
            ))
        }
      </div>
    </div>
  );
}
