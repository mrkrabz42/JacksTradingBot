/**
 * Historical bias logging — stores daily fundamentals snapshots in SQLite.
 */

import Database from "better-sqlite3";
import path from "path";
import type { FundamentalsData } from "./types";

const DB_PATH = path.join(process.cwd(), "data", "bias-history.sqlite");

let db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.exec(`
      CREATE TABLE IF NOT EXISTS bias_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        date TEXT NOT NULL,
        net_bias TEXT NOT NULL,
        net_score INTEGER NOT NULL,
        strength INTEGER NOT NULL,
        factors_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(symbol, date)
      )
    `);
  }
  return db;
}

/**
 * Log (or update) a bias snapshot for a symbol on today's date.
 */
export function logBias(data: FundamentalsData): void {
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const database = getDb();
  const stmt = database.prepare(`
    INSERT INTO bias_log (symbol, date, net_bias, net_score, strength, factors_json)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(symbol, date) DO UPDATE SET
      net_bias = excluded.net_bias,
      net_score = excluded.net_score,
      strength = excluded.strength,
      factors_json = excluded.factors_json,
      created_at = datetime('now')
  `);
  stmt.run(
    data.symbol,
    today,
    data.netBias,
    data.netScore,
    data.strength,
    JSON.stringify(data.factors),
  );
}

export interface BiasHistoryEntry {
  symbol: string;
  date: string;
  netBias: string;
  netScore: number;
  strength: number;
  factors: FundamentalsData["factors"];
}

/**
 * Get recent bias history for a symbol.
 */
export function getBiasHistory(symbol: string, days = 30): BiasHistoryEntry[] {
  const database = getDb();
  const rows = database.prepare(`
    SELECT symbol, date, net_bias, net_score, strength, factors_json
    FROM bias_log
    WHERE symbol = ?
    ORDER BY date DESC
    LIMIT ?
  `).all(symbol, days) as {
    symbol: string;
    date: string;
    net_bias: string;
    net_score: number;
    strength: number;
    factors_json: string;
  }[];

  return rows.map((row) => ({
    symbol: row.symbol,
    date: row.date,
    netBias: row.net_bias,
    netScore: row.net_score,
    strength: row.strength,
    factors: JSON.parse(row.factors_json),
  }));
}
