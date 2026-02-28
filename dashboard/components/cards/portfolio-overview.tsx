"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTile } from "@/components/shared/metric-tile";
import { useAccount } from "@/lib/hooks/use-account";
import { usePortfolioHistory } from "@/lib/hooks/use-portfolio-history";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { format } from "date-fns";

const EquityChart = dynamic(
  () => import("@/components/charts/equity-chart").then((m) => m.EquityChart),
  { ssr: false, loading: () => <Skeleton className="h-[200px] w-full" /> }
);

export function PortfolioOverview() {
  const { account, isLoading: accLoading } = useAccount();
  const { history, isLoading: histLoading } = usePortfolioHistory();

  if (accLoading || histLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Portfolio Overview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const equity = parseFloat(account?.equity ?? "0");
  const lastEquity = parseFloat(account?.last_equity ?? "0");
  const dayPl = equity - lastEquity;
  const dayPlPct = lastEquity > 0 ? dayPl / lastEquity : 0;
  const buyingPower = parseFloat(account?.buying_power ?? "0");

  const chartData =
    history?.timestamp?.map((ts, i) => ({
      date: format(new Date(ts * 1000), "MMM dd"),
      equity: history.equity[i],
    })) ?? [];

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">Portfolio Overview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <MetricTile label="Equity" value={formatCurrency(equity)} />
          <MetricTile
            label="Day P&L"
            value={formatCurrency(dayPl)}
            change={formatPercent(dayPlPct)}
            changeColor={dayPl >= 0 ? "text-success" : "text-loss"}
          />
          <MetricTile label="Buying Power" value={formatCurrency(buyingPower)} />
        </div>
        <EquityChart data={chartData} />
      </CardContent>
    </Card>
  );
}
