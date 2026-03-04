import { NextRequest, NextResponse } from "next/server";
import { getBiasHistory } from "@/lib/bias-history";

export const dynamic = "force-dynamic";

/**
 * GET /api/fundamentals/history?symbol=XAU_USD&days=30
 * Returns historical bias log entries for a symbol.
 */
export async function GET(req: NextRequest) {
  try {
    const symbol = req.nextUrl.searchParams.get("symbol");
    const daysParam = req.nextUrl.searchParams.get("days");
    const days = daysParam ? parseInt(daysParam, 10) : 30;

    if (!symbol) {
      return NextResponse.json(
        { error: "Missing required 'symbol' parameter" },
        { status: 400 },
      );
    }

    const history = await getBiasHistory(symbol, days);
    return NextResponse.json(history);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Bias history API error:", message);
    return NextResponse.json(
      { error: "Failed to fetch bias history", detail: message },
      { status: 500 },
    );
  }
}
