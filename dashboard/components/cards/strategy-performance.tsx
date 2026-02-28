"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MetricTile } from "@/components/shared/metric-tile";

const BACKTEST_STATS = {
  strategy: "SMA Crossover (20/50)",
  period: "2024-01-01 to 2025-01-01",
  returnPct: "18.52%",
  winRate: "50.00%",
  sharpe: "0.80",
  maxDrawdown: "-8.34%",
  totalTrades: "12",
  avgTrade: "+1.54%",
};

export function StrategyPerformance() {
  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">Strategy Performance</CardTitle>
        <p className="text-xs text-muted-foreground/60">Backtest Results (Historical Data: 2024-2025)</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm font-medium text-white">{BACKTEST_STATS.strategy}</p>
          <p className="text-xs text-muted-foreground">{BACKTEST_STATS.period}</p>
        </div>

        <Separator className="bg-border" />

        <div className="grid grid-cols-2 gap-4">
          <MetricTile
            label="Return"
            value={BACKTEST_STATS.returnPct}
            changeColor="text-success"
          />
          <MetricTile
            label="Win Rate"
            value={BACKTEST_STATS.winRate}
          />
          <MetricTile
            label="Sharpe Ratio"
            value={BACKTEST_STATS.sharpe}
          />
          <MetricTile
            label="Max Drawdown"
            value={BACKTEST_STATS.maxDrawdown}
            changeColor="text-loss"
          />
          <MetricTile
            label="Total Trades"
            value={BACKTEST_STATS.totalTrades}
          />
          <MetricTile
            label="Avg Trade"
            value={BACKTEST_STATS.avgTrade}
            changeColor="text-success"
          />
        </div>

        <p className="text-[10px] text-muted-foreground italic">
          Based on backtesting.py results. Past performance does not guarantee future results.
        </p>
      </CardContent>
    </Card>
  );
}
