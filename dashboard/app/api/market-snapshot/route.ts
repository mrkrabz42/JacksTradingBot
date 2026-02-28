import { NextResponse } from "next/server";
import { fetchData } from "@/lib/alpaca";
import { INDEX_SYMBOLS } from "@/lib/constants";

export async function GET() {
  try {
    const symbols = INDEX_SYMBOLS.join(",");
    const res = await fetchData(`/stocks/quotes/latest?symbols=${symbols}&feed=iex`);
    if (!res.ok) {
      return NextResponse.json({ error: `Alpaca API error: ${res.status}` }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to fetch market snapshot" }, { status: 500 });
  }
}
