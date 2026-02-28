import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const db = getDb();
    const body = await req.json();
    const id = params.id;

    if (typeof body.enabled === "number" || typeof body.enabled === "boolean") {
      db.prepare("UPDATE strategy_rules SET enabled = ? WHERE id = ?").run(body.enabled ? 1 : 0, id);
    }
    if (body.rule_name) {
      db.prepare("UPDATE strategy_rules SET rule_name = ? WHERE id = ?").run(body.rule_name, id);
    }
    if (body.rule_description) {
      db.prepare("UPDATE strategy_rules SET rule_description = ? WHERE id = ?").run(body.rule_description, id);
    }

    const updated = db.prepare("SELECT * FROM strategy_rules WHERE id = ?").get(id);
    return NextResponse.json(updated);
  } catch {
    return NextResponse.json({ error: "Failed to update rule" }, { status: 500 });
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const db = getDb();
    db.prepare("DELETE FROM strategy_rules WHERE id = ?").run(params.id);
    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Failed to delete rule" }, { status: 500 });
  }
}
