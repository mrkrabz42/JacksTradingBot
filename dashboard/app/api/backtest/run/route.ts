import { NextRequest, NextResponse } from "next/server";
import {
  fetchBars,
  computeATR,
  identifyControlPoints,
  detectMSS,
  computeDailyExtremes,
  findLiquidityPools,
  detectSweeps,
} from "@/lib/mss-pipeline";

const TIMEFRAME_MAP: Record<string, string> = {
  "1m": "1Min",
  "5m": "5Min",
  "15m": "15Min",
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { symbol, start, end, timeframe = "5m", sessions } = body as {
      symbol: string;
      start: string;
      end: string;
      timeframe?: string;
      sessions?: string[];
    };

    if (!symbol || !start || !end) {
      return NextResponse.json({ error: "symbol, start, end are required" }, { status: 400 });
    }

    const tf = TIMEFRAME_MAP[timeframe] || "5Min";

    // Fetch bars for the full range
    const allBars = await fetchBars(symbol, start, end, tf);
    if (allBars.length === 0) {
      return NextResponse.json({ error: "No bars returned for the given range" }, { status: 404 });
    }

    // Fetch previous day bars for PDH/PDL
    const firstBarDate = new Date(allBars[0].t);
    const dayBefore = new Date(firstBarDate.getTime() - 2 * 86400000);
    const dayBeforeEnd = new Date(firstBarDate.getTime());
    let prevBars = await fetchBars(symbol, dayBefore.toISOString(), dayBeforeEnd.toISOString(), tf);
    // Filter to only the last trading day
    if (prevBars.length > 0) {
      const lastDate = new Date(prevBars[prevBars.length - 1].t).toISOString().slice(0, 10);
      prevBars = prevBars.filter(b => new Date(b.t).toISOString().slice(0, 10) === lastDate);
    }
    const daily = computeDailyExtremes(prevBars);

    // Pipeline
    const atr = computeATR(allBars);
    const cps = identifyControlPoints(allBars);
    const pools = findLiquidityPools(cps);
    const sweeps = detectSweeps(allBars, pools, atr);
    let mssEvents = detectMSS(allBars, cps, atr, daily.pdh, daily.pdl);

    // Filter by session if provided
    if (sessions && sessions.length > 0) {
      mssEvents = mssEvents.filter(e => sessions.includes(e.session));
    }

    // Compute metrics
    const accepted = mssEvents.filter(e => e.is_accepted);
    const bullCount = mssEvents.filter(e => e.direction === "BULL").length;
    const bearCount = mssEvents.filter(e => e.direction === "BEAR").length;
    const qualities = mssEvents.map(e => e.displacement_quality);
    const avgQuality = qualities.length
      ? Math.round(qualities.reduce((a, b) => a + b, 0) / qualities.length * 1000) / 1000
      : 0;

    // Best session
    const sessionCounts: Record<string, number> = {};
    for (const e of mssEvents) {
      sessionCounts[e.session] = (sessionCounts[e.session] || 0) + 1;
    }
    const bestSession = Object.entries(sessionCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";

    return NextResponse.json({
      bars: allBars,
      swings: cps,
      liquidity_pools: pools,
      sweep_events: sweeps,
      mss_events: mssEvents,
      metrics: {
        total_bars: allBars.length,
        total_mss: mssEvents.length,
        accepted_count: accepted.length,
        accepted_pct: mssEvents.length ? Math.round(accepted.length / mssEvents.length * 100) : 0,
        avg_quality: avgQuality,
        bull_count: bullCount,
        bear_count: bearCount,
        best_session: bestSession,
        total_sweeps: sweeps.length,
        total_pools: pools.length,
        atr: Math.round(atr * 10000) / 10000,
      },
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: `Backtest failed: ${message}` }, { status: 500 });
  }
}
