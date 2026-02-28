"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { Bar, CP, LiquidityPool, SweepEvent, MSSEvent } from "@/lib/mss-pipeline";

export interface BacktestParams {
  symbol: string;
  start: string;
  end: string;
  timeframe: string;
  sessions?: string[];
}

export interface BacktestMetrics {
  total_bars: number;
  total_mss: number;
  accepted_count: number;
  accepted_pct: number;
  avg_quality: number;
  bull_count: number;
  bear_count: number;
  best_session: string;
  total_sweeps: number;
  total_pools: number;
  atr: number;
}

export interface BacktestResult {
  bars: Bar[];
  swings: CP[];
  liquidity_pools: LiquidityPool[];
  sweep_events: SweepEvent[];
  mss_events: MSSEvent[];
  metrics: BacktestMetrics;
}

export function useBacktest() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [liveBars, setLiveBars] = useState<Bar[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const liveRef = useRef<{ symbol: string; timeframe: string; lastBarTime: string } | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopLive = useCallback(() => {
    setIsLive(false);
    liveRef.current = null;
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const fetchLiveBars = useCallback(async () => {
    if (!liveRef.current) return;
    const { symbol, timeframe, lastBarTime } = liveRef.current;
    try {
      const res = await fetch(
        `/api/backtest/live?symbol=${symbol}&timeframe=${timeframe}&since=${lastBarTime}`
      );
      if (!res.ok) return;
      const json = await res.json();
      if (json.bars && json.bars.length > 0) {
        setLiveBars(json.bars);
        // Update lastBarTime to the latest bar
        liveRef.current.lastBarTime = json.bars[json.bars.length - 1].t;
      }
    } catch {
      // Silently fail live updates
    }
  }, []);

  const run = useCallback(async (params: BacktestParams) => {
    stopLive();
    setIsLoading(true);
    setError(null);
    setData(null);
    setLiveBars([]);

    try {
      const res = await fetch("/api/backtest/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      const json = await res.json();

      if (!res.ok) {
        setError(json.error || `Request failed: ${res.status}`);
        return;
      }

      setData(json);

      // Check if end date is today or future — start live polling
      const endDate = new Date(params.end);
      const today = new Date();
      today.setHours(23, 59, 59, 999);

      if (endDate >= new Date(today.getTime() - 86400000)) {
        const lastBar = json.bars[json.bars.length - 1];
        liveRef.current = {
          symbol: params.symbol,
          timeframe: params.timeframe,
          lastBarTime: lastBar.t,
        };
        setIsLive(true);
        // Poll every 10s for live data
        intervalRef.current = setInterval(fetchLiveBars, 10_000);
        // Fetch once immediately
        fetchLiveBars();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setIsLoading(false);
    }
  }, [stopLive, fetchLiveBars]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { data, liveBars, isLoading, isLive, error, run, stopLive };
}
