/**
 * Post-event market reaction tracking — Postgres storage.
 * Captures pre-event prices and post-event deltas at +15m and +1h.
 */

import sql from "./db";
import type { EventReaction } from "./types";

/**
 * Save or update the pre-event price for a symbol.
 */
export async function savePreEventPrice(
  eventId: string,
  eventName: string,
  scheduledAt: string,
  symbol: string,
  prePrice: number,
): Promise<void> {
  await sql`
    INSERT INTO event_reactions (event_id, event_name, scheduled_at, symbol, pre_price)
    VALUES (${eventId}, ${eventName}, ${scheduledAt}, ${symbol}, ${prePrice})
    ON CONFLICT (event_id, symbol) DO UPDATE SET
      pre_price = EXCLUDED.pre_price
  `;
}

/**
 * Update post-event prices and compute deltas.
 */
export async function updatePostEventPrice(
  eventId: string,
  symbol: string,
  price15m: number | null,
  price1h: number | null,
): Promise<void> {
  const rows = await sql`
    SELECT pre_price FROM event_reactions WHERE event_id = ${eventId} AND symbol = ${symbol}
  `;

  if (rows.length === 0 || rows[0].pre_price == null) return;

  const prePrice = rows[0].pre_price as number;

  if (price15m != null) {
    const delta15m = ((price15m - prePrice) / prePrice) * 100;
    await sql`
      UPDATE event_reactions
      SET price_15m = ${price15m}, delta_15m_pct = ${delta15m}, captured_at = NOW()
      WHERE event_id = ${eventId} AND symbol = ${symbol}
    `;
  }

  if (price1h != null) {
    const delta1h = ((price1h - prePrice) / prePrice) * 100;
    await sql`
      UPDATE event_reactions
      SET price_1h = ${price1h}, delta_1h_pct = ${delta1h}, captured_at = NOW()
      WHERE event_id = ${eventId} AND symbol = ${symbol}
    `;
  }
}

/**
 * Get recent event reactions.
 */
export async function getRecentReactions(limit = 50): Promise<EventReaction[]> {
  const rows = await sql`
    SELECT event_id, event_name, scheduled_at, symbol, pre_price, price_15m, price_1h,
           delta_15m_pct, delta_1h_pct, captured_at
    FROM event_reactions
    ORDER BY scheduled_at DESC
    LIMIT ${limit}
  `;

  return rows.map((r) => ({
    eventId: r.event_id,
    eventName: r.event_name,
    scheduledAt: r.scheduled_at,
    symbol: r.symbol,
    prePrice: r.pre_price,
    price15m: r.price_15m,
    price1h: r.price_1h,
    delta15mPct: r.delta_15m_pct,
    delta1hPct: r.delta_1h_pct,
    capturedAt: r.captured_at,
  }));
}
