"use client";

import { useState, useEffect } from "react";
import { useTimezone } from "@/lib/context/timezone-context";
import { getMarketStatus } from "@/lib/market-utils";
import type { MarketStatusResult } from "@/lib/types";

export function MarketStatusIndicator() {
  const { selected } = useTimezone();
  const [result, setResult] = useState<MarketStatusResult | null>(null);

  useEffect(() => {
    const update = () => setResult(getMarketStatus(new Date(), selected.key));
    update();
    const interval = setInterval(update, 10_000);
    return () => clearInterval(interval);
  }, [selected.key]);

  if (!result) return null;

  return (
    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
      <span
        className={`h-2 w-2 rounded-full ${result.dotColor} ${
          result.status === "open" ? "animate-pulse" : ""
        }`}
      />
      <span>{result.label}</span>
      <span className="text-xs opacity-60">({result.countdown})</span>
    </div>
  );
}
