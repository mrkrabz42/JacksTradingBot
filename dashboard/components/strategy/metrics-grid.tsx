"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { TrendingUp, Target, BarChart3, TrendingDown, Hash, Percent } from "lucide-react";

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

const METRICS = [
  {
    label: "Return",
    value: BACKTEST_STATS.returnPct,
    icon: TrendingUp,
    color: "text-success",
    tooltip: "Total percentage return over the backtest period. Higher is better.",
  },
  {
    label: "Win Rate",
    value: BACKTEST_STATS.winRate,
    icon: Target,
    color: "text-white",
    tooltip: "Percentage of trades that were profitable. Above 50% is generally good for trend-following strategies.",
  },
  {
    label: "Sharpe Ratio",
    value: BACKTEST_STATS.sharpe,
    icon: BarChart3,
    color: "text-cyan",
    tooltip: "Risk-adjusted return. Above 1.0 is good, above 2.0 is excellent. Measures return per unit of risk taken.",
  },
  {
    label: "Max Drawdown",
    value: BACKTEST_STATS.maxDrawdown,
    icon: TrendingDown,
    color: "text-loss",
    tooltip: "Largest peak-to-trough decline during the backtest. Smaller is better — shows worst-case scenario.",
  },
  {
    label: "Total Trades",
    value: BACKTEST_STATS.totalTrades,
    icon: Hash,
    color: "text-white",
    tooltip: "Total number of completed trades in the backtest period.",
  },
  {
    label: "Avg Trade",
    value: BACKTEST_STATS.avgTrade,
    icon: Percent,
    color: "text-success",
    tooltip: "Average return per trade. A positive number means the strategy is profitable on average.",
  },
];

export function MetricsGrid() {
  return (
    <TooltipProvider>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {METRICS.map((metric) => (
          <Tooltip key={metric.label}>
            <TooltipTrigger asChild>
              <Card className="bg-card border-border hover:border-pink/30 transition-colors cursor-help">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <metric.icon className={cn("h-4 w-4", metric.color)} />
                    <p className="text-xs text-muted-foreground">{metric.label}</p>
                  </div>
                  <p className={cn("text-xl font-bold", metric.color)}>{metric.value}</p>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[250px]">
              <p className="text-sm">{metric.tooltip}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}
