import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET() {
  try {
    const db = getDb();
    const rows = db.prepare("SELECT * FROM strategy_rules ORDER BY created_at ASC").all();
    return NextResponse.json(rows);
  } catch {
    return NextResponse.json({ error: "Failed to fetch rules" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb();
    const { rule_name, rule_description, rule_type, created_by } = await req.json();

    if (!rule_name || !rule_description) {
      return NextResponse.json({ error: "rule_name and rule_description required" }, { status: 400 });
    }

    const stmt = db.prepare(
      "INSERT INTO strategy_rules (rule_name, rule_description, rule_type, enabled, created_by) VALUES (?, ?, ?, 1, ?)"
    );
    const result = stmt.run(
      rule_name,
      rule_description,
      rule_type ?? "filter",
      created_by ?? "user"
    );

    return NextResponse.json({ success: true, id: result.lastInsertRowid });
  } catch {
    return NextResponse.json({ error: "Failed to create rule" }, { status: 500 });
  }
}
