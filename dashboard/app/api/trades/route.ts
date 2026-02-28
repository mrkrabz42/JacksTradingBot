import { NextResponse } from "next/server";
import { fetchTrading } from "@/lib/alpaca";
import { MOCK_TRADES } from "@/lib/mock-trades";

export async function GET() {
  try {
    // 3-second timeout so the page doesn't hang waiting for Alpaca
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    const res = await fetchTrading(
      "/account/activities/FILL?page_size=20&direction=desc",
      controller.signal
    );
    clearTimeout(timeout);

    if (!res.ok) {
      return NextResponse.json(MOCK_TRADES);
    }
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      return NextResponse.json(data);
    }
    return NextResponse.json(MOCK_TRADES);
  } catch {
    return NextResponse.json(MOCK_TRADES);
  }
}
