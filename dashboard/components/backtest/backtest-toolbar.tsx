"use client";

import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import type { BacktestParams } from "@/lib/hooks/use-backtest";

interface BacktestToolbarProps {
  onRun: (params: BacktestParams) => void;
  isLoading: boolean;
}

const TIMEFRAMES = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
];

const SESSION_OPTIONS = ["ASIA", "LONDON", "NY"] as const;

function getDefaultDates() {
  const end = new Date();
  const start = new Date(end.getTime() - 5 * 86400000);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export function BacktestToolbar({ onRun, isLoading }: BacktestToolbarProps) {
  const defaults = getDefaultDates();
  const [symbol, setSymbol] = useState("SPY");
  const [startDate, setStartDate] = useState(defaults.start);
  const [endDate, setEndDate] = useState(defaults.end);
  const [timeframe, setTimeframe] = useState("5m");
  const [sessions, setSessions] = useState<string[]>([]);

  const toggleSession = (s: string) => {
    setSessions(prev =>
      prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
    );
  };

  const handleRun = () => {
    onRun({
      symbol: symbol.toUpperCase().trim(),
      start: new Date(startDate).toISOString(),
      end: new Date(endDate + "T23:59:59Z").toISOString(),
      timeframe,
      sessions: sessions.length > 0 ? sessions : undefined,
    });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-card border border-border rounded-xl">
      {/* Symbol */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase text-muted-foreground font-medium">Symbol</label>
        <input
          type="text"
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          className="w-20 px-2 py-1.5 bg-background border border-border rounded-md text-sm text-white focus:outline-none focus:border-pink"
        />
      </div>

      {/* Date range */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase text-muted-foreground font-medium">Start</label>
        <input
          type="date"
          value={startDate}
          onChange={e => setStartDate(e.target.value)}
          className="px-2 py-1.5 bg-background border border-border rounded-md text-sm text-white focus:outline-none focus:border-pink [color-scheme:dark]"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase text-muted-foreground font-medium">End</label>
        <input
          type="date"
          value={endDate}
          onChange={e => setEndDate(e.target.value)}
          className="px-2 py-1.5 bg-background border border-border rounded-md text-sm text-white focus:outline-none focus:border-pink [color-scheme:dark]"
        />
      </div>

      {/* Timeframe */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase text-muted-foreground font-medium">Timeframe</label>
        <div className="flex gap-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                timeframe === tf.value
                  ? "bg-pink text-white"
                  : "bg-background border border-border text-muted-foreground hover:text-white"
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Session chips */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase text-muted-foreground font-medium">Sessions</label>
        <div className="flex gap-1">
          {SESSION_OPTIONS.map(s => (
            <button
              key={s}
              onClick={() => toggleSession(s)}
              className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                sessions.includes(s)
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                  : "bg-background border border-border text-muted-foreground hover:text-white"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Run button */}
      <div className="flex flex-col gap-1 ml-auto">
        <label className="text-[10px] invisible">Run</label>
        <button
          onClick={handleRun}
          disabled={isLoading || !symbol.trim()}
          className="flex items-center gap-2 px-4 py-1.5 bg-pink hover:bg-pink/90 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isLoading ? "Running..." : "Run Backtest"}
        </button>
      </div>
    </div>
  );
}
