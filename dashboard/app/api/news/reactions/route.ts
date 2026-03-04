import { NextRequest, NextResponse } from "next/server";
import { savePreEventPrice, updatePostEventPrice, getRecentReactions } from "@/lib/event-reactions";
import { fetchPrices } from "@/lib/oanda";
import { INSTRUMENTS } from "@/lib/constants";

export const dynamic = "force-dynamic";

// In-memory tracker: which events we've already captured pre-prices for
const capturedEvents = new Map<string, { scheduledAt: number; captured15m: boolean; captured1h: boolean }>();

/**
 * GET /api/news/reactions?action=capture&events=JSON
 *   action=capture — triggers price snapshots for imminent/released events
 *   (no action)    — returns recent reactions
 *
 * Events param is a JSON array of { id, name, scheduledAt, status, impact }
 */
export async function GET(req: NextRequest) {
  try {
    const action = req.nextUrl.searchParams.get("action");

    if (action === "capture") {
      const eventsJson = req.nextUrl.searchParams.get("events");
      if (!eventsJson) {
        return NextResponse.json({ captured: 0 });
      }

      const events = JSON.parse(eventsJson) as {
        id: string;
        name: string;
        scheduledAt: string;
        status: string;
        impact: string;
      }[];

      const now = Date.now();
      const symbols = INSTRUMENTS.map((i) => i.symbol);
      let prices: Record<string, number> | null = null;

      let captured = 0;

      for (const event of events) {
        if (event.impact !== "RED") continue;
        const eventTime = new Date(event.scheduledAt).getTime();
        const tracker = capturedEvents.get(event.id);

        // Pre-event capture: within 15 min before event
        if (!tracker && eventTime - now < 15 * 60 * 1000 && eventTime - now > 0) {
          if (!prices) prices = await fetchPrices(symbols);
          for (const sym of symbols) {
            if (prices[sym] != null) {
              await savePreEventPrice(event.id, event.name, event.scheduledAt, sym, prices[sym]);
            }
          }
          capturedEvents.set(event.id, { scheduledAt: eventTime, captured15m: false, captured1h: false });
          captured++;
        }

        // Post-event +15m capture
        if (tracker && !tracker.captured15m && now - eventTime >= 15 * 60 * 1000 && now - eventTime < 20 * 60 * 1000) {
          if (!prices) prices = await fetchPrices(symbols);
          for (const sym of symbols) {
            if (prices[sym] != null) {
              await updatePostEventPrice(event.id, sym, prices[sym], null);
            }
          }
          tracker.captured15m = true;
          captured++;
        }

        // Post-event +1h capture
        if (tracker && !tracker.captured1h && now - eventTime >= 60 * 60 * 1000 && now - eventTime < 65 * 60 * 1000) {
          if (!prices) prices = await fetchPrices(symbols);
          for (const sym of symbols) {
            if (prices[sym] != null) {
              await updatePostEventPrice(event.id, sym, null, prices[sym]);
            }
          }
          tracker.captured1h = true;
          captured++;
        }
      }

      return NextResponse.json({ captured });
    }

    // Default: return recent reactions
    const reactions = await getRecentReactions();
    return NextResponse.json(reactions);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Event reactions API error:", message);
    return NextResponse.json(
      { error: "Failed to process event reactions", detail: message },
      { status: 500 },
    );
  }
}
