"use client";

import { useNewsCalendar } from "@/lib/hooks/use-news-calendar";
import { useAllFundamentals } from "@/lib/hooks/use-fundamentals";
import { useEventReactions } from "@/lib/hooks/use-event-reactions";
import { cn } from "@/lib/utils";
import type { CalendarEvent, FundamentalsData, EventReaction } from "@/lib/types";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

// ── Calendar event row ──────────────────────────────────────────────────────

function formatRelativeTime(isoDate: string): string {
  const target = new Date(isoDate).getTime();
  const now = Date.now();
  const diffMs = target - now;
  const absDiff = Math.abs(diffMs);
  const minutes = Math.round(absDiff / 60_000);
  const hours = Math.floor(absDiff / 3_600_000);
  const remainingMin = minutes - hours * 60;

  if (diffMs > 0) {
    if (hours > 0) return `in ${hours}h ${remainingMin}m`;
    return `in ${minutes}m`;
  } else {
    if (hours > 0) return `${hours}h ${remainingMin}m ago`;
    return `${minutes}m ago`;
  }
}

function formatScheduledTime(isoDate: string): string {
  return new Date(isoDate).toLocaleString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function EventCard({ event }: { event: CalendarEvent }) {
  const isImminent = event.status === "imminent";
  const isReleased = event.status === "released";

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 rounded-xl border transition-colors",
        isImminent
          ? "bg-red-500/5 border-red-500/30 animate-pulse"
          : isReleased
            ? "bg-card/50 border-border/50 opacity-70"
            : "bg-card border-border hover:border-blue-500/30",
      )}
    >
      {/* Impact indicator */}
      <div className="flex flex-col items-center gap-1">
        <span
          className={cn(
            "w-3 h-3 rounded-full",
            event.impact === "RED" ? "bg-red-500" : "bg-amber-500",
          )}
        />
        <span className="text-[9px] text-muted-foreground font-medium">
          {event.impact}
        </span>
      </div>

      {/* Country + Name */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm">
            {event.country === "US" ? "\uD83C\uDDFA\uD83C\uDDF8" : "\uD83C\uDDEC\uD83C\uDDE7"}
          </span>
          <span
            className={cn(
              "text-sm font-semibold truncate",
              isImminent ? "text-foreground" : "text-zinc-700",
            )}
          >
            {event.name}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatScheduledTime(event.scheduledAt)}
        </p>
      </div>

      {/* Forecast / Previous / Actual */}
      <div className="flex gap-4 text-xs flex-shrink-0">
        {event.forecast && (
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground/60 uppercase">Fcst</p>
            <p className="text-zinc-600 font-mono">{event.forecast}</p>
          </div>
        )}
        {event.previous && (
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground/60 uppercase">Prev</p>
            <p className="text-zinc-600 font-mono">{event.previous}</p>
          </div>
        )}
        {event.actual && (
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground/60 uppercase">Act</p>
            <p className="text-foreground font-bold font-mono">{event.actual}</p>
          </div>
        )}
      </div>

      {/* Relative time */}
      <span
        className={cn(
          "text-xs font-mono flex-shrink-0 w-20 text-right",
          isImminent ? "text-red-400 font-bold" : "text-muted-foreground",
        )}
      >
        {formatRelativeTime(event.scheduledAt)}
      </span>

      {/* Status badge */}
      <span
        className={cn(
          "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase flex-shrink-0",
          isImminent && "bg-red-500/15 text-red-400",
          event.status === "upcoming" && "bg-blue-500/10 text-blue-400",
          isReleased && "bg-zinc-500/10 text-zinc-500",
        )}
      >
        {event.status}
      </span>
    </div>
  );
}

// ── Fundamentals summary card ───────────────────────────────────────────────

function DirectionIcon({ direction }: { direction: 1 | 0 | -1 }) {
  if (direction === 1) return <ArrowUpRight className="h-3.5 w-3.5 text-emerald-400" />;
  if (direction === -1) return <ArrowDownRight className="h-3.5 w-3.5 text-red-400" />;
  return <Minus className="h-3.5 w-3.5 text-zinc-500" />;
}

function FundamentalsCard({ data }: { data: FundamentalsData }) {
  const biasColor = {
    "Strong Bullish": "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    "Moderate Bullish": "text-emerald-400/80 bg-emerald-500/8 border-emerald-500/20",
    "Neutral": "text-zinc-400 bg-zinc-500/10 border-zinc-500/20",
    "Moderate Bearish": "text-red-400/80 bg-red-500/8 border-red-500/20",
    "Strong Bearish": "text-red-400 bg-red-500/10 border-red-500/30",
  }[data.netBias];

  return (
    <div className="bg-card border border-border rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-foreground">{data.symbol.replace("_", "/")}</span>
        <span className={cn("px-2.5 py-0.5 rounded-full text-[11px] font-bold border", biasColor)}>
          {data.netBias}
        </span>
      </div>

      {/* Strength bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              data.strength >= 65 ? "bg-emerald-500" : data.strength >= 40 ? "bg-zinc-400" : "bg-red-500",
            )}
            style={{ width: `${data.strength}%` }}
          />
        </div>
        <span className="text-[11px] text-muted-foreground font-mono">{data.strength}%</span>
      </div>

      {/* Factor mini-table */}
      <div className="space-y-1">
        {data.factors.map((f) => (
          <div key={f.name} className="flex items-center gap-2 text-[11px]">
            <DirectionIcon direction={f.direction} />
            <span className="flex-1 text-zinc-400 truncate">{f.name}</span>
            <span
              className={cn(
                "font-mono font-bold w-5 text-right",
                f.contribution > 0 ? "text-emerald-400" : f.contribution < 0 ? "text-red-400" : "text-zinc-600",
              )}
            >
              {f.contribution > 0 ? "+" : ""}{f.contribution}
            </span>
          </div>
        ))}
      </div>

      <div className="text-[10px] text-muted-foreground/50 text-right">
        Net: {data.netScore > 0 ? "+" : ""}{data.netScore} / {data.maxPossibleScore}
      </div>
    </div>
  );
}

// ── Post-Event Reaction Card ────────────────────────────────────────────────

function DeltaBadge({ value }: { value: number | null }) {
  if (value == null) return <span className="text-[10px] text-zinc-600 font-mono">--</span>;
  const color = value > 0 ? "text-emerald-400" : value < 0 ? "text-red-400" : "text-zinc-400";
  return (
    <span className={cn("text-[11px] font-bold font-mono", color)}>
      {value > 0 ? "+" : ""}{value.toFixed(3)}%
    </span>
  );
}

function ReactionGroup({ eventName, scheduledAt, reactions }: { eventName: string; scheduledAt: string; reactions: EventReaction[] }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-foreground">{eventName}</span>
        <span className="text-[10px] text-muted-foreground font-mono">
          {new Date(scheduledAt).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-1 text-center">
        <span className="text-[9px] text-muted-foreground/60 uppercase">Symbol</span>
        <span className="text-[9px] text-muted-foreground/60 uppercase">+15m</span>
        <span className="text-[9px] text-muted-foreground/60 uppercase">+1h</span>
      </div>
      {reactions.map((r) => (
        <div key={r.symbol} className="grid grid-cols-3 gap-1 text-center items-center">
          <span className="text-[11px] text-zinc-600 font-medium">{r.symbol.replace("_", "/")}</span>
          <DeltaBadge value={r.delta15mPct} />
          <DeltaBadge value={r.delta1hPct} />
        </div>
      ))}
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function NewsPage() {
  const { upcoming, released, isLoading: calLoading } = useNewsCalendar();
  const { fundamentals, isLoading: fundLoading } = useAllFundamentals();
  const { reactions } = useEventReactions();

  // Group reactions by event
  const reactionsByEvent = reactions.reduce<Record<string, EventReaction[]>>((acc, r) => {
    const key = r.eventId;
    if (!acc[key]) acc[key] = [];
    acc[key].push(r);
    return acc;
  }, {});

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">News & Fundamentals</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Economic calendar and macro factor scores across all instruments
        </p>
      </div>

      {/* Economic Calendar */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Economic Calendar
        </h2>

        {calLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-card border border-border rounded-xl animate-pulse" />
            ))}
          </div>
        ) : upcoming.length === 0 && released.length === 0 ? (
          <p className="text-sm text-muted-foreground/60 py-8 text-center">
            Loading economic calendar data...
          </p>
        ) : (
          <div className="space-y-2">
            {upcoming.length > 0 && (
              <>
                <p className="text-xs text-muted-foreground/60 font-medium uppercase tracking-wider">
                  Upcoming ({upcoming.length})
                </p>
                {upcoming.map((e) => (
                  <EventCard key={e.id} event={e} />
                ))}
              </>
            )}

            {released.length > 0 && (
              <>
                <p className="text-xs text-muted-foreground/60 font-medium uppercase tracking-wider mt-6">
                  Released ({released.length})
                </p>
                {released.map((e) => (
                  <EventCard key={e.id} event={e} />
                ))}
              </>
            )}
          </div>
        )}
      </section>

      {/* Post-Event Impact */}
      {Object.keys(reactionsByEvent).length > 0 && (
        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Post-Event Impact
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Object.entries(reactionsByEvent).map(([eventId, eventReactions]) => (
              <ReactionGroup
                key={eventId}
                eventName={eventReactions[0].eventName}
                scheduledAt={eventReactions[0].scheduledAt}
                reactions={eventReactions}
              />
            ))}
          </div>
        </section>
      )}

      {/* Fundamentals Grid */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Macro Fundamentals
        </h2>

        {fundLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-48 bg-card border border-border rounded-xl animate-pulse" />
            ))}
          </div>
        ) : fundamentals.length === 0 ? (
          <p className="text-sm text-muted-foreground/60 py-8 text-center">
            No fundamentals data available — check FRED_API_KEY
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {fundamentals.map((f) => (
              <FundamentalsCard key={f.symbol} data={f} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
