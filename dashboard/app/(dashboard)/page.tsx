"use client";

import { DollarSign, TrendingUp, Briefcase } from "lucide-react";
import { OverviewCard } from "@/components/cards/overview-card";
import { PerformanceTabs } from "@/components/cards/performance-tabs";
import { BotStatus } from "@/components/cards/bot-status";
import { MarketSnapshot } from "@/components/cards/market-snapshot";
import { useAccount } from "@/lib/hooks/use-account";
import { usePositions } from "@/lib/hooks/use-positions";
import { formatCurrency, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { account, isLoading: accLoading } = useAccount();
  const { positions, isLoading: posLoading } = usePositions();

  const equity = parseFloat(account?.equity ?? "0");
  const lastEquity = parseFloat(account?.last_equity ?? "0");
  const dayPl = equity - lastEquity;
  const dayPlPct = lastEquity > 0 ? dayPl / lastEquity : 0;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <OverviewCard
          icon={<DollarSign className="h-4 w-4" />}
          label="Portfolio Value"
          value={formatCurrency(equity)}
          loading={accLoading}
        />
        <OverviewCard
          icon={<TrendingUp className="h-4 w-4" />}
          label="Day P&L"
          value={formatCurrency(dayPl)}
          change={formatPercent(dayPlPct)}
          changeColor={dayPl >= 0 ? "text-success" : "text-loss"}
          loading={accLoading}
        />
        <OverviewCard
          icon={<Briefcase className="h-4 w-4" />}
          label="Open Positions"
          value={posLoading ? "..." : `${positions.length} / 5`}
          loading={posLoading}
        />
      </div>

      {/* Performance Tabs */}
      <PerformanceTabs />

      {/* Bot Status + Market Snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BotStatus />
        <MarketSnapshot />
      </div>

    </div>
  );
}
