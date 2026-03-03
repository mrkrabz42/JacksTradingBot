/**
 * Economic calendar — live data from Forex Factory feed.
 * Free, no API key required. Provides forecast, previous, and actual values.
 */

import type { CalendarEvent } from "./types";

const FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";

// ── Cache ───────────────────────────────────────────────────────────────────

let cachedData: { events: FFEvent[]; fetchedAt: number } | null = null;

// Only fetch once every 15 minutes to stay well within rate limits
const CACHE_TTL = 15 * 60 * 1000;

// If a fetch fails, don't retry for 5 minutes
let rateLimitedUntil = 0;

// ── Raw Forex Factory event shape ───────────────────────────────────────────

interface FFEvent {
  title: string;
  country: string;
  date: string;     // ISO timestamp with offset
  impact: string;   // "High" | "Medium" | "Low" | "Holiday"
  forecast: string; // e.g. "51.7" or "0.3%" or ""
  previous: string; // e.g. "52.6" or ""
}

// ── Fetch from Forex Factory ────────────────────────────────────────────────

async function fetchFFCalendar(): Promise<FFEvent[]> {
  // Return cached data if fresh
  if (cachedData && Date.now() - cachedData.fetchedAt < CACHE_TTL) {
    return cachedData.events;
  }

  // Don't retry if we were recently rate limited
  if (Date.now() < rateLimitedUntil) {
    return cachedData?.events ?? [];
  }

  try {
    const res = await fetch(FF_URL, {
      cache: "no-store",
      headers: { "User-Agent": "EconomicDashboard/1.0" },
    });

    if (res.status === 429) {
      console.warn("FF calendar rate limited, backing off 5 minutes");
      rateLimitedUntil = Date.now() + 5 * 60 * 1000;
      return cachedData?.events ?? [];
    }

    if (!res.ok) {
      console.warn(`FF calendar fetch failed: ${res.status}`);
      return cachedData?.events ?? [];
    }

    const text = await res.text();

    // Guard against HTML error pages (Cloudflare rate limiting)
    if (text.startsWith("<!") || text.startsWith("<html")) {
      console.warn("FF calendar returned HTML (rate limited)");
      rateLimitedUntil = Date.now() + 5 * 60 * 1000;
      return cachedData?.events ?? [];
    }

    const events: FFEvent[] = JSON.parse(text);
    cachedData = { events, fetchedAt: Date.now() };
    return events;
  } catch (err) {
    console.warn("FF calendar fetch error:", err);
    return cachedData?.events ?? [];
  }
}

// ── Map impact levels ───────────────────────────────────────────────────────

function mapImpact(ffImpact: string): "RED" | "AMBER" | null {
  if (ffImpact === "High") return "RED";
  if (ffImpact === "Medium") return "AMBER";
  return null; // Skip Low and Holiday
}

function mapCountry(ffCountry: string): "US" | "UK" | null {
  if (ffCountry === "USD") return "US";
  if (ffCountry === "GBP") return "UK";
  return null;
}

// ── Public API ──────────────────────────────────────────────────────────────

/**
 * Get upcoming and recent US/UK high-impact economic events.
 * Shows all events from the current week (no time windowing — show the full week).
 */
export async function getUpcomingEvents(): Promise<CalendarEvent[]> {
  const allEvents = await fetchFFCalendar();
  const now = new Date();
  const events: CalendarEvent[] = [];

  for (const ff of allEvents) {
    const country = mapCountry(ff.country);
    if (!country) continue;

    const impact = mapImpact(ff.impact);
    if (!impact) continue;

    const scheduledAt = new Date(ff.date);
    if (isNaN(scheduledAt.getTime())) continue;

    const msUntil = scheduledAt.getTime() - now.getTime();

    let status: CalendarEvent["status"];
    if (msUntil < -60_000) {
      status = "released";
    } else if (msUntil <= 15 * 60_000) {
      status = "imminent";
    } else {
      status = "upcoming";
    }

    const id = `${ff.title}-${scheduledAt.toISOString()}`.replace(/[^a-zA-Z0-9-]/g, "_");

    events.push({
      id,
      name: ff.title,
      country,
      impact,
      scheduledAt: scheduledAt.toISOString(),
      forecast: ff.forecast || null,
      previous: ff.previous || null,
      actual: null,
      status,
    });
  }

  // Sort: imminent first, then upcoming (soonest), then released (most recent)
  events.sort((a, b) => {
    const statusOrder = { imminent: 0, upcoming: 1, released: 2 };
    const aDist = statusOrder[a.status];
    const bDist = statusOrder[b.status];
    if (aDist !== bDist) return aDist - bDist;

    if (a.status === "released") {
      return new Date(b.scheduledAt).getTime() - new Date(a.scheduledAt).getTime();
    }
    return new Date(a.scheduledAt).getTime() - new Date(b.scheduledAt).getTime();
  });

  return events;
}
