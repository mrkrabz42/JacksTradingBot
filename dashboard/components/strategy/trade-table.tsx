"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useTrades } from "@/lib/hooks/use-trades";
import { useTimezone } from "@/lib/context/timezone-context";
import { formatCurrency, formatTime } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { TradeDetail } from "./trade-detail";
import { ChevronDown, ChevronUp, ChevronRight, Filter, LineChart, Search } from "lucide-react";
import { cn } from "@/lib/utils";

type SortField = "time" | "symbol" | "side" | "qty" | "price";
type SortDir = "asc" | "desc";
type FilterMode = "all" | "buy" | "sell";

export function TradeTable() {
  const { trades, isLoading } = useTrades();
  const { selected } = useTimezone();
  const [sortField, setSortField] = useState<SortField>("time");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filter, setFilter] = useState<FilterMode>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Trade History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex gap-4">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-16 ml-auto" />
              <Skeleton className="h-8 w-20" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const filtered = filter === "all" ? trades : trades.filter((t) => t.side === filter);

  const sorted = [...filtered].sort((a, b) => {
    const dir = sortDir === "asc" ? 1 : -1;
    switch (sortField) {
      case "time":
        return dir * (new Date(a.transaction_time).getTime() - new Date(b.transaction_time).getTime());
      case "symbol":
        return dir * a.symbol.localeCompare(b.symbol);
      case "side":
        return dir * a.side.localeCompare(b.side);
      case "qty":
        return dir * (parseFloat(a.qty) - parseFloat(b.qty));
      case "price":
        return dir * (parseFloat(a.price) - parseFloat(b.price));
      default:
        return 0;
    }
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDir === "asc" ? (
      <ChevronUp className="h-3 w-3 inline ml-1" />
    ) : (
      <ChevronDown className="h-3 w-3 inline ml-1" />
    );
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm text-muted-foreground">
          Trade History
          <span className="ml-2 text-xs bg-secondary px-2 py-0.5 rounded-full">
            {sorted.length}
          </span>
        </CardTitle>
        <div className="flex items-center gap-1">
          <Filter className="h-3 w-3 text-muted-foreground" />
          {(["all", "buy", "sell"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "text-xs px-2 py-1 rounded transition-colors",
                filter === f
                  ? "bg-pink/10 text-pink"
                  : "text-muted-foreground hover:text-white"
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-4">
            <div className="relative">
              <LineChart className="h-12 w-12 text-muted-foreground/30" />
              <Search className="h-5 w-5 text-pink absolute -bottom-1 -right-1" />
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-medium text-muted-foreground">No trades yet</p>
              <p className="text-xs text-muted-foreground/60 max-w-[280px]">
                Trades will appear here once the bot executes orders via Alpaca.
                Run the bot during market hours to start trading.
              </p>
            </div>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="w-8" />
                <TableHead className="text-muted-foreground cursor-pointer" onClick={() => handleSort("time")}>
                  Time <SortIcon field="time" />
                </TableHead>
                <TableHead className="text-muted-foreground cursor-pointer" onClick={() => handleSort("side")}>
                  Side <SortIcon field="side" />
                </TableHead>
                <TableHead className="text-muted-foreground cursor-pointer" onClick={() => handleSort("symbol")}>
                  Symbol <SortIcon field="symbol" />
                </TableHead>
                <TableHead className="text-muted-foreground text-right cursor-pointer" onClick={() => handleSort("qty")}>
                  Qty <SortIcon field="qty" />
                </TableHead>
                <TableHead className="text-muted-foreground text-right cursor-pointer" onClick={() => handleSort("price")}>
                  Price <SortIcon field="price" />
                </TableHead>
                <TableHead className="text-muted-foreground text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((trade) => {
                const isExpanded = expandedId === trade.id;
                return (
                  <><TableRow
                      key={trade.id}
                      className={cn(
                        "border-border cursor-pointer transition-colors",
                        isExpanded ? "bg-white/5" : "hover:bg-white/5"
                      )}
                      onClick={() => setExpandedId(isExpanded ? null : trade.id)}
                    >
                      <TableCell className="w-8 px-2">
                        <ChevronRight
                          className={cn(
                            "h-4 w-4 text-muted-foreground transition-transform",
                            isExpanded && "rotate-90 text-pink"
                          )}
                        />
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatTime(trade.transaction_time, selected.iana)}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "text-xs font-medium px-2 py-0.5 rounded",
                            trade.side === "buy" ? "bg-success/10 text-success" : "bg-loss/10 text-loss"
                          )}
                        >
                          {trade.side.toUpperCase()}
                        </span>
                      </TableCell>
                      <TableCell className="font-medium text-white">{trade.symbol}</TableCell>
                      <TableCell className="text-right">{trade.qty}</TableCell>
                      <TableCell className="text-right">{formatCurrency(trade.price)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatCurrency(parseFloat(trade.qty) * parseFloat(trade.price))}
                      </TableCell>
                    </TableRow>
                    {isExpanded && (
                      <TableRow key={`${trade.id}-detail`} className="border-border bg-card/50 hover:bg-card/50">
                        <TableCell colSpan={7} className="p-0">
                          <div className="border-l-2 border-pink ml-4">
                            <TradeDetail trade={trade} />
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
