import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

const DB_PATH = path.resolve(process.cwd(), "..", "trade_journal.sqlite");

export async function GET() {
  try {
    if (!fs.existsSync(DB_PATH)) {
      return NextResponse.json({ scores: [], message: "No trade journal found — bot has not recorded any trades yet." });
    }

    const db = new Database(DB_PATH, { readonly: true });

    // Check if strategy_scores table exists
    const tableCheck = db.prepare(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_scores'"
    ).get();

    if (!tableCheck) {
      db.close();
      return NextResponse.json({ scores: [], message: "No strategy scores yet — waiting for closed trades." });
    }

    const rows = db.prepare(
      "SELECT strategy_name, regime, win_rate, avg_pnl_pct, profit_factor, avg_r_multiple, trade_count, composite_score, kelly_fraction, updated_at FROM strategy_scores ORDER BY composite_score DESC"
    ).all();

    db.close();

    return NextResponse.json({ scores: rows });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
