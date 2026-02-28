"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketSnapshot } from "@/lib/hooks/use-market-snapshot";
import { INDEX_SYMBOLS } from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";

const INDEX_NAMES: Record<string, string> = {
  SPY: "S&P 500",
  QQQ: "Nasdaq 100",
  DIA: "Dow Jones",
  IWM: "Russell 2000",
};

export function MarketSnapshot() {
  const { snapshot, isLoading } = useMarketSnapshot();

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Market Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {INDEX_SYMBOLS.map((s) => (
            <Skeleton key={s} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const quotes = snapshot?.quotes ?? {};

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">Market Snapshot</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {INDEX_SYMBOLS.map((symbol) => {
          const q = quotes[symbol];
          if (!q) {
            return (
              <div key={symbol} className="flex justify-between items-center py-2">
                <div>
                  <p className="text-sm font-medium text-white">{symbol}</p>
                  <p className="text-xs text-muted-foreground">{INDEX_NAMES[symbol]}</p>
                </div>
                <p className="text-sm text-muted-foreground">--</p>
              </div>
            );
          }

          const midPrice = (q.ap + q.bp) / 2;

          return (
            <div key={symbol} className="flex justify-between items-center py-2 border-b border-border last:border-0">
              <div>
                <p className="text-sm font-medium text-white">{symbol}</p>
                <p className="text-xs text-muted-foreground">{INDEX_NAMES[symbol]}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-white">
                  {formatCurrency(midPrice)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Bid {formatCurrency(q.bp)} / Ask {formatCurrency(q.ap)}
                </p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
