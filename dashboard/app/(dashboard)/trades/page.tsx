"use client";

import { RecentTrades } from "@/components/cards/recent-trades";
import { useTrades } from "@/lib/hooks/use-trades";

export default function TradesPage() {
  const { trades } = useTrades();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Trade History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          All executed trades ({trades.length} total)
        </p>
      </div>

      <RecentTrades />
    </div>
  );
}
