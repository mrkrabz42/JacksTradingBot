"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FundamentalsData, FundamentalFactor } from "@/lib/types";

function BiasLabel({ bias }: { bias: FundamentalsData["netBias"] }) {
  const color = {
    "Strong Bullish": "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    "Moderate Bullish": "bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20",
    "Neutral": "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
    "Moderate Bearish": "bg-red-500/10 text-red-400/80 border-red-500/20",
    "Strong Bearish": "bg-red-500/15 text-red-400 border-red-500/30",
  }[bias];

  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-[11px] font-bold border", color)}>
      {bias}
    </span>
  );
}

function StrengthBar({ strength, dampened }: { strength: number; dampened?: boolean }) {
  const displayStrength = dampened ? Math.min(60, Math.round(strength * 0.7)) : strength;
  const color =
    displayStrength >= 65 ? "bg-emerald-500" :
    displayStrength >= 40 ? "bg-zinc-400" :
    "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-black/5 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${displayStrength}%` }}
        />
      </div>
      <span className="text-[10px] text-muted-foreground font-mono text-right">
        {displayStrength}%{dampened && <span className="text-red-400/70 ml-0.5">(dampened)</span>}
      </span>
    </div>
  );
}

function DirectionIcon({ direction }: { direction: 1 | 0 | -1 }) {
  if (direction === 1) return <ArrowUpRight className="h-3 w-3 text-emerald-400" />;
  if (direction === -1) return <ArrowDownRight className="h-3 w-3 text-red-400" />;
  return <Minus className="h-3 w-3 text-zinc-500" />;
}

function StateChangeArrow({ factor }: { factor: FundamentalFactor }) {
  if (!factor.previousState || factor.previousState === factor.state) return null;
  // Determine if change is an improvement or deterioration
  const stateRank = { Bearish: -1, Neutral: 0, Bullish: 1 } as const;
  const prev = stateRank[factor.previousState];
  const curr = stateRank[factor.state];
  if (curr > prev) {
    return <span className="text-[10px] text-emerald-400" title={`was ${factor.previousState}`}>{"\u2197"}</span>;
  }
  return <span className="text-[10px] text-red-400" title={`was ${factor.previousState}`}>{"\u2198"}</span>;
}

function FactorRow({ factor }: { factor: FundamentalFactor }) {
  const contribColor =
    factor.contribution > 0 ? "text-emerald-400" :
    factor.contribution < 0 ? "text-red-400" :
    "text-zinc-500";

  return (
    <div className="flex items-center gap-2 py-1">
      <DirectionIcon direction={factor.direction} />
      <StateChangeArrow factor={factor} />
      <span className="flex-1 text-[11px] text-foreground/80 truncate">{factor.name}</span>
      <span className="text-[10px] text-muted-foreground font-mono w-4 text-center">{factor.weight}</span>
      <span className={cn("text-[11px] font-bold font-mono w-6 text-right", contribColor)}>
        {factor.contribution > 0 ? "+" : ""}{factor.contribution}
      </span>
    </div>
  );
}

export function FundamentalsPanel({ data, eventDampening }: { data: FundamentalsData | undefined; eventDampening?: boolean }) {
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  return (
    <div className="border-t border-border/50 pt-3">
      {/* Toggle row */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setExpanded((v) => !v);
        }}
        className="flex items-center justify-between w-full group"
      >
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
            Fundamentals
          </span>
          <BiasLabel bias={data.netBias} />
        </div>
        <div className="flex items-center gap-1.5">
          {!expanded && (
            <span className="text-[10px] text-muted-foreground font-mono">
              {eventDampening ? `${Math.min(60, Math.round(data.strength * 0.7))}%` : `${data.strength}%`}
              {eventDampening && <span className="text-red-400/70 ml-0.5">(dampened)</span>}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-3 space-y-2">
          <StrengthBar strength={data.strength} dampened={eventDampening} />

          {/* Factor header */}
          <div className="flex items-center gap-2 pb-1 border-b border-border/30">
            <span className="w-3" />
            <span className="flex-1 text-[9px] text-muted-foreground/60 uppercase tracking-wider">Factor</span>
            <span className="text-[9px] text-muted-foreground/60 uppercase w-4 text-center">W</span>
            <span className="text-[9px] text-muted-foreground/60 uppercase w-6 text-right">Score</span>
          </div>

          {/* Factor rows */}
          {data.factors.map((factor) => (
            <FactorRow key={factor.name} factor={factor} />
          ))}

          {/* Net score summary */}
          <div className="flex items-center justify-between pt-2 border-t border-border/30">
            <span className="text-[10px] text-muted-foreground">
              Net: <span className="font-bold text-foreground">{data.netScore > 0 ? "+" : ""}{data.netScore}</span>
              <span className="text-muted-foreground/50"> / {data.maxPossibleScore}</span>
            </span>
            <span className="text-[9px] text-muted-foreground/50">
              {new Date(data.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
