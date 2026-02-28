import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";

export async function POST(req: NextRequest) {
  try {
    const { input } = await req.json();

    if (!input || typeof input !== "string") {
      return NextResponse.json({ error: "input string required" }, { status: 400 });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      // Fallback: simple parsing without AI
      return NextResponse.json({
        rule_name: input.slice(0, 50),
        rule_description: input,
        rule_type: "filter",
      });
    }

    const client = new Anthropic({ apiKey });
    const message = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 256,
      messages: [
        {
          role: "user",
          content: `Parse this trading rule into a JSON object with these fields:
- rule_name: short name (max 50 chars)
- rule_description: clear description of what the rule does
- rule_type: one of "filter", "entry", "exit", or "risk"

Trading rule: "${input}"

Respond with ONLY valid JSON, no markdown.`,
        },
      ],
    });

    const text = message.content[0].type === "text" ? message.content[0].text : "";
    const parsed = JSON.parse(text);

    return NextResponse.json({
      rule_name: parsed.rule_name ?? input.slice(0, 50),
      rule_description: parsed.rule_description ?? input,
      rule_type: parsed.rule_type ?? "filter",
    });
  } catch {
    return NextResponse.json({ error: "Failed to parse rule" }, { status: 500 });
  }
}
