"use client";

import { useNewsCalendar } from "@/lib/hooks/use-news-calendar";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/types";

function formatRelativeTime(isoDate: string): string {
  const target = new Date(isoDate).getTime();
  const now = Date.now();
  const diffMs = target - now;
  const absDiff = Math.abs(diffMs);

  const minutes = Math.round(absDiff / 60_000);
  const hours = Math.floor(absDiff / 3_600_000);
  const remainingMin = minutes - hours * 60;

  if (diffMs > 0) {
    // Future
    if (hours > 0) return `in ${hours}h ${remainingMin}m`;
    return `in ${minutes}m`;
  } else {
    // Past
    if (hours > 0) return `${hours}h ${remainingMin}m ago`;
    return `${minutes}m ago`;
  }
}

function ImpactDot({ impact, imminent }: { impact: CalendarEvent["impact"]; imminent: boolean }) {
  return (
    <span
      className={cn(
        "inline-block w-2 h-2 rounded-full flex-shrink-0",
        impact === "RED" ? "bg-red-500" : "bg-amber-500",
        imminent && "animate-pulse",
      )}
    />
  );
}

function CountryFlag({ country }: { country: "US" | "UK" }) {
  return (
    <span className="text-[10px]">
      {country === "US" ? "\uD83C\uDDFA\uD83C\uDDF8" : "\uD83C\uDDEC\uD83C\uDDE7"}
    </span>
  );
}

function EventRow({ event }: { event: CalendarEvent }) {
  const isImminent = event.status === "imminent";

  return (
    <div
      className={cn(
        "flex items-start gap-2 py-1.5 px-2 rounded-md",
        isImminent && "bg-red-500/5 border border-red-500/20",
      )}
    >
      <div className="mt-1">
        <ImpactDot impact={event.impact} imminent={isImminent} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <CountryFlag country={event.country} />
          <span className={cn(
            "text-[11px] truncate",
            isImminent ? "font-bold text-foreground" : "text-zinc-600",
          )}>
            {event.name}
          </span>
        </div>
        {event.actual && (
          <div className="flex gap-2 mt-0.5">
            <span className="text-[9px] text-muted-foreground">
              Act: <span className="text-foreground font-medium">{event.actual}</span>
            </span>
            {event.previous && (
              <span className="text-[9px] text-muted-foreground">
                Prev: {event.previous}
              </span>
            )}
          </div>
        )}
      </div>
      <span className={cn(
        "text-[10px] font-mono flex-shrink-0",
        isImminent ? "text-red-400 font-bold" : "text-muted-foreground",
      )}>
        {formatRelativeTime(event.scheduledAt)}
      </span>
    </div>
  );
}

export function NewsBoard() {
  const { upcoming, released, isLoading } = useNewsCalendar();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-8 bg-border/30 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  const hasEvents = upcoming.length > 0 || released.length > 0;

  if (!hasEvents) {
    return (
      <p className="text-[11px] text-muted-foreground/50 text-center py-2">
        No events in the next 48 hours
      </p>
    );
  }

  return (
    <div className="space-y-3 max-h-[400px] overflow-y-auto">
      {upcoming.length > 0 && (
        <div>
          <p className="text-[9px] text-muted-foreground/60 font-semibold uppercase tracking-wider mb-1">
            Upcoming
          </p>
          <div className="space-y-0.5">
            {upcoming.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
          </div>
        </div>
      )}

      {released.length > 0 && (
        <div>
          <p className="text-[9px] text-muted-foreground/60 font-semibold uppercase tracking-wider mb-1">
            Released
          </p>
          <div className="space-y-0.5">
            {released.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
