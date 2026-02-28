"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent } from "@/components/ui/card";
import { TIMEZONE_OPTIONS } from "@/lib/constants";
import { getMarketStatus } from "@/lib/market-utils";
import type { TimezoneKey, MarketStatusResult } from "@/lib/types";
import { cn } from "@/lib/utils";

const GlobeView = dynamic(
  () => import("@/components/globe/globe-view").then((m) => m.GlobeView),
  { ssr: false, loading: () => <div className="aspect-square w-full max-w-[400px] mx-auto bg-card rounded-xl animate-pulse" /> }
);

function ExchangeCard({ exchangeKey }: { exchangeKey: TimezoneKey }) {
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
    <Card className="bg-card border-border hover:border-pink/30 transition-colors">
      <CardContent className="p-4 flex flex-col items-center text-center gap-2">
        <span className="text-2xl">{option.flag}</span>
        <p className="text-sm font-medium text-white">{option.exchange}</p>
        <p className="text-xs text-muted-foreground">{option.label}</p>
        <div className="flex items-center gap-2 mt-1">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              result.dotColor,
              result.status === "open" && "animate-pulse"
            )}
          />
          <span className="text-xs text-white">{result.label}</span>
        </div>
        <p className="text-xs text-muted-foreground font-mono">{result.countdown}</p>
      </CardContent>
    </Card>
  );
}

export default function MarketHoursPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Global Market Status</h1>
        <p className="text-sm text-muted-foreground mt-1">Live exchange status and session times worldwide</p>
      </div>

      {/* Exchange cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {TIMEZONE_OPTIONS.map((opt) => (
          <ExchangeCard key={opt.key} exchangeKey={opt.key as TimezoneKey} />
        ))}
      </div>

      {/* Globe */}
      <div className="flex flex-col items-center">
        <GlobeView />
        <p className="text-xs text-muted-foreground mt-4 text-center">
          Markers show exchange locations. Green = open, orange = extended hours, red = closed. Drag to spin.
        </p>
      </div>
    </div>
  );
}
