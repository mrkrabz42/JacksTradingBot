import { NextRequest, NextResponse } from "next/server";
import { getDb, generateBasicExplanation } from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const db = getDb();
    const tradeId = req.nextUrl.searchParams.get("trade_id");

    if (tradeId) {
      const row = db.prepare("SELECT * FROM trade_explanations WHERE trade_id = ?").get(tradeId);
      return NextResponse.json(row ?? null);
    }

    const rows = db.prepare("SELECT * FROM trade_explanations ORDER BY generated_at DESC").all();
    return NextResponse.json(rows);
  } catch (err) {
    console.error("[trade-explanations GET] Error:", err);
    return NextResponse.json({ error: "Failed to fetch explanations" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb();
    const body = await req.json();

    // Accept either a full explanation or a trade object to auto-generate from.
    // Trade objects from Alpaca use "id" (not "trade_id"), so check both.
    const tradeId = body.trade_id || body.id;
    const isRawTrade = tradeId && !body.signal_description;

    if (!tradeId) {
      return NextResponse.json(
        { error: "Missing trade_id or id in request body" },
        { status: 400 }
      );
    }

    const explanation = isRawTrade
      ? generateBasicExplanation({ ...body, id: tradeId })
      : body;

    const stmt = db.prepare(`
      INSERT OR REPLACE INTO trade_explanations
      (trade_id, strategy_name, signal_description, timing_description, risk_description, rules_applied, exit_description)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      explanation.trade_id ?? tradeId,
      explanation.strategy_name,
      explanation.signal_description,
      explanation.timing_description,
      explanation.risk_description,
      explanation.rules_applied,
      explanation.exit_description
    );

    return NextResponse.json({ success: true, trade_id: tradeId });
  } catch (err) {
    console.error("[trade-explanations POST] Error:", err);
    return NextResponse.json({ error: "Failed to save explanation" }, { status: 500 });
  }
}
