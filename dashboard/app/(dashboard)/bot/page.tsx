"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBotStatus } from "@/lib/hooks/use-bot-status";
import { useMSS } from "@/lib/hooks/use-mss";
import type { MSSEvent } from "@/lib/hooks/use-mss";
import { useRegime } from "@/lib/hooks/use-regime";
import { useVolume } from "@/lib/hooks/use-volume";
import type { VolumeState } from "@/lib/hooks/use-volume";
import { Activity, Clock, Star, BarChart3, TrendingUp, TrendingDown, Zap, ShieldCheck, ShieldX, Gauge, Layers, ArrowUpCircle, ArrowDownCircle, MinusCircle, Crosshair } from "lucide-react";
import { cn } from "@/lib/utils";

const SESSION_COLORS: Record<string, string> = {
  ASIA: "bg-purple-500",
  LONDON: "bg-blue-500",
  NY: "bg-emerald-500",
  OUTSIDE: "bg-zinc-600",
};

const REGIME_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  TREND: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  RANGE: { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30" },
  TRANSITION: { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/30" },
};

const TREND_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  UP: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30", bar: "bg-emerald-500" },
  DOWN: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30", bar: "bg-red-500" },
  NEUTRAL: { bg: "bg-zinc-500/20", text: "text-zinc-300", border: "border-zinc-500/30", bar: "bg-zinc-400" },
};

const VOLATILITY_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  LOW: { bg: "bg-teal-500/20", text: "text-teal-400", border: "border-teal-500/30", bar: "bg-teal-500" },
  MEDIUM: { bg: "bg-zinc-500/20", text: "text-zinc-300", border: "border-zinc-500/30", bar: "bg-zinc-400" },
  HIGH: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30", bar: "bg-red-500" },
};

function RegimeBadge({ regime, size = "sm" }: { regime: string; size?: "sm" | "lg" }) {
  const colors = REGIME_COLORS[regime] ?? REGIME_COLORS.TRANSITION;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        {regime}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {regime}
    </span>
  );
}

function VolatilityBadge({ state, size = "sm" }: { state: string; size?: "sm" | "lg" }) {
  const colors = VOLATILITY_COLORS[state] ?? VOLATILITY_COLORS.MEDIUM;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        {state} VOL
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {state}
    </span>
  );
}

function TrendBadge({ direction, score, size = "sm" }: { direction: string; score?: number; size?: "sm" | "lg" }) {
  const colors = TREND_COLORS[direction] ?? TREND_COLORS.NEUTRAL;
  const label = score !== undefined ? `${direction} ${score.toFixed(0)}` : direction;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        {label}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const VOLUME_STATE_COLORS: Record<VolumeState, { bg: string; text: string; border: string; dot: string }> = {
  IN_VALUE:        { bg: "bg-cyan-500/20",   text: "text-cyan-400",   border: "border-cyan-500/30",   dot: "bg-cyan-500" },
  ACCEPTING_ABOVE: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30", dot: "bg-emerald-500" },
  ACCEPTING_BELOW: { bg: "bg-red-500/20",    text: "text-red-400",    border: "border-red-500/30",    dot: "bg-red-500" },
  REJECTING_ABOVE: { bg: "bg-amber-500/20",  text: "text-amber-400",  border: "border-amber-500/30",  dot: "bg-amber-500" },
  REJECTING_BELOW: { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/30", dot: "bg-orange-500" },
};

function VolumeStateBadge({ state, size = "sm" }: { state: string; size?: "sm" | "lg" }) {
  const colors = VOLUME_STATE_COLORS[state as VolumeState] ?? VOLUME_STATE_COLORS.IN_VALUE;
  const label = state.replace(/_/g, " ");
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        {label}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const LIQUIDITY_DRAW_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  ABOVE:   { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  BELOW:   { bg: "bg-red-500/20",     text: "text-red-400",     border: "border-red-500/30" },
  NEUTRAL: { bg: "bg-zinc-500/20",    text: "text-zinc-300",    border: "border-zinc-500/30" },
};

function LiquidityDrawBadge({
  direction, score, size = "sm",
}: { direction: string; score?: number; size?: "sm" | "lg" }) {
  const colors = LIQUIDITY_DRAW_COLORS[direction] ?? LIQUIDITY_DRAW_COLORS.NEUTRAL;
  const Icon =
    direction === "ABOVE" ? ArrowUpCircle :
    direction === "BELOW" ? ArrowDownCircle :
    MinusCircle;
  const label = score !== undefined
    ? `DRAW ${direction} (${score.toFixed(0)})`
    : `DRAW ${direction}`;
  if (size === "lg") {
    return (
      <span className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        <Icon className="h-4 w-4" />
        {label}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const MTF_ALIGN_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  FULL_ALIGN_UP:     { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  FULL_ALIGN_DOWN:   { bg: "bg-red-500/20",     text: "text-red-400",     border: "border-red-500/30" },
  PARTIAL_ALIGN_UP:  { bg: "bg-emerald-500/10", text: "text-emerald-300", border: "border-emerald-500/20" },
  PARTIAL_ALIGN_DOWN:{ bg: "bg-red-500/10",     text: "text-red-300",     border: "border-red-500/20" },
  CONFLICT:          { bg: "bg-amber-500/20",   text: "text-amber-400",   border: "border-amber-500/30" },
  WEAK_ALIGN:        { bg: "bg-zinc-500/20",    text: "text-zinc-300",    border: "border-zinc-500/30" },
};

function MTFAlignmentBadge({
  state, score, size = "sm",
}: { state: string; score?: number; size?: "sm" | "lg" }) {
  const colors = MTF_ALIGN_COLORS[state] ?? MTF_ALIGN_COLORS.WEAK_ALIGN;
  const label = state.replace(/_/g, " ");
  if (size === "lg") {
    return (
      <span className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        <Crosshair className="h-4 w-4" />
        {score !== undefined ? `${label} (${score.toFixed(0)}/100)` : label}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const SETUP_GRADE_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  NO_TRADE:     { bg: "bg-zinc-500/20",    text: "text-zinc-400",   border: "border-zinc-500/30",    bar: "bg-zinc-400" },
  MEDIUM_SETUP: { bg: "bg-amber-500/20",   text: "text-amber-400",  border: "border-amber-500/30",   bar: "bg-amber-500" },
  HIGH_SETUP:   { bg: "bg-blue-500/20",    text: "text-blue-400",   border: "border-blue-500/30",    bar: "bg-blue-500" },
  A_PLUS_SETUP: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30", bar: "bg-emerald-500" },
};

const GRADE_LABELS: Record<string, string> = {
  NO_TRADE: "NO TRADE", MEDIUM_SETUP: "MEDIUM", HIGH_SETUP: "HIGH", A_PLUS_SETUP: "A+ SETUP",
};

function SetupGradeBadge({ grade, score, size = "sm" }: { grade: string; score?: number; size?: "sm" | "lg" }) {
  const colors = SETUP_GRADE_COLORS[grade] ?? SETUP_GRADE_COLORS.NO_TRADE;
  const label  = GRADE_LABELS[grade] ?? grade;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        {score !== undefined ? `${score.toFixed(0)}/100 ` : ""}{label}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const TRADE_BIAS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  LONG:    { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  SHORT:   { bg: "bg-red-500/20",     text: "text-red-400",     border: "border-red-500/30" },
  NEUTRAL: { bg: "bg-zinc-500/20",    text: "text-zinc-300",    border: "border-zinc-500/30" },
};

function TradeBiasBadge({ bias, size = "sm" }: { bias: string; size?: "sm" | "lg" }) {
  const colors = TRADE_BIAS_COLORS[bias] ?? TRADE_BIAS_COLORS.NEUTRAL;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        BIAS: {bias}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {bias}
    </span>
  );
}

const PARTICIPATION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  LOW_ACTIVITY: { bg: "bg-zinc-500/20",  text: "text-zinc-300",   border: "border-zinc-500/30" },
  NORMAL:       { bg: "bg-cyan-500/20",  text: "text-cyan-400",   border: "border-cyan-500/30" },
  ELEVATED:     { bg: "bg-amber-500/20", text: "text-amber-400",  border: "border-amber-500/30" },
  EXTREME:      { bg: "bg-red-500/20",   text: "text-red-400",    border: "border-red-500/30" },
};

function ParticipationBadge({
  state, rvol, size = "sm",
}: { state: string; rvol?: number; size?: "sm" | "lg" }) {
  const colors = PARTICIPATION_COLORS[state] ?? PARTICIPATION_COLORS.NORMAL;
  const label = state.replace(/_/g, " ");
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        PARTICIPATION: {label}{rvol !== undefined ? ` (RVOL ${rvol.toFixed(2)}x)` : ""}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

const BREAKOUT_TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CONTINUATION: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  FAKEOUT:      { bg: "bg-red-500/20",     text: "text-red-400",     border: "border-red-500/30" },
  UNCLEAR:      { bg: "bg-amber-500/20",   text: "text-amber-400",   border: "border-amber-500/30" },
};

function BreakoutTypeBadge({
  type, score, size = "sm",
}: { type: string; score?: number; size?: "sm" | "lg" }) {
  const colors = BREAKOUT_TYPE_COLORS[type] ?? BREAKOUT_TYPE_COLORS.UNCLEAR;
  const label = type === "FAKEOUT" ? "LIKELY FAKEOUT" : type;
  if (size === "lg") {
    return (
      <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold border", colors.bg, colors.text, colors.border)}>
        Breakout: {label}{score !== undefined ? ` (${score.toFixed(0)}/100)` : ""}
      </span>
    );
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", colors.bg, colors.text)}>
      {label}
    </span>
  );
}

function flagColor(flag: string): string {
  if (/(TRENDING UP|LONG BIAS|A\+|ALIGN UP|ABOVE|ACCEPTING ABOVE|CONTINUATION)/.test(flag))
    return "bg-emerald-500/20 text-emerald-400";
  if (/(TRENDING DOWN|SHORT BIAS|ALIGN DOWN|BELOW|ACCEPTING BELOW|FAKEOUT)/.test(flag))
    return "bg-red-500/20 text-red-400";
  if (/(VOLATILITY|AGGRESSIVE|ELEVATED)/.test(flag))
    return "bg-amber-500/20 text-amber-400";
  if (/(RANGE|QUIET|MIXED|WEAK|PARTIAL)/.test(flag))
    return "bg-zinc-600/40 text-zinc-300";
  if (/(SESSION)/.test(flag))
    return "bg-purple-500/20 text-purple-300";
  return "bg-zinc-600/40 text-zinc-300";
}

const SESSION_TEXT_COLORS: Record<string, string> = {
  ASIA: "text-purple-400",
  LONDON: "text-blue-400",
  NY: "text-emerald-400",
  OUTSIDE: "text-zinc-400",
};

function formatTime(iso: string | null): string {
  if (!iso) return "\u2014";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" }) + " UTC";
  } catch {
    return "\u2014";
  }
}

function formatPrice(val: number | null): string {
  if (val === null) return "\u2014";
  return `$${val.toFixed(2)}`;
}

function MSSCard({ event }: { event: MSSEvent }) {
  const isBull = event.direction === "BULL";
  const accepted = event.is_accepted;
  const borderColor = !accepted
    ? "border-zinc-700"
    : isBull
    ? "border-emerald-500/30"
    : "border-red-500/30";
  const bgColor = !accepted
    ? "bg-zinc-800/30"
    : isBull
    ? "bg-emerald-500/5"
    : "bg-red-500/5";

  const time = (() => {
    try {
      const d = new Date(event.timestamp);
      return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" });
    } catch {
      return "--:--";
    }
  })();

  return (
    <div className={cn("rounded-lg border p-3 space-y-2", borderColor, bgColor)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isBull ? (
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-400" />
          )}
          <span className={cn("text-sm font-bold", isBull ? "text-emerald-400" : "text-red-400")}>
            {event.direction} MSS
          </span>
          <span className={cn(
            "text-[10px] px-1.5 py-0.5 rounded font-medium",
            SESSION_TEXT_COLORS[event.session] ?? "text-zinc-400",
            SESSION_COLORS[event.session] ? SESSION_COLORS[event.session] + "/20" : "bg-zinc-700/30"
          )}>
            {event.session}
          </span>
          {event.regime && <RegimeBadge regime={event.regime} />}
          {event.volatility_state && <VolatilityBadge state={event.volatility_state} />}
          {event.trend_direction && <TrendBadge direction={event.trend_direction} score={event.trend_strength_score ?? undefined} />}
          {event.volume_state && <VolumeStateBadge state={event.volume_state} />}
          {event.mtf_alignment_state && <MTFAlignmentBadge state={event.mtf_alignment_state} />}
          {event.breakout_type && <BreakoutTypeBadge type={event.breakout_type} />}
          {event.setup_grade && <SetupGradeBadge grade={event.setup_grade} />}
          {event.event_trade_bias && <TradeBiasBadge bias={event.event_trade_bias} />}
        </div>
        <span className="text-xs text-muted-foreground">{time} UTC</span>
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">
          Close <span className="text-foreground font-medium">${event.price.toFixed(2)}</span>
          {" / "}
          CP <span className="text-foreground font-medium">${event.control_point_price.toFixed(2)}</span>
        </span>
        {accepted ? (
          <span className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck className="h-3 w-3" /> Accepted
          </span>
        ) : (
          <span className="flex items-center gap-1 text-red-400">
            <ShieldX className="h-3 w-3" /> Rejected
          </span>
        )}
      </div>

      {/* Environment summary */}
      {event.environment_summary && (
        <p className="text-[10px] text-zinc-300 italic leading-relaxed">
          {event.environment_summary}
        </p>
      )}

      {/* Context flag pills */}
      {event.context_flags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {event.context_flags.map((flag) => (
            <span key={flag} className={cn(
              "text-[9px] px-1.5 py-0.5 rounded font-medium",
              flagColor(flag)
            )}>
              {flag}
            </span>
          ))}
        </div>
      )}

      {/* Displacement quality bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>Displacement</span>
          <span>{(event.displacement_quality * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-zinc-800 rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full bg-purple-500 transition-all"
            style={{ width: `${event.displacement_quality * 100}%` }}
          />
        </div>
      </div>

      {/* Context distances */}
      {(event.distance_to_pdh !== null || event.distance_to_pdl !== null) && (
        <div className="flex gap-3 text-[10px] text-muted-foreground">
          {event.distance_to_pdh !== null && (
            <span>PDH: <span className={event.distance_to_pdh >= 0 ? "text-emerald-400" : "text-red-400"}>{event.distance_to_pdh >= 0 ? "+" : ""}{event.distance_to_pdh.toFixed(2)}</span></span>
          )}
          {event.distance_to_pdl !== null && (
            <span>PDL: <span className={event.distance_to_pdl >= 0 ? "text-emerald-400" : "text-red-400"}>{event.distance_to_pdl >= 0 ? "+" : ""}{event.distance_to_pdl.toFixed(2)}</span></span>
          )}
        </div>
      )}

      {/* Liquidity draw context */}
      {event.liquidity_draw_direction && (
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-muted-foreground">Liquidity:</span>
          <LiquidityDrawBadge
            direction={event.liquidity_draw_direction}
            score={event.liquidity_magnet_score ?? undefined}
          />
        </div>
      )}

      {/* Session liquidity levels */}
      {(event.session_high !== null || event.session_low !== null) && (
        <div className="flex gap-3 text-[10px] text-muted-foreground">
          <span className="text-muted-foreground">Session:</span>
          {event.session_high !== null && (
            <span>
              H <span className="text-emerald-400 font-medium">${event.session_high.toFixed(2)}</span>
              {event.dist_session_high !== null && (
                <span className="text-zinc-400 ml-1">({event.dist_session_high >= 0 ? "+" : ""}{event.dist_session_high.toFixed(2)} ATR)</span>
              )}
            </span>
          )}
          {event.session_low !== null && (
            <span>
              L <span className="text-red-400 font-medium">${event.session_low.toFixed(2)}</span>
              {event.dist_session_low !== null && (
                <span className="text-zinc-400 ml-1">({event.dist_session_low.toFixed(2)} ATR)</span>
              )}
            </span>
          )}
        </div>
      )}

      {/* Participation / RVOL context */}
      {event.participation_state && (
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-muted-foreground">Participation:</span>
          <ParticipationBadge
            state={event.participation_state}
            rvol={event.rvol_ratio ?? undefined}
          />
          {event.volume_spike_flag && (
            <span className="text-red-400 font-medium">⚡ SPIKE</span>
          )}
        </div>
      )}

      {/* Volume context */}
      {(event.vwap !== null || event.poc !== null) && (
        <div className="flex gap-3 text-[10px] text-muted-foreground">
          {event.vwap !== null && (
            <span>VWAP: <span className="text-cyan-400 font-medium">${event.vwap.toFixed(2)}</span></span>
          )}
          {event.poc !== null && (
            <span>POC: <span className="text-amber-400 font-medium">${event.poc.toFixed(2)}</span></span>
          )}
          {event.vah !== null && event.val !== null && (
            <span>VA: <span className="text-zinc-300 font-medium">${event.val.toFixed(2)}–${event.vah.toFixed(2)}</span></span>
          )}
        </div>
      )}

      {/* MTF alignment context */}
      {event.mtf_alignment_state && (
        <div className="space-y-1">
          <div className="flex gap-3 text-[10px] text-muted-foreground">
            <span>HTF: <span className="text-foreground font-medium">{event.htf_bias ?? "—"}</span></span>
            <span>15M: <span className="text-foreground font-medium">{event.mtf_structure_bias ?? "—"}</span></span>
            <span>5M: <span className="text-foreground font-medium">{event.ltf_direction ?? "—"}</span></span>
          </div>
          <div className="flex items-center gap-2 text-[10px]">
            <span className="text-muted-foreground">MTF Alignment:</span>
            <MTFAlignmentBadge
              state={event.mtf_alignment_state}
              score={event.mtf_alignment_score ?? undefined}
            />
          </div>
        </div>
      )}

      {/* Breakout quality */}
      {event.breakout_type && event.breakout_quality_score !== null && (
        <div className="space-y-1.5">
          <BreakoutTypeBadge
            type={event.breakout_type}
            score={event.breakout_quality_score ?? undefined}
            size="lg"
          />
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] text-muted-foreground pl-0.5">
            {event.break_strength_score !== null && (
              <span>Break Strength: <span className="text-foreground font-medium">{event.break_strength_score?.toFixed(0)}</span></span>
            )}
            {event.retest_quality_score !== null && (
              <span>Retest Quality: <span className="text-foreground font-medium">{event.retest_quality_score?.toFixed(0)}</span>
                {event.has_clean_retest && <span className="text-emerald-400 ml-1">✓</span>}
              </span>
            )}
            {event.volume_confirmation_score !== null && (
              <span>Volume Confirm: <span className="text-foreground font-medium">{event.volume_confirmation_score?.toFixed(0)}</span></span>
            )}
            {event.environment_alignment_score !== null && (
              <span>Env Alignment: <span className="text-foreground font-medium">{event.environment_alignment_score?.toFixed(0)}</span></span>
            )}
          </div>
        </div>
      )}

      {/* Confluence */}
      {event.confluence_score !== null && event.setup_grade && (
        <div className="space-y-1.5 rounded-lg border border-zinc-700/50 bg-zinc-800/30 p-2.5">
          <div className="flex items-center gap-2">
            <SetupGradeBadge grade={event.setup_grade} score={event.confluence_score ?? undefined} size="lg" />
            {event.event_trade_bias && <TradeBiasBadge bias={event.event_trade_bias} size="lg" />}
          </div>
          {event.confluence_components && (
            <div className="grid grid-cols-4 gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground pt-0.5">
              <span>Trend <span className="text-foreground">{event.confluence_components.trend}</span></span>
              <span>Regime <span className="text-foreground">{event.confluence_components.regime}</span></span>
              <span>Vol <span className="text-foreground">{event.confluence_components.volatility}</span></span>
              <span>Volume <span className="text-foreground">{event.confluence_components.volume}</span></span>
              <span>Liq <span className="text-foreground">{event.confluence_components.liquidity}</span></span>
              <span>MTF <span className="text-foreground">{event.confluence_components.mtf}</span></span>
              <span>MSS <span className="text-foreground">{event.confluence_components.mss}</span></span>
              <span>BKT <span className="text-foreground">{event.confluence_components.breakout}</span></span>
            </div>
          )}
        </div>
      )}

      {!accepted && event.rejection_reason && (
        <p className="text-[10px] text-red-400/70 truncate">{event.rejection_reason}</p>
      )}
    </div>
  );
}

export default function BotStatusPage() {
  const { status, isLoading } = useBotStatus();
  const { mss, isLoading: mssLoading } = useMSS();
  const { regime: regimeData, isLoading: regimeLoading } = useRegime();
  const { volume: volumeData, isLoading: volumeLoading } = useVolume();

  if (isLoading || !status) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Bot Status</h1>
          <p className="text-sm text-muted-foreground mt-1">Session liquidity levels and market structure</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="bg-card border-border animate-pulse">
              <CardContent className="p-6 h-40" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const { current_session, sessions, daily } = status;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Bot Status</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Session liquidity levels for {status.symbol} &mdash; {new Date(status.timestamp).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "UTC" })} UTC
        </p>
      </div>

      {status.is_holiday && (
        <div className="flex items-center gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-2.5 text-sm text-yellow-300">
          <Clock className="h-4 w-4 shrink-0" />
          <span>
            Market closed &mdash; showing last trading session
            {status.data_date && <> ({status.data_date})</>}
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* A. Current Session Status */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4 text-brand" />
              Current Session
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold", SESSION_TEXT_COLORS[current_session.session] ?? "text-foreground")}>
                {current_session.label}
              </span>
              {current_session.session !== "OUTSIDE" && (
                <span className="text-xs text-muted-foreground">
                  {current_session.start_utc} &ndash; {current_session.end_utc} UTC
                </span>
              )}
            </div>

            {current_session.session !== "OUTSIDE" ? (
              <>
                {/* Progress bar */}
                <div className="w-full bg-zinc-800 rounded-full h-2.5">
                  <div
                    className={cn("h-2.5 rounded-full transition-all", SESSION_COLORS[current_session.session])}
                    style={{ width: `${current_session.progress_pct}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{current_session.progress_pct}% complete</span>
                  <span>{current_session.remaining_min} min remaining</span>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Waiting for next session...</p>
            )}
          </CardContent>
        </Card>

        {/* B. Today's Session Levels */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-cyan" />
              Session Levels
              {status.is_holiday && <span className="text-xs font-normal text-yellow-400 ml-1">(historical)</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted-foreground border-b border-border">
                    <th className="text-left py-1.5 font-medium">Session</th>
                    <th className="text-right py-1.5 font-medium">High</th>
                    <th className="text-right py-1.5 font-medium">Low</th>
                    <th className="text-right py-1.5 font-medium">Bars</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => {
                    const isPDH = daily.pdh !== null && s.high === daily.pdh;
                    const isPDL = daily.pdl !== null && s.low === daily.pdl;
                    return (
                      <tr key={s.session} className="border-b border-border/50">
                        <td className="py-2">
                          <span className={cn("font-medium", SESSION_TEXT_COLORS[s.session] ?? "text-foreground")}>
                            {s.session}
                          </span>
                        </td>
                        <td className="text-right py-2 text-success">
                          {formatPrice(s.high)}
                          {isPDH && <Star className="inline h-3 w-3 ml-1 text-yellow-400" />}
                        </td>
                        <td className="text-right py-2 text-loss">
                          {formatPrice(s.low)}
                          {isPDL && <Star className="inline h-3 w-3 ml-1 text-yellow-400" />}
                        </td>
                        <td className="text-right py-2 text-muted-foreground">{s.bar_count}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* C. Session Timeline */}
        <Card className="bg-card border-border md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4 text-yellow-400" />
              Session Timeline (UTC)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-12 bg-zinc-800/50 rounded-lg overflow-hidden">
              {/* 24-hour background grid */}
              {[0, 6, 12, 18].map((h) => (
                <div
                  key={h}
                  className="absolute top-0 bottom-0 border-l border-zinc-700"
                  style={{ left: `${(h / 24) * 100}%` }}
                />
              ))}

              {/* Session blocks */}
              {[
                { name: "ASIA", start: 0, end: 6 },
                { name: "LONDON", start: 6, end: 12 },
                { name: "NY", start: 13.5, end: 20 },
              ].map((s) => (
                <div
                  key={s.name}
                  className={cn(
                    "absolute top-1 bottom-1 rounded opacity-70 flex items-center justify-center text-[10px] font-bold text-foreground",
                    SESSION_COLORS[s.name]
                  )}
                  style={{
                    left: `${(s.start / 24) * 100}%`,
                    width: `${((s.end - s.start) / 24) * 100}%`,
                  }}
                >
                  {s.name}
                </div>
              ))}

              {/* Current time marker */}
              {(() => {
                const now = new Date(status.timestamp);
                const hourFrac = now.getUTCHours() + now.getUTCMinutes() / 60;
                return (
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-brand z-10"
                    style={{ left: `${(hourFrac / 24) * 100}%` }}
                  >
                    <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-brand rounded-full" />
                  </div>
                );
              })()}
            </div>

            {/* Hour labels */}
            <div className="flex justify-between mt-1 text-[10px] text-muted-foreground px-0.5">
              {[0, 3, 6, 9, 12, 15, 18, 21, 24].map((h) => (
                <span key={h}>{String(h % 24).padStart(2, "0")}:00</span>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* D. PDH/PDL & Activity */}
        <Card className="bg-card border-border md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-400" />
              Previous Day Levels
              {daily.date && <span className="text-xs font-normal ml-1">({daily.date})</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {daily.pdh !== null ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-success/10 rounded-lg p-4 border border-success/20">
                  <p className="text-xs text-muted-foreground mb-1">Previous Day High (PDH)</p>
                  <p className="text-xl font-bold text-success">{formatPrice(daily.pdh)}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatTime(daily.pdh_time)} &middot;{" "}
                    <span className={SESSION_TEXT_COLORS[daily.pdh_session ?? ""] ?? ""}>{daily.pdh_session}</span> session
                  </p>
                </div>
                <div className="bg-loss/10 rounded-lg p-4 border border-loss/20">
                  <p className="text-xs text-muted-foreground mb-1">Previous Day Low (PDL)</p>
                  <p className="text-xl font-bold text-loss">{formatPrice(daily.pdl)}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatTime(daily.pdl_time)} &middot;{" "}
                    <span className={SESSION_TEXT_COLORS[daily.pdl_session ?? ""] ?? ""}>{daily.pdl_session}</span> session
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No previous day data available.</p>
            )}
          </CardContent>
        </Card>
        {/* E. Market Regime */}
        <Card className="bg-card border-border md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Gauge className="h-4 w-4 text-orange-400" />
              Market Regime
              {regimeData?.date && <span className="text-xs font-normal ml-1">({regimeData.date})</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {regimeLoading ? (
              <div className="h-24 flex items-center justify-center">
                <p className="text-sm text-muted-foreground animate-pulse">Loading regime data...</p>
              </div>
            ) : !regimeData ? (
              <p className="text-sm text-muted-foreground">No regime data available.</p>
            ) : (
              <div className="space-y-4">
                {/* Top row: badge + stats */}
                <div className="flex items-center gap-3 flex-wrap">
                  <RegimeBadge regime={regimeData.current_regime} size="lg" />
                  {mss?.current_volatility_state && (
                    <VolatilityBadge state={mss.current_volatility_state} size="lg" />
                  )}
                  {mss?.current_trend_direction && (
                    <TrendBadge direction={mss.current_trend_direction} score={mss.current_trend_score} size="lg" />
                  )}
                  {mss?.current_liquidity_draw_direction && (
                    <LiquidityDrawBadge
                      direction={mss.current_liquidity_draw_direction}
                      score={mss.current_liquidity_magnet_score}
                      size="lg"
                    />
                  )}
                  {mss?.current_mtf_alignment_state && (
                    <MTFAlignmentBadge
                      state={mss.current_mtf_alignment_state}
                      score={mss.current_mtf_alignment_score}
                      size="lg"
                    />
                  )}
                  {mss?.current_setup_grade && (
                    <SetupGradeBadge
                      grade={mss.current_setup_grade}
                      score={mss.current_confluence_score}
                      size="lg"
                    />
                  )}
                  {mss?.current_trade_bias && (
                    <TradeBiasBadge bias={mss.current_trade_bias} size="lg" />
                  )}
                  {mss?.current_participation_state && (
                    <ParticipationBadge
                      state={mss.current_participation_state}
                      rvol={mss.current_rvol_ratio}
                      size="lg"
                    />
                  )}
                  {(mss?.current_session_high || mss?.current_session_low) && (
                    <div className="flex gap-4 text-sm flex-wrap">
                      {mss.current_session_high && (
                        <div>
                          <span className="text-muted-foreground">Session H </span>
                          <span className="text-emerald-400 font-mono font-medium">${mss.current_session_high.toFixed(2)}</span>
                        </div>
                      )}
                      {mss.current_session_low && (
                        <div>
                          <span className="text-muted-foreground">Session L </span>
                          <span className="text-red-400 font-mono font-medium">${mss.current_session_low.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  )}
                  {mss?.current_environment_summary && (
                    <p className="w-full text-xs text-zinc-300 italic">
                      {mss.current_environment_summary}
                    </p>
                  )}
                  <div className="flex gap-6 text-sm">
                    <div>
                      <span className="text-muted-foreground">ADX </span>
                      <span className="text-foreground font-mono font-medium">{regimeData.adx.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">BB Width </span>
                      <span className="text-foreground font-mono font-medium">{(regimeData.bb_width * 100).toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">VWAP Dist </span>
                      <span className="text-foreground font-mono font-medium">{(regimeData.vwap_distance * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                </div>

                {/* Distribution bar */}
                {regimeData.total_bars > 0 && (() => {
                  const d = regimeData.regime_distribution;
                  const total = regimeData.total_bars;
                  const trendPct = Math.round((d.TREND / total) * 100);
                  const rangePct = Math.round((d.RANGE / total) * 100);
                  const transPct = 100 - trendPct - rangePct;
                  return (
                    <div className="space-y-2">
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {trendPct > 0 && (
                          <div className="bg-emerald-500 transition-all" style={{ width: `${trendPct}%` }} />
                        )}
                        {rangePct > 0 && (
                          <div className="bg-amber-500 transition-all" style={{ width: `${rangePct}%` }} />
                        )}
                        {transPct > 0 && (
                          <div className="bg-orange-500 transition-all" style={{ width: `${transPct}%` }} />
                        )}
                      </div>
                      <div className="flex gap-4 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500" />
                          Trend {trendPct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-amber-500" />
                          Range {rangePct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-orange-500" />
                          Transition {transPct}%
                        </span>
                      </div>
                    </div>
                  );
                })()}

                {/* Trend direction distribution bar */}
                {mss?.trend_direction_distribution && regimeData.total_bars > 0 && (() => {
                  const td = mss.trend_direction_distribution;
                  const total = regimeData.total_bars;
                  const upPct = Math.round((td.UP / total) * 100);
                  const downPct = Math.round((td.DOWN / total) * 100);
                  const neutralPct = 100 - upPct - downPct;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Trend</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {upPct > 0 && (
                          <div className="bg-emerald-500 transition-all" style={{ width: `${upPct}%` }} />
                        )}
                        {neutralPct > 0 && (
                          <div className="bg-zinc-400 transition-all" style={{ width: `${neutralPct}%` }} />
                        )}
                        {downPct > 0 && (
                          <div className="bg-red-500 transition-all" style={{ width: `${downPct}%` }} />
                        )}
                      </div>
                      <div className="flex gap-4 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500" />
                          Up {upPct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-zinc-400" />
                          Neutral {neutralPct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-red-500" />
                          Down {downPct}%
                        </span>
                      </div>
                    </div>
                  );
                })()}

                {/* Liquidity draw distribution bar */}
                {mss?.liquidity_draw_distribution && regimeData.total_bars > 0 && (() => {
                  const ld = mss.liquidity_draw_distribution;
                  const total = ld.ABOVE + ld.BELOW + ld.NEUTRAL;
                  if (total === 0) return null;
                  const abovePct  = Math.round((ld.ABOVE   / total) * 100);
                  const belowPct  = Math.round((ld.BELOW   / total) * 100);
                  const neutralPct = 100 - abovePct - belowPct;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Liquidity Draw</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {abovePct   > 0 && <div className="bg-emerald-500 transition-all" style={{ width: `${abovePct}%` }} />}
                        {neutralPct > 0 && <div className="bg-zinc-400 transition-all"    style={{ width: `${neutralPct}%` }} />}
                        {belowPct   > 0 && <div className="bg-red-500 transition-all"     style={{ width: `${belowPct}%` }} />}
                      </div>
                      <div className="flex gap-4 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Above {abovePct}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-zinc-400" />Neutral {neutralPct}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Below {belowPct}%</span>
                      </div>
                    </div>
                  );
                })()}

                {/* Volatility distribution bar */}
                {mss?.volatility_distribution && regimeData.total_bars > 0 && (() => {
                  const vd = mss.volatility_distribution;
                  const total = regimeData.total_bars;
                  const lowPct = Math.round((vd.LOW / total) * 100);
                  const highPct = Math.round((vd.HIGH / total) * 100);
                  const medPct = 100 - lowPct - highPct;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Volatility</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {lowPct > 0 && (
                          <div className="bg-teal-500 transition-all" style={{ width: `${lowPct}%` }} />
                        )}
                        {medPct > 0 && (
                          <div className="bg-zinc-400 transition-all" style={{ width: `${medPct}%` }} />
                        )}
                        {highPct > 0 && (
                          <div className="bg-red-500 transition-all" style={{ width: `${highPct}%` }} />
                        )}
                      </div>
                      <div className="flex gap-4 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-teal-500" />
                          Low {lowPct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-zinc-400" />
                          Medium {medPct}%
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-red-500" />
                          High {highPct}%
                        </span>
                      </div>
                    </div>
                  );
                })()}

                {/* MTF alignment distribution bar */}
                {mss?.mtf_alignment_distribution && (() => {
                  const md = mss.mtf_alignment_distribution;
                  const total = Object.values(md).reduce((a, b) => a + b, 0);
                  if (total === 0) return null;
                  const pct = (v: number) => Math.round((v / total) * 100);
                  const faUp  = pct(md.FULL_ALIGN_UP);
                  const faDown = pct(md.FULL_ALIGN_DOWN);
                  const paUp  = pct(md.PARTIAL_ALIGN_UP);
                  const paDown = pct(md.PARTIAL_ALIGN_DOWN);
                  const conf  = pct(md.CONFLICT);
                  const weak  = 100 - faUp - faDown - paUp - paDown - conf;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">MTF Alignment</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {faUp   > 0 && <div className="bg-emerald-500 transition-all"   style={{ width: `${faUp}%` }} />}
                        {paUp   > 0 && <div className="bg-emerald-300/60 transition-all" style={{ width: `${paUp}%` }} />}
                        {weak   > 0 && <div className="bg-zinc-400 transition-all"       style={{ width: `${Math.max(0, weak)}%` }} />}
                        {conf   > 0 && <div className="bg-amber-500 transition-all"      style={{ width: `${conf}%` }} />}
                        {paDown > 0 && <div className="bg-red-300/60 transition-all"     style={{ width: `${paDown}%` }} />}
                        {faDown > 0 && <div className="bg-red-500 transition-all"        style={{ width: `${faDown}%` }} />}
                      </div>
                      <div className="flex gap-3 flex-wrap text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Full Up {faUp}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-300/60" />Part Up {paUp}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-zinc-400" />Weak {Math.max(0, weak)}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Conflict {conf}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Full Down {faDown}%</span>
                      </div>
                    </div>
                  );
                })()}

                {/* Confluence distribution bar */}
                {mss?.confluence_distribution && (() => {
                  const cd = mss.confluence_distribution;
                  const total = cd.NO_TRADE + cd.MEDIUM_SETUP + cd.HIGH_SETUP + cd.A_PLUS_SETUP;
                  if (total === 0) return null;
                  const pct = (v: number) => Math.round((v / total) * 100);
                  const noTrade = pct(cd.NO_TRADE);
                  const medium  = pct(cd.MEDIUM_SETUP);
                  const high    = pct(cd.HIGH_SETUP);
                  const aPlus   = 100 - noTrade - medium - high;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Confluence</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {noTrade > 0 && <div className="bg-zinc-400 transition-all"    style={{ width: `${noTrade}%` }} />}
                        {medium  > 0 && <div className="bg-amber-500 transition-all"   style={{ width: `${medium}%` }} />}
                        {high    > 0 && <div className="bg-blue-500 transition-all"    style={{ width: `${high}%` }} />}
                        {aPlus   > 0 && <div className="bg-emerald-500 transition-all" style={{ width: `${Math.max(0, aPlus)}%` }} />}
                      </div>
                      <div className="flex gap-3 flex-wrap text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-zinc-400" />No Trade {noTrade}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Medium {medium}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" />High {high}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />A+ {Math.max(0, aPlus)}%</span>
                      </div>
                    </div>
                  );
                })()}
                {/* Participation distribution bar */}
                {mss?.participation_state_distribution && (() => {
                  const pd = mss.participation_state_distribution;
                  const total = pd.LOW_ACTIVITY + pd.NORMAL + pd.ELEVATED + pd.EXTREME;
                  if (total === 0) return null;
                  const pct = (v: number) => Math.round((v / total) * 100);
                  const low     = pct(pd.LOW_ACTIVITY);
                  const normal  = pct(pd.NORMAL);
                  const elev    = pct(pd.ELEVATED);
                  const extreme = 100 - low - normal - elev;
                  return (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Participation (RVOL)</p>
                      <div className="flex h-3 rounded-full overflow-hidden">
                        {low     > 0 && <div className="bg-zinc-400 transition-all"    style={{ width: `${low}%` }} />}
                        {normal  > 0 && <div className="bg-cyan-500 transition-all"    style={{ width: `${normal}%` }} />}
                        {elev    > 0 && <div className="bg-amber-500 transition-all"   style={{ width: `${elev}%` }} />}
                        {extreme > 0 && <div className="bg-red-500 transition-all"     style={{ width: `${Math.max(0, extreme)}%` }} />}
                      </div>
                      <div className="flex gap-3 flex-wrap text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-zinc-400" />Low {low}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500" />Normal {normal}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Elevated {elev}%</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Extreme {Math.max(0, extreme)}%</span>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </CardContent>
        </Card>

        {/* F. Volume / Value Area */}
        <Card className="bg-card border-border md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              Volume / Value Area
              {(volumeData ?? mss)?.date && (
                <span className="text-xs font-normal ml-1">
                  ({(volumeData ?? mss)?.date})
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {volumeLoading ? (
              <div className="h-24 flex items-center justify-center">
                <p className="text-sm text-muted-foreground animate-pulse">Loading volume data...</p>
              </div>
            ) : (() => {
              const vwap   = volumeData?.current_vwap   ?? mss?.current_vwap   ?? null;
              const poc    = volumeData?.current_poc    ?? mss?.current_poc    ?? null;
              const vah    = volumeData?.current_vah    ?? mss?.current_vah    ?? null;
              const val    = volumeData?.current_val    ?? mss?.current_val    ?? null;
              const state  = volumeData?.current_volume_state ?? mss?.current_volume_state ?? null;
              const dist   = volumeData?.volume_state_distribution ?? mss?.volume_state_distribution ?? null;
              const total  = dist ? Object.values(dist).reduce((a, b) => a + b, 0) : 0;

              if (!vwap && !poc) {
                return <p className="text-sm text-muted-foreground">No volume data available.</p>;
              }

              return (
                <div className="space-y-4">
                  {/* Price levels row */}
                  <div className="flex items-center gap-6 flex-wrap">
                    {state && <VolumeStateBadge state={state} size="lg" />}
                    <div className="flex gap-6 text-sm flex-wrap">
                      {vwap !== null && (
                        <div>
                          <span className="text-muted-foreground">VWAP </span>
                          <span className="text-cyan-400 font-mono font-medium">${vwap.toFixed(2)}</span>
                        </div>
                      )}
                      {poc !== null && (
                        <div>
                          <span className="text-muted-foreground">POC </span>
                          <span className="text-amber-400 font-mono font-medium">${poc.toFixed(2)}</span>
                        </div>
                      )}
                      {vah !== null && val !== null && (
                        <div>
                          <span className="text-muted-foreground">VAH / VAL </span>
                          <span className="text-emerald-400 font-mono font-medium">${vah.toFixed(2)}</span>
                          <span className="text-muted-foreground"> / </span>
                          <span className="text-red-400 font-mono font-medium">${val.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* State distribution bar */}
                  {dist && total > 0 && (() => {
                    const pct = (k: keyof typeof dist) => Math.round((dist[k] / total) * 100);
                    const inValPct  = pct("IN_VALUE");
                    const accAbove  = pct("ACCEPTING_ABOVE");
                    const accBelow  = pct("ACCEPTING_BELOW");
                    const rejAbove  = pct("REJECTING_ABOVE");
                    const rejBelow  = 100 - inValPct - accAbove - accBelow - rejAbove;
                    return (
                      <div className="space-y-2">
                        <div className="flex h-3 rounded-full overflow-hidden">
                          {inValPct  > 0 && <div className="bg-cyan-500 transition-all"    style={{ width: `${inValPct}%` }} />}
                          {accAbove  > 0 && <div className="bg-emerald-500 transition-all" style={{ width: `${accAbove}%` }} />}
                          {rejAbove  > 0 && <div className="bg-amber-500 transition-all"   style={{ width: `${rejAbove}%` }} />}
                          {rejBelow  > 0 && <div className="bg-orange-500 transition-all"  style={{ width: `${rejBelow}%` }} />}
                          {accBelow  > 0 && <div className="bg-red-500 transition-all"     style={{ width: `${accBelow}%` }} />}
                        </div>
                        <div className="flex gap-3 flex-wrap text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500" />In Value {inValPct}%</span>
                          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Acc Above {accAbove}%</span>
                          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Rej Above {rejAbove}%</span>
                          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" />Rej Below {Math.max(0, rejBelow)}%</span>
                          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Acc Below {accBelow}%</span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              );
            })()}
          </CardContent>
        </Card>

        {/* G. Market Structure Shifts */}
        <Card className="bg-card border-border md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4 text-purple-400" />
              Market Structure Shifts (MSS)
              {mss && <span className="text-xs font-normal ml-1">({mss.date})</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {mssLoading ? (
              <div className="h-32 flex items-center justify-center">
                <p className="text-sm text-muted-foreground animate-pulse">Loading MSS data...</p>
              </div>
            ) : !mss || !mss.events || mss.events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No MSS events detected.</p>
            ) : (
              <div className="space-y-4">
                {/* Stats row */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-zinc-800/50 rounded-lg p-2.5 text-center">
                    <p className="text-lg font-bold text-foreground">{mss.total_mss}</p>
                    <p className="text-[10px] text-muted-foreground">Total</p>
                  </div>
                  <div className="bg-emerald-500/10 rounded-lg p-2.5 text-center border border-emerald-500/20">
                    <p className="text-lg font-bold text-emerald-400">{mss.accepted}</p>
                    <p className="text-[10px] text-muted-foreground">Accepted</p>
                  </div>
                  <div className="bg-red-500/10 rounded-lg p-2.5 text-center border border-red-500/20">
                    <p className="text-lg font-bold text-red-400">{mss.rejected}</p>
                    <p className="text-[10px] text-muted-foreground">Rejected</p>
                  </div>
                  <div className="bg-purple-500/10 rounded-lg p-2.5 text-center border border-purple-500/20">
                    <p className="text-lg font-bold text-purple-400">{(mss.avg_displacement_quality * 100).toFixed(0)}%</p>
                    <p className="text-[10px] text-muted-foreground">Avg Quality</p>
                  </div>
                </div>

                {/* MSS event cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {mss.events.map((event) => (
                    <MSSCard key={event.id} event={event} />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
