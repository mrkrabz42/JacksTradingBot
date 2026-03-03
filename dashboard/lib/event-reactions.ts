/**
 * Post-event market reaction tracking — SQLite storage.
 * Captures pre-event prices and post-event deltas at +15m and +1h.
 */

import Database from "better-sqlite3";
import path from "path";
import type { EventReaction } from "./types";

const DB_PATH = path.join(process.cwd(), "data", "bias-history.sqlite");

let db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.exec(`
      CREATE TABLE IF NOT EXISTS event_reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        event_name TEXT NOT NULL,
        scheduled_at TEXT NOT NULL,
        symbol TEXT NOT NULL,
        pre_price REAL,
        price_15m REAL,
        price_1h REAL,
        delta_15m_pct REAL,
        delta_1h_pct REAL,
        captured_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(event_id, symbol)
      )
    `);
  }
  return db;
}

/**
 * Save or update the pre-event price for a symbol.
 */
export function savePreEventPrice(
  eventId: string,
  eventName: string,
  scheduledAt: string,
  symbol: string,
  prePrice: number,
): void {
  const database = getDb();
  database.prepare(`
    INSERT INTO event_reactions (event_id, event_name, scheduled_at, symbol, pre_price)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(event_id, symbol) DO UPDATE SET
      pre_price = excluded.pre_price
  `).run(eventId, eventName, scheduledAt, symbol, prePrice);
}

/**
 * Update post-event prices and compute deltas.
 */
export function updatePostEventPrice(
  eventId: string,
  symbol: string,
  price15m: number | null,
  price1h: number | null,
): void {
  const database = getDb();
  const row = database.prepare(
    `SELECT pre_price FROM event_reactions WHERE event_id = ? AND symbol = ?`,
  ).get(eventId, symbol) as { pre_price: number | null } | undefined;

  if (!row || row.pre_price == null) return;

  const prePrice = row.pre_price;
  const delta15m = price15m != null ? ((price15m - prePrice) / prePrice) * 100 : null;
  const delta1h = price1h != null ? ((price1h - prePrice) / prePrice) * 100 : null;

  const updates: string[] = [];
  const params: (number | null)[] = [];

  if (price15m != null) {
    updates.push("price_15m = ?", "delta_15m_pct = ?");
    params.push(price15m, delta15m);
  }
  if (price1h != null) {
    updates.push("price_1h = ?", "delta_1h_pct = ?");
    params.push(price1h, delta1h);
  }

  if (updates.length === 0) return;

  database.prepare(
    `UPDATE event_reactions SET ${updates.join(", ")}, captured_at = datetime('now') WHERE event_id = ? AND symbol = ?`,
  ).run(...params, eventId, symbol);
}

/**
 * Get recent event reactions.
 */
export function getRecentReactions(limit = 50): EventReaction[] {
  const database = getDb();
  const rows = database.prepare(`
    SELECT event_id, event_name, scheduled_at, symbol, pre_price, price_15m, price_1h,
           delta_15m_pct, delta_1h_pct, captured_at
    FROM event_reactions
    ORDER BY scheduled_at DESC
    LIMIT ?
  `).all(limit) as {
    event_id: string;
    event_name: string;
    scheduled_at: string;
    symbol: string;
    pre_price: number | null;
    price_15m: number | null;
    price_1h: number | null;
    delta_15m_pct: number | null;
    delta_1h_pct: number | null;
    captured_at: string;
  }[];

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
