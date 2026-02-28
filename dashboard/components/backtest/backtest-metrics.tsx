"use client";

import {
  BarChart3,
  CheckCircle,
  Zap,
  TrendingUp,
  TrendingDown,
  Clock,
  Waves,
  Target,
} from "lucide-react";
import type { BacktestMetrics as Metrics } from "@/lib/hooks/use-backtest";
import type { MSSEvent, SweepEvent } from "@/lib/mss-pipeline";
import { cn } from "@/lib/utils";

interface BacktestMetricsProps {
  metrics: Metrics;
  mssEvents: MSSEvent[];
  sweepEvents: SweepEvent[];
  onEventClick: (timestamp: string) => void;
}

function MetricCard({ label, value, icon: Icon, color }: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={cn("h-3.5 w-3.5", color || "text-muted-foreground")} />
        <span className="text-[10px] uppercase text-muted-foreground font-medium">{label}</span>
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
    </div>
  );
}

function SessionBadge({ session }: { session: string }) {
  const colors: Record<string, string> = {
    ASIA: "bg-purple-500/20 text-purple-400",
    LONDON: "bg-blue-500/20 text-blue-400",
    NY: "bg-green-500/20 text-green-400",
    OUTSIDE: "bg-zinc-500/20 text-zinc-400",
  };
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors[session] || colors.OUTSIDE)}>
      {session}
    </span>
  );
}

function DirectionBadge({ direction }: { direction: "BULL" | "BEAR" }) {
  return (
    <span className={cn(
      "flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium",
      direction === "BULL" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
    )}>
      {direction === "BULL" ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {direction}
    </span>
  );
}

export function BacktestMetrics({ metrics, mssEvents, sweepEvents, onEventClick }: BacktestMetricsProps) {
  const formatTime = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleString("en-US", {
      month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Metrics cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 p-3 flex-shrink-0">
        <MetricCard label="Total MSS" value={metrics.total_mss} icon={BarChart3} color="text-pink" />
        <MetricCard label="Accepted" value={`${metrics.accepted_pct}%`} icon={CheckCircle} color="text-emerald-400" />
        <MetricCard label="Avg Quality" value={`${Math.round(metrics.avg_quality * 100)}%`} icon={Zap} color="text-amber-400" />
        <MetricCard label="Bull / Bear" value={`${metrics.bull_count} / ${metrics.bear_count}`} icon={TrendingUp} color="text-blue-400" />
        <MetricCard label="Best Session" value={metrics.best_session} icon={Clock} color="text-purple-400" />
        <MetricCard label="Total Bars" value={metrics.total_bars.toLocaleString()} icon={Target} />
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <h3 className="text-xs uppercase text-muted-foreground font-medium mb-2 sticky top-0 bg-background py-1">
          Events ({mssEvents.length + sweepEvents.length})
        </h3>

        <div className="space-y-1">
          {/* MSS events */}
          {mssEvents.map(event => (
            <button
              key={event.id}
              onClick={() => onEventClick(event.timestamp)}
              className="w-full flex items-center gap-3 px-3 py-2 bg-card border border-border rounded-lg hover:border-pink/40 transition-colors text-left"
            >
              <DirectionBadge direction={event.direction} />

              <span className="text-xs text-muted-foreground min-w-[110px]">
                {formatTime(event.timestamp)}
              </span>

              {/* Quality bar */}
              <div className="flex items-center gap-2 flex-1 min-w-[80px]">
                <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full",
                      event.displacement_quality >= 0.7 ? "bg-emerald-500" :
                      event.displacement_quality >= 0.5 ? "bg-amber-500" : "bg-red-500"
                    )}
                    style={{ width: `${Math.round(event.displacement_quality * 100)}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground w-8">
                  {Math.round(event.displacement_quality * 100)}%
                </span>
              </div>

              <SessionBadge session={event.session} />

              <span className={cn(
                "text-[10px] px-1.5 py-0.5 rounded font-medium",
                event.is_accepted ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-500/20 text-zinc-400"
              )}>
                {event.is_accepted ? "ACC" : "REJ"}
              </span>
            </button>
          ))}

          {/* Sweep events */}
          {sweepEvents.map((sweep, i) => (
            <button
              key={`sweep-${i}`}
              onClick={() => onEventClick(sweep.timestamp)}
              className="w-full flex items-center gap-3 px-3 py-2 bg-card border border-amber-500/20 rounded-lg hover:border-amber-500/40 transition-colors text-left"
            >
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-400">
                <Waves className="h-3 w-3" />
                SWEEP
              </span>

              <span className="text-xs text-muted-foreground min-w-[110px]">
                {formatTime(sweep.timestamp)}
              </span>

              <DirectionBadge direction={sweep.direction} />

              <span className="text-xs text-muted-foreground ml-auto">
                Pool: ${sweep.pool_price.toFixed(2)}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
