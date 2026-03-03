import { NextResponse } from "next/server";
import { getUpcomingEvents } from "@/lib/economic-calendar";

export const dynamic = "force-dynamic";

/**
 * GET /api/news/calendar
 * Returns upcoming (next 48h) and recent (past 24h) high-impact economic events.
 */
export async function GET() {
  try {
    const events = await getUpcomingEvents();
    return NextResponse.json(events);
  } catch (error) {
    console.error("News calendar API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch calendar events" },
      { status: 500 },
    );
  }
}
