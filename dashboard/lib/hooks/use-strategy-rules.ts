import useSWR, { mutate } from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export interface StrategyRule {
  id: number;
  rule_name: string;
  rule_description: string;
  rule_type: "filter" | "entry" | "exit" | "risk";
  enabled: number; // 0 or 1
  created_by: string;
  backtest_result: string | null;
  created_at: string;
}

export function useStrategyRules() {
  const { data, error, isLoading } = useSWR<StrategyRule[]>(
    "/api/strategy-rules",
    fetcher
  );
  return { rules: Array.isArray(data) ? data : [], error, isLoading };
}

export async function toggleRule(id: number, enabled: boolean) {
  await fetch(`/api/strategy-rules/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  mutate("/api/strategy-rules");
}

export async function addRule(ruleName: string, ruleDescription: string, ruleType: string) {
  await fetch("/api/strategy-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      rule_name: ruleName,
      rule_description: ruleDescription,
      rule_type: ruleType,
      created_by: "user",
    }),
  });
  mutate("/api/strategy-rules");
}

export async function deleteRule(id: number) {
  await fetch(`/api/strategy-rules/${id}`, { method: "DELETE" });
  mutate("/api/strategy-rules");
}

export async function parseRuleWithAI(input: string): Promise<{
  rule_name: string;
  rule_description: string;
  rule_type: string;
}> {
  const res = await fetch("/api/parse-rule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });
  return res.json();
}
