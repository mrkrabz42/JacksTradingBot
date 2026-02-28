"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { usePositions } from "@/lib/hooks/use-positions";
import { formatCurrency, formatPercent } from "@/lib/utils";

export function ActivePositions({ embedded }: { embedded?: boolean } = {}) {
  const { positions, isLoading } = usePositions();

  if (isLoading) {
    if (embedded) return <Skeleton className="h-32 w-full" />;
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const content = positions.length === 0 ? (
    <p className="text-sm text-muted-foreground text-center py-8">
      No open positions
    </p>
  ) : (
    <Table>
      <TableHeader>
        <TableRow className="border-border hover:bg-transparent">
          <TableHead className="text-muted-foreground">Symbol</TableHead>
          <TableHead className="text-muted-foreground text-right">Qty</TableHead>
          <TableHead className="text-muted-foreground text-right">Entry</TableHead>
          <TableHead className="text-muted-foreground text-right">Current</TableHead>
          <TableHead className="text-muted-foreground text-right">P&L</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {positions.map((pos) => {
          const pl = parseFloat(pos.unrealized_pl);
          const plPct = parseFloat(pos.unrealized_plpc);
          return (
            <TableRow key={pos.asset_id} className="border-border">
              <TableCell className="font-medium text-white">{pos.symbol}</TableCell>
              <TableCell className="text-right">{pos.qty}</TableCell>
              <TableCell className="text-right">{formatCurrency(pos.avg_entry_price)}</TableCell>
              <TableCell className="text-right">{formatCurrency(pos.current_price)}</TableCell>
              <TableCell className={`text-right font-medium ${pl >= 0 ? "text-success" : "text-loss"}`}>
                {formatCurrency(pl)} ({formatPercent(plPct)})
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );

  if (embedded) return content;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          Active Positions
          <span className="ml-2 text-xs bg-secondary px-2 py-0.5 rounded-full">
            {positions.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
