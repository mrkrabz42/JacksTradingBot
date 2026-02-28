import { NextRequest, NextResponse } from "next/server";
import { fetchBars } from "@/lib/mss-pipeline";

const TIMEFRAME_MAP: Record<string, string> = {
  "1m": "1Min",
  "5m": "5Min",
  "15m": "15Min",
};

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const symbol = searchParams.get("symbol") || "SPY";
    const timeframe = searchParams.get("timeframe") || "5m";
    const since = searchParams.get("since"); // ISO timestamp

    const tf = TIMEFRAME_MAP[timeframe] || "5Min";
    const now = new Date();
    const start = since || new Date(now.getTime() - 30 * 60000).toISOString(); // last 30 min default

    const bars = await fetchBars(symbol, start, now.toISOString(), tf);

    return NextResponse.json({ bars });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
