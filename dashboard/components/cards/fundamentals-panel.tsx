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

function StrengthBar({ strength }: { strength: number }) {
  const color =
    strength >= 65 ? "bg-emerald-500" :
    strength >= 40 ? "bg-zinc-400" :
    "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${strength}%` }}
        />
      </div>
      <span className="text-[10px] text-muted-foreground font-mono w-7 text-right">{strength}%</span>
    </div>
  );
}

function DirectionIcon({ direction }: { direction: 1 | 0 | -1 }) {
  if (direction === 1) return <ArrowUpRight className="h-3 w-3 text-emerald-400" />;
  if (direction === -1) return <ArrowDownRight className="h-3 w-3 text-red-400" />;
  return <Minus className="h-3 w-3 text-zinc-500" />;
}

function FactorRow({ factor }: { factor: FundamentalFactor }) {
  const contribColor =
    factor.contribution > 0 ? "text-emerald-400" :
    factor.contribution < 0 ? "text-red-400" :
    "text-zinc-500";

  return (
    <div className="flex items-center gap-2 py-1">
      <DirectionIcon direction={factor.direction} />
      <span className="flex-1 text-[11px] text-zinc-300 truncate">{factor.name}</span>
      <span className="text-[10px] text-muted-foreground font-mono w-4 text-center">{factor.weight}</span>
      <span className={cn("text-[11px] font-bold font-mono w-6 text-right", contribColor)}>
        {factor.contribution > 0 ? "+" : ""}{factor.contribution}
      </span>
    </div>
  );
}

export function FundamentalsPanel({ data }: { data: FundamentalsData | undefined }) {
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
            <span className="text-[10px] text-muted-foreground font-mono">{data.strength}%</span>
          )}
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5 text-muted-foreground group-hover:text-white transition-colors" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground group-hover:text-white transition-colors" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-3 space-y-2">
          <StrengthBar strength={data.strength} />

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
              Net: <span className="font-bold text-white">{data.netScore > 0 ? "+" : ""}{data.netScore}</span>
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
