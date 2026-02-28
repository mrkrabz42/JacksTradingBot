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
import { useTrades } from "@/lib/hooks/use-trades";
import { useTimezone } from "@/lib/context/timezone-context";
import { formatCurrency, formatTime } from "@/lib/utils";

export function RecentTrades({ embedded }: { embedded?: boolean } = {}) {
  const { trades, isLoading } = useTrades();
  const { selected } = useTimezone();

  if (isLoading) {
    if (embedded) return <Skeleton className="h-32 w-full" />;
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const content = trades.length === 0 ? (
    <p className="text-sm text-muted-foreground text-center py-8">
      No trades yet
    </p>
  ) : (
    <div className="max-h-[300px] overflow-y-auto">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-muted-foreground">Time</TableHead>
            <TableHead className="text-muted-foreground">Side</TableHead>
            <TableHead className="text-muted-foreground">Symbol</TableHead>
            <TableHead className="text-muted-foreground text-right">Qty</TableHead>
            <TableHead className="text-muted-foreground text-right">Price</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trades.map((trade) => (
            <TableRow key={trade.id} className="border-border group">
              <TableCell className="text-xs text-muted-foreground">
                {formatTime(trade.transaction_time, selected.iana)}
              </TableCell>
              <TableCell>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded ${
                    trade.side === "buy"
                      ? "bg-success/10 text-success"
                      : "bg-loss/10 text-loss"
                  }`}
                >
                  {trade.side.toUpperCase()}
                </span>
              </TableCell>
              <TableCell className="font-medium text-white">{trade.symbol}</TableCell>
              <TableCell className="text-right">{trade.qty}</TableCell>
              <TableCell className="text-right">{formatCurrency(trade.price)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );

  if (embedded) return content;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">Recent Trades</CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}
