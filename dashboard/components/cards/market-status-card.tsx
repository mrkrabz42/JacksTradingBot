"use client";

import { useEffect, useState } from "react";
import { useTimezone } from "@/lib/context/timezone-context";
import { getMarketStatus } from "@/lib/market-utils";
import { TIMEZONE_OPTIONS } from "@/lib/constants";
import type { TimezoneKey, MarketStatusResult } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MarketStatusCardProps {
  exchangeKey: TimezoneKey;
}

export function MarketStatusCard({ exchangeKey }: MarketStatusCardProps) {
  const { setTimezone } = useTimezone();
  const [result, setResult] = useState<MarketStatusResult | null>(null);

  const option = TIMEZONE_OPTIONS.find((o) => o.key === exchangeKey);

  useEffect(() => {
    const update = () => setResult(getMarketStatus(new Date(), exchangeKey));
    update();
    const interval = setInterval(update, 10_000);
    return () => clearInterval(interval);
  }, [exchangeKey]);

  if (!result || !option) return null;

  return (
    <button
      onClick={() => setTimezone(exchangeKey)}
      className="w-full flex items-center gap-3 py-2.5 px-3 rounded-lg bg-background/50 hover:bg-background transition-colors text-left group"
    >
      <span className="text-lg">{option.flag}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{option.exchange}</p>
        <p className="text-xs text-muted-foreground">{result.label}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-muted-foreground font-mono">{result.countdown}</span>
        <span
          className={cn(
            "h-2 w-2 rounded-full flex-shrink-0",
            result.dotColor,
            result.status === "open" && "animate-pulse"
          )}
        />
      </div>
    </button>
  );
}
