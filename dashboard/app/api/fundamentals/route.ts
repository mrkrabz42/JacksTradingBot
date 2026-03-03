import { NextRequest, NextResponse } from "next/server";
import { fetchAllFredData } from "@/lib/fred";
import { scoreFundamentals, type DxyPriceData } from "@/lib/fundamentals-engine";
import { fetchPrices, fetchCandles } from "@/lib/oanda";
import { INSTRUMENTS } from "@/lib/constants";
import type { FundamentalsData } from "@/lib/types";

export const dynamic = "force-dynamic";

/**
 * GET /api/fundamentals?symbol=XAU_USD
 * Returns fundamentals scoring for one or all instruments.
 */
export async function GET(req: NextRequest) {
  try {
    const symbol = req.nextUrl.searchParams.get("symbol");

    // Fetch FRED data and EUR/USD price (for DXY proxy) in parallel
    const [fredData, eurPrices] = await Promise.all([
      fetchAllFredData(),
      fetchPrices(["EUR_USD"]),
    ]);

    // Get previous EUR/USD close for DXY direction comparison
    // Fetch yesterday's daily candle for EUR/USD
    const now = new Date();
    const twoDaysAgo = new Date(now.getTime() - 2 * 86400000);
    let prevEurUsd: number | null = null;

    try {
      const eurBars = await fetchCandles(
        "EUR_USD",
        twoDaysAgo.toISOString(),
        now.toISOString(),
        "1Day",
      );
      if (eurBars.length >= 2) {
        prevEurUsd = eurBars[eurBars.length - 2].c;
      } else if (eurBars.length === 1) {
        prevEurUsd = eurBars[0].o;
      }
    } catch {
      // Fall back to null — DXY factor will score neutral
    }

    const dxy: DxyPriceData = {
      current: eurPrices["EUR_USD"] ?? null,
      previous: prevEurUsd,
    };

    // Score instruments
    const symbols = symbol
      ? [symbol]
      : INSTRUMENTS.map((i) => i.symbol);

    const results: FundamentalsData[] = [];
    for (const sym of symbols) {
      try {
        results.push(scoreFundamentals(sym, fredData, dxy));
      } catch {
        // Skip instruments without config
      }
    }

    if (symbol && results.length === 1) {
      return NextResponse.json(results[0]);
    }

    return NextResponse.json(results);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Fundamentals API error:", message);
    return NextResponse.json(
      { error: "Failed to fetch fundamentals data", detail: message },
      { status: 500 },
    );
  }
}
