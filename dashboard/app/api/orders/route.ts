import { NextResponse } from "next/server";
import { fetchTrading } from "@/lib/alpaca";

export async function GET() {
  try {
    const res = await fetchTrading("/orders?status=open&limit=50");
    if (!res.ok) {
      return NextResponse.json({ error: `Alpaca API error: ${res.status}` }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to fetch orders" }, { status: 500 });
  }
}
