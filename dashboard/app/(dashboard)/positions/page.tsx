"use client";

import { Card, CardContent } from "@/components/ui/card";
import { ActivePositions } from "@/components/cards/active-positions";
import { usePositions } from "@/lib/hooks/use-positions";
import { formatCurrency } from "@/lib/utils";
import { Briefcase, DollarSign, TrendingUp } from "lucide-react";

export default function PositionsPage() {
  const { positions } = usePositions();

  const totalUnrealized = positions.reduce((sum, p) => sum + parseFloat(p.unrealized_pl), 0);
  const totalMarketValue = positions.reduce((sum, p) => sum + parseFloat(p.market_value), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Positions</h1>
        <p className="text-sm text-muted-foreground mt-1">Current open positions and portfolio allocation</p>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <Briefcase className="h-5 w-5 text-pink" />
            <div>
              <p className="text-xs text-muted-foreground">Open Positions</p>
              <p className="text-lg font-bold text-white">{positions.length} / 5</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <DollarSign className="h-5 w-5 text-cyan" />
            <div>
              <p className="text-xs text-muted-foreground">Market Value</p>
              <p className="text-lg font-bold text-white">{formatCurrency(totalMarketValue)}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4 flex items-center gap-3">
            <TrendingUp className={`h-5 w-5 ${totalUnrealized >= 0 ? "text-success" : "text-loss"}`} />
            <div>
              <p className="text-xs text-muted-foreground">Unrealized P&L</p>
              <p className={`text-lg font-bold ${totalUnrealized >= 0 ? "text-success" : "text-loss"}`}>
                {formatCurrency(totalUnrealized)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <ActivePositions />
    </div>
  );
}
