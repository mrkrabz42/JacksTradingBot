/**
 * Historical bias logging — stores daily fundamentals snapshots in Postgres.
 */

import sql from "./db";
import type { FundamentalsData } from "./types";

/**
 * Log (or update) a bias snapshot for a symbol on today's date.
 */
export async function logBias(data: FundamentalsData): Promise<void> {
  const today = new Date().toISOString().slice(0, 10);
  await sql`
    INSERT INTO bias_log (symbol, date, net_bias, net_score, strength, factors_json)
    VALUES (${data.symbol}, ${today}, ${data.netBias}, ${data.netScore}, ${data.strength}, ${JSON.stringify(data.factors)})
    ON CONFLICT (symbol, date) DO UPDATE SET
      net_bias = EXCLUDED.net_bias,
      net_score = EXCLUDED.net_score,
      strength = EXCLUDED.strength,
      factors_json = EXCLUDED.factors_json,
      created_at = NOW()
  `;
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
export async function getBiasHistory(symbol: string, days = 30): Promise<BiasHistoryEntry[]> {
  const rows = await sql`
    SELECT symbol, date, net_bias, net_score, strength, factors_json
    FROM bias_log
    WHERE symbol = ${symbol}
    ORDER BY date DESC
    LIMIT ${days}
  `;

  return rows.map((row) => ({
    symbol: row.symbol,
    date: row.date,
    netBias: row.net_bias,
    netScore: row.net_score,
    strength: row.strength,
    factors: JSON.parse(row.factors_json),
  }));
}
