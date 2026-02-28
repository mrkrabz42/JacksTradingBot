import useSWR, { mutate } from "swr";

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Fetch error ${res.status}`);
  }
  return res.json();
};

export interface TradeExplanation {
  id: number;
  trade_id: string;
  strategy_name: string;
  signal_description: string;
  timing_description: string;
  risk_description: string;
  rules_applied: string; // JSON string
  exit_description: string;
  generated_at: string;
}

/** Returns true if the object looks like a real TradeExplanation (not null, not an error) */
function isValidExplanation(obj: unknown): obj is TradeExplanation {
  return (
    obj !== null &&
    typeof obj === "object" &&
    "trade_id" in (obj as Record<string, unknown>) &&
    "signal_description" in (obj as Record<string, unknown>) &&
    !("error" in (obj as Record<string, unknown>))
  );
}

export function useTradeExplanation(tradeId: string | null) {
  const { data, error, isLoading } = useSWR<TradeExplanation | null>(
    tradeId ? `/api/trade-explanations?trade_id=${tradeId}` : null,
    fetcher,
    {
      // Don't auto-retry too aggressively since we generate on-demand
      errorRetryCount: 2,
    }
  );

  // Only return as explanation if it's actually valid (not an error object)
  const explanation = isValidExplanation(data) ? data : null;
  return { explanation, error, isLoading };
}

export function useTradeExplanations() {
  const { data, error, isLoading } = useSWR<TradeExplanation[]>(
    "/api/trade-explanations",
    fetcher
  );
  return { explanations: Array.isArray(data) ? data : [], error, isLoading };
}

// Track in-flight generation requests to prevent duplicate POSTs
const pendingGenerations = new Set<string>();

export async function ensureExplanation(trade: {
  id: string;
  symbol: string;
  side: string;
  qty: string;
  price: string;
  transaction_time: string;
}): Promise<TradeExplanation | null> {
  const swrKey = `/api/trade-explanations?trade_id=${trade.id}`;

  // Prevent duplicate concurrent generation for the same trade
  if (pendingGenerations.has(trade.id)) {
    console.log(`[ensureExplanation] Already generating for ${trade.id}, skipping`);
    return null;
  }

  try {
    // Check if explanation already exists
    const res = await fetch(swrKey);
    if (res.ok) {
      const existing = await res.json();
      if (isValidExplanation(existing)) {
        console.log(`[ensureExplanation] Found existing for ${trade.id}`);
        return existing;
      }
    }

    // Mark as in-flight
    pendingGenerations.add(trade.id);
    console.log(`[ensureExplanation] Generating explanation for ${trade.id} (${trade.symbol} ${trade.side})`);

    // Generate and store
    const postRes = await fetch("/api/trade-explanations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trade),
    });

    if (!postRes.ok) {
      const errBody = await postRes.text();
      console.error(`[ensureExplanation] POST failed (${postRes.status}):`, errBody);
      return null;
    }

    const result = await postRes.json();
    console.log(`[ensureExplanation] POST succeeded for ${trade.id}:`, result);

    // Revalidate the SWR cache so the hook picks up the new explanation
    await mutate(swrKey);

    return null; // SWR will provide the data via the hook
  } catch (err) {
    console.error(`[ensureExplanation] Error for trade ${trade.id}:`, err);
    return null;
  } finally {
    pendingGenerations.delete(trade.id);
  }
}
