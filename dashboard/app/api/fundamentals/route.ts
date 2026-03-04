import { NextRequest, NextResponse } from "next/server";
import { fetchAllFredData } from "@/lib/fred";
import { scoreFundamentals, type DxyPriceData, type CommodityPriceData } from "@/lib/fundamentals-engine";
import { fetchPrices, fetchCandles } from "@/lib/oanda";
import { INSTRUMENTS } from "@/lib/constants";
import type { FundamentalsData } from "@/lib/types";
import { logBias } from "@/lib/bias-history";

export const dynamic = "force-dynamic";

// Module-level cache for previous results (trend arrows)
const previousResults = new Map<string, FundamentalsData>();

/**
 * Compute simple moving average from daily candle closes.
 */
function smaFromCandles(candles: { c: number }[]): number | null {
  if (candles.length === 0) return null;
  const sum = candles.reduce((s, bar) => s + bar.c, 0);
  return sum / candles.length;
}

/**
 * GET /api/fundamentals?symbol=XAU_USD
 * Returns fundamentals scoring for one or all instruments.
 */
export async function GET(req: NextRequest) {
  try {
    const symbol = req.nextUrl.searchParams.get("symbol");

    const now = new Date();
    const twoDaysAgo = new Date(now.getTime() - 2 * 86400000);
    const twentyFiveDaysAgo = new Date(now.getTime() - 25 * 86400000);

    // Fetch FRED data, EUR/USD price, and commodity prices all in parallel
    const [fredData, eurPrices, commodityPrices, eurBarsResult, xauBarsResult, xagBarsResult] = await Promise.all([
      fetchAllFredData(),
      fetchPrices(["EUR_USD"]),
      fetchPrices(["XAU_USD", "XAG_USD"]),
      fetchCandles("EUR_USD", twoDaysAgo.toISOString(), now.toISOString(), "1Day").catch(() => [] as { c: number; o: number }[]),
      fetchCandles("XAU_USD", twentyFiveDaysAgo.toISOString(), now.toISOString(), "1Day").catch(() => [] as { c: number }[]),
      fetchCandles("XAG_USD", twentyFiveDaysAgo.toISOString(), now.toISOString(), "1Day").catch(() => [] as { c: number }[]),
    ]);

    // Previous EUR/USD close for DXY direction comparison
    let prevEurUsd: number | null = null;
    if (eurBarsResult.length >= 2) {
      prevEurUsd = eurBarsResult[eurBarsResult.length - 2].c;
    } else if (eurBarsResult.length === 1) {
      prevEurUsd = eurBarsResult[0].o;
    }

    const dxy: DxyPriceData = {
      current: eurPrices["EUR_USD"] ?? null,
      previous: prevEurUsd,
    };

    // Build commodity price data from OANDA candles
    const commodity: CommodityPriceData = {
      xauCurrent: commodityPrices["XAU_USD"] ?? null,
      xauSma5d: xauBarsResult.length >= 5 ? smaFromCandles(xauBarsResult.slice(-5)) : null,
      xauSma20d: xauBarsResult.length >= 20 ? smaFromCandles(xauBarsResult.slice(-20)) : null,
      xagCurrent: commodityPrices["XAG_USD"] ?? null,
      xagSma5d: xagBarsResult.length >= 5 ? smaFromCandles(xagBarsResult.slice(-5)) : null,
      xagSma20d: xagBarsResult.length >= 20 ? smaFromCandles(xagBarsResult.slice(-20)) : null,
    };

    // Score instruments
    const symbols = symbol
      ? [symbol]
      : INSTRUMENTS.map((i) => i.symbol);

    const results: FundamentalsData[] = [];
    for (const sym of symbols) {
      try {
        const prev = previousResults.get(sym);
        const result = scoreFundamentals(sym, fredData, dxy, commodity, prev?.factors);
        results.push(result);

        // Cache current result for next cycle's trend arrows
        previousResults.set(sym, result);

        // Log bias to SQLite (non-critical)
        try {
          await logBias(result);
        } catch {
          // Bias logging is non-critical
        }
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
