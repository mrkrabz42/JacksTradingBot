import { NextRequest, NextResponse } from "next/server";
import { fetchData } from "@/lib/alpaca";

export async function GET(req: NextRequest) {
  try {
    const symbol = req.nextUrl.searchParams.get("symbol") || "SPY";
    const timeframe = req.nextUrl.searchParams.get("timeframe") || "5Min";
    const days = parseInt(req.nextUrl.searchParams.get("days") || "5", 10);

    const now = new Date();
    const start = new Date(now.getTime() - days * 86400000);

    // Skip weekends for start date
    while (start.getUTCDay() === 0 || start.getUTCDay() === 6) {
      start.setTime(start.getTime() - 86400000);
    }

    const allBars: { t: string; o: number; h: number; l: number; c: number; v: number }[] = [];
    let pageToken: string | null = null;

    do {
      let url = `/stocks/${symbol}/bars?timeframe=${timeframe}&start=${start.toISOString()}&end=${now.toISOString()}&feed=iex&limit=10000`;
      if (pageToken) url += `&page_token=${pageToken}`;
      const res = await fetchData(url);
      if (!res.ok) throw new Error(`Alpaca bars error: ${res.status}`);
      const data = await res.json();
      if (data.bars) allBars.push(...data.bars);
      pageToken = data.next_page_token || null;
    } while (pageToken);

    // Latest quote for live price line
    const quoteRes = await fetchData(`/stocks/${symbol}/quotes/latest?feed=iex`);
    let livePrice = 0;
    if (quoteRes.ok) {
      const q = await quoteRes.json();
      if (q.quote) livePrice = q.quote.ap || q.quote.bp || 0;
    }

    return NextResponse.json({
      symbol,
      timeframe,
      bars: allBars,
      livePrice,
      count: allBars.length,
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: `Market bars failed: ${message}` }, { status: 500 });
  }
}
