import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const db = getDb();
    const tradeId = req.nextUrl.searchParams.get("trade_id");

    if (tradeId) {
      const rows = db.prepare("SELECT * FROM user_feedback WHERE trade_id = ? ORDER BY created_at DESC").all(tradeId);
      return NextResponse.json(rows);
    }

    const rows = db.prepare("SELECT * FROM user_feedback ORDER BY created_at DESC").all();
    return NextResponse.json(rows);
  } catch {
    return NextResponse.json({ error: "Failed to fetch feedback" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb();
    const { trade_id, comment, sentiment, tags } = await req.json();

    if (!trade_id) {
      return NextResponse.json({ error: "trade_id is required" }, { status: 400 });
    }

    const stmt = db.prepare(
      "INSERT INTO user_feedback (trade_id, comment, sentiment, tags) VALUES (?, ?, ?, ?)"
    );
    const result = stmt.run(trade_id, comment ?? null, sentiment ?? null, tags ? JSON.stringify(tags) : null);

    return NextResponse.json({ success: true, id: result.lastInsertRowid });
  } catch {
    return NextResponse.json({ error: "Failed to save feedback" }, { status: 500 });
  }
}
