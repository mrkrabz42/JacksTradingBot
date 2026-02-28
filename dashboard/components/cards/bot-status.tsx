"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { StatusBadge } from "@/components/shared/status-badge";
import { MetricTile } from "@/components/shared/metric-tile";
import { useAccount } from "@/lib/hooks/use-account";
import { usePositions } from "@/lib/hooks/use-positions";
import { useTrades } from "@/lib/hooks/use-trades";
import { RISK_PARAMS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";

export function BotStatus({ embedded }: { embedded?: boolean } = {}) {
  const { account, isLoading: accLoading } = useAccount();
  const { positions, isLoading: posLoading } = usePositions();
  const { trades } = useTrades();

  if (accLoading || posLoading) {
    if (embedded) return <Skeleton className="h-32 w-full" />;
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Bot Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-28" />
        </CardContent>
      </Card>
    );
  }

  const blocked = account?.trading_blocked ?? false;

  const content = (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <StatusBadge
          status={blocked ? "error" : "active"}
          label={blocked ? "Trading Blocked" : "Trading Active"}
        />
        <span className="text-xs bg-pink/10 text-pink px-2 py-1 rounded-full font-medium">
          PAPER MODE
        </span>
      </div>

      {trades.length > 0 ? (
        <span className="text-xs bg-success/10 text-success px-2 py-1 rounded-full font-medium inline-block">
          Live Since: {formatDate(trades[trades.length - 1].transaction_time)}
        </span>
      ) : (
        <span className="text-xs bg-secondary text-muted-foreground px-2 py-1 rounded-full font-medium inline-block">
          No live trades yet
        </span>
      )}

      <Separator className="bg-border" />

      <div className="space-y-3">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Risk Parameters</p>
        <div className="grid grid-cols-2 gap-3">
          <MetricTile
            label="Max Risk/Trade"
            value={`${(RISK_PARAMS.MAX_RISK_PER_TRADE * 100).toFixed(0)}%`}
          />
          <MetricTile
            label="Max Positions"
            value={`${positions.length} / ${RISK_PARAMS.MAX_POSITIONS}`}
          />
          <MetricTile
            label="Daily Loss Limit"
            value={`${(RISK_PARAMS.DAILY_LOSS_LIMIT * 100).toFixed(0)}%`}
          />
          <MetricTile
            label="Day Trades"
            value={`${account?.daytrade_count ?? 0}`}
          />
        </div>
      </div>

      <Separator className="bg-border" />

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Strategy</p>
        <p className="text-sm text-white">SMA Crossover (20/50)</p>
        <p className="text-xs text-muted-foreground">Scan interval: 5 min during market hours</p>
      </div>
    </div>
  );

  if (embedded) return content;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">Bot Status</CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
