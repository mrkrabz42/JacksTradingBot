"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTrades } from "@/lib/hooks/use-trades";
import { useAllFeedback } from "@/lib/hooks/use-user-feedback";
import { useTradeExplanations } from "@/lib/hooks/use-trade-explanations";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";
import {
  BarChart3, DollarSign, PieChart,
  MessageSquare, ThumbsUp, ThumbsDown, HelpCircle, Activity,
} from "lucide-react";

interface InsightStat {
  label: string;
  value: string;
  subtext?: string;
  color: string;
  icon: typeof BarChart3;
}

export function InsightsPanel() {
  const { trades, isLoading: tradesLoading } = useTrades();
  const { feedback, isLoading: fbLoading } = useAllFeedback();
  const { explanations, isLoading: expLoading } = useTradeExplanations();

  const isLoading = tradesLoading || fbLoading || expLoading;

  const insights = useMemo(() => {
    if (trades.length === 0) return null;

    // Symbol breakdown
    const symbolMap: Record<string, { buys: number; sells: number; volume: number }> = {};
    let totalBuys = 0;
    let totalSells = 0;
    let totalVolume = 0;

    for (const t of trades) {
      const sym = t.symbol;
      if (!symbolMap[sym]) symbolMap[sym] = { buys: 0, sells: 0, volume: 0 };
      const val = parseFloat(t.qty) * parseFloat(t.price);
      symbolMap[sym].volume += val;
      totalVolume += val;
      if (t.side === "buy") {
        symbolMap[sym].buys++;
        totalBuys++;
      } else {
        symbolMap[sym].sells++;
        totalSells++;
      }
    }

    // Top symbols by volume
    const topSymbols = Object.entries(symbolMap)
      .sort((a, b) => b[1].volume - a[1].volume)
      .slice(0, 5);

    // Feedback breakdown
    let goodCount = 0;
    let badCount = 0;
    let questionableCount = 0;
    for (const fb of feedback) {
      if (fb.sentiment === "good") goodCount++;
      else if (fb.sentiment === "bad") badCount++;
      else if (fb.sentiment === "questionable") questionableCount++;
    }

    return {
      totalTrades: trades.length,
      totalBuys,
      totalSells,
      totalVolume,
      topSymbols,
      symbolMap,
      feedbackTotal: feedback.length,
      goodCount,
      badCount,
      questionableCount,
      explanationsCount: explanations.length,
    };
  }, [trades, feedback, explanations]);

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Trade Insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!insights) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-cyan" />
            Trade Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 space-y-2">
            <Activity className="h-8 w-8 text-muted-foreground/30" />
            <p className="text-xs text-muted-foreground text-center">
              Insights will populate once trades start flowing.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const stats: InsightStat[] = [
    {
      label: "Total Volume",
      value: formatCurrency(insights.totalVolume),
      subtext: `${insights.totalTrades} trades`,
      color: "text-white",
      icon: DollarSign,
    },
    {
      label: "Buy / Sell",
      value: `${insights.totalBuys} / ${insights.totalSells}`,
      subtext: `${insights.totalTrades > 0 ? ((insights.totalBuys / insights.totalTrades) * 100).toFixed(0) : 0}% buys`,
      color: "text-success",
      icon: PieChart,
    },
    {
      label: "Reviewed",
      value: `${insights.feedbackTotal}`,
      subtext: `of ${insights.totalTrades} trades`,
      color: "text-cyan",
      icon: MessageSquare,
    },
    {
      label: "Explained",
      value: `${insights.explanationsCount}`,
      subtext: `of ${insights.totalTrades} trades`,
      color: "text-pink",
      icon: BarChart3,
    },
  ];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-cyan" />
          Trade Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-2">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="bg-background/50 rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon className={cn("h-3 w-3", stat.color)} />
                  <span className="text-[10px] text-muted-foreground uppercase">{stat.label}</span>
                </div>
                <p className={cn("text-sm font-semibold", stat.color)}>{stat.value}</p>
                {stat.subtext && (
                  <p className="text-[10px] text-muted-foreground">{stat.subtext}</p>
                )}
              </div>
            );
          })}
        </div>

        {/* Top symbols */}
        {insights.topSymbols.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground font-medium mb-2 uppercase">Top Symbols</p>
            <div className="space-y-1.5">
              {insights.topSymbols.map(([symbol, data]) => {
                const pct = (data.volume / insights.totalVolume) * 100;
                return (
                  <div key={symbol} className="flex items-center gap-2">
                    <span className="text-xs font-medium text-white w-10">{symbol}</span>
                    <div className="flex-1 h-4 bg-background/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-pink/60 to-pink rounded-full transition-all"
                        style={{ width: `${Math.max(pct, 4)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground w-12 text-right">
                      {formatCurrency(data.volume)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Feedback sentiment breakdown */}
        {insights.feedbackTotal > 0 && (
          <div>
            <p className="text-xs text-muted-foreground font-medium mb-2 uppercase">Feedback Sentiment</p>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <ThumbsUp className="h-3.5 w-3.5 text-success" />
                <span className="text-xs text-success font-medium">{insights.goodCount}</span>
              </div>
              <div className="flex items-center gap-1">
                <ThumbsDown className="h-3.5 w-3.5 text-loss" />
                <span className="text-xs text-loss font-medium">{insights.badCount}</span>
              </div>
              <div className="flex items-center gap-1">
                <HelpCircle className="h-3.5 w-3.5 text-yellow-500" />
                <span className="text-xs text-yellow-500 font-medium">{insights.questionableCount}</span>
              </div>
            </div>
            {/* Sentiment bar */}
            <div className="flex h-2 rounded-full overflow-hidden mt-2 bg-background/50">
              {insights.goodCount > 0 && (
                <div
                  className="bg-success transition-all"
                  style={{ width: `${(insights.goodCount / insights.feedbackTotal) * 100}%` }}
                />
              )}
              {insights.questionableCount > 0 && (
                <div
                  className="bg-yellow-500 transition-all"
                  style={{ width: `${(insights.questionableCount / insights.feedbackTotal) * 100}%` }}
                />
              )}
              {insights.badCount > 0 && (
                <div
                  className="bg-loss transition-all"
                  style={{ width: `${(insights.badCount / insights.feedbackTotal) * 100}%` }}
                />
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
