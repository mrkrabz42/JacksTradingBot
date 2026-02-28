"use client";

import { useState } from "react";
import { Bell, Trash2, TrendingUp, TrendingDown } from "lucide-react";
import { useMSSAlerts, type MSSAlert } from "@/lib/hooks/use-mss-alerts";

const SESSIONS = ["All", "NY", "LONDON", "ASIA", "OUTSIDE"] as const;
const DIRECTIONS = ["All", "BULL", "BEAR"] as const;

const SESSION_COLORS: Record<string, string> = {
  NY: "bg-blue-500/20 text-blue-400",
  LONDON: "bg-purple-500/20 text-purple-400",
  ASIA: "bg-amber-500/20 text-amber-400",
  OUTSIDE: "bg-zinc-500/20 text-zinc-400",
};

const REGIME_BADGE_COLORS: Record<string, string> = {
  TREND: "bg-emerald-500/20 text-emerald-400",
  RANGE: "bg-amber-500/20 text-amber-400",
  TRANSITION: "bg-orange-500/20 text-orange-400",
};

const VOLATILITY_BADGE_COLORS: Record<string, string> = {
  LOW: "bg-teal-500/20 text-teal-400",
  MEDIUM: "bg-zinc-500/20 text-zinc-300",
  HIGH: "bg-red-500/20 text-red-400",
};

const TREND_BADGE_COLORS: Record<string, string> = {
  UP: "bg-emerald-500/20 text-emerald-400",
  DOWN: "bg-red-500/20 text-red-400",
  NEUTRAL: "bg-zinc-500/20 text-zinc-300",
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AlertsPage() {
  const { alerts, isLoading, clearAlerts } = useMSSAlerts();
  const [sessionFilter, setSessionFilter] = useState<string>("All");
  const [directionFilter, setDirectionFilter] = useState<string>("All");

  const filtered = alerts.filter((a) => {
    if (sessionFilter !== "All" && a.session !== sessionFilter) return false;
    if (directionFilter !== "All" && a.direction !== directionFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          {alerts.length > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-pink/20 text-pink text-sm font-medium">
              {alerts.length}
            </span>
          )}
        </div>
        {alerts.length > 0 && (
          <button
            onClick={clearAlerts}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Clear All
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Session</span>
          <div className="flex gap-1">
            {SESSIONS.map((s) => (
              <button
                key={s}
                onClick={() => setSessionFilter(s)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  sessionFilter === s
                    ? "bg-white/10 text-white"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                }`}
              >
                {s === "All" ? "All" : s}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Direction</span>
          <div className="flex gap-1">
            {DIRECTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDirectionFilter(d)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  directionFilter === d
                    ? "bg-white/10 text-white"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                }`}
              >
                {d === "All" ? "All" : d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alert list */}
      {isLoading && alerts.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">Loading MSS data...</div>
      ) : filtered.length === 0 ? (
        <EmptyState hasAlerts={alerts.length > 0} />
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => (
            <AlertCard key={alert.id + alert.alertedAt} alert={alert} />
          ))}
        </div>
      )}
    </div>
  );
}

function AlertCard({ alert }: { alert: MSSAlert }) {
  const qualPct = Math.round(alert.displacement_quality * 100);
  const isBull = alert.direction === "BULL";

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Direction badge */}
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-bold ${
              isBull ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
            }`}
          >
            {isBull ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {alert.direction}
          </span>
          {/* Session tag */}
          <span
            className={`px-2 py-0.5 rounded-md text-xs font-medium ${
              SESSION_COLORS[alert.session] ?? SESSION_COLORS.OUTSIDE
            }`}
          >
            {alert.session}
          </span>
          {/* Accepted / Rejected */}
          <span
            className={`px-2 py-0.5 rounded-md text-xs font-medium ${
              alert.is_accepted
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-orange-500/10 text-orange-400"
            }`}
          >
            {alert.is_accepted ? "Accepted" : "Rejected"}
          </span>
          {/* Regime badge */}
          {alert.regime && (
            <span
              className={`px-2 py-0.5 rounded-md text-xs font-medium ${
                REGIME_BADGE_COLORS[alert.regime] ?? REGIME_BADGE_COLORS.TRANSITION
              }`}
            >
              {alert.regime}
            </span>
          )}
          {/* Volatility badge */}
          {alert.volatility_state && (
            <span
              className={`px-2 py-0.5 rounded-md text-xs font-medium ${
                VOLATILITY_BADGE_COLORS[alert.volatility_state] ?? VOLATILITY_BADGE_COLORS.MEDIUM
              }`}
            >
              {alert.volatility_state}
            </span>
          )}
          {/* Trend badge */}
          {alert.trend_direction && (
            <span
              className={`px-2 py-0.5 rounded-md text-xs font-medium ${
                TREND_BADGE_COLORS[alert.trend_direction] ?? TREND_BADGE_COLORS.NEUTRAL
              }`}
            >
              {alert.trend_direction}{alert.trend_strength_score != null ? ` ${Math.round(alert.trend_strength_score)}` : ""}
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground">{timeAgo(alert.alertedAt)}</span>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-muted-foreground">Close </span>
          <span className="text-white font-mono font-medium">${alert.price.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">CP </span>
          <span className="text-white font-mono font-medium">${alert.control_point_price.toFixed(2)}</span>
        </div>
        {alert.distance_to_pdh !== null && (
          <div>
            <span className="text-muted-foreground">PDH </span>
            <span className={`font-mono font-medium ${alert.distance_to_pdh >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {alert.distance_to_pdh >= 0 ? "+" : ""}
              {alert.distance_to_pdh.toFixed(2)}
            </span>
          </div>
        )}
        {alert.distance_to_pdl !== null && (
          <div>
            <span className="text-muted-foreground">PDL </span>
            <span className={`font-mono font-medium ${alert.distance_to_pdl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {alert.distance_to_pdl >= 0 ? "+" : ""}
              {alert.distance_to_pdl.toFixed(2)}
            </span>
          </div>
        )}
      </div>

      {/* Quality bar */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground w-16">Quality</span>
        <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              qualPct >= 65 ? "bg-emerald-500" : qualPct >= 40 ? "bg-amber-500" : "bg-red-500"
            }`}
            style={{ width: `${qualPct}%` }}
          />
        </div>
        <span className="text-xs text-white font-mono w-10 text-right">{qualPct}%</span>
      </div>
    </div>
  );
}

function EmptyState({ hasAlerts }: { hasAlerts: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] text-center">
      <div className="h-16 w-16 rounded-2xl bg-pink/10 flex items-center justify-center mb-4">
        <Bell className="h-8 w-8 text-pink" />
      </div>
      <h2 className="text-lg font-semibold text-white mb-2">
        {hasAlerts ? "No matching alerts" : "No alerts yet"}
      </h2>
      <p className="text-muted-foreground max-w-md">
        {hasAlerts
          ? "Try adjusting your filters to see more alerts."
          : "MSS events will appear here as they\u2019re detected during market hours."}
      </p>
    </div>
  );
}
