"use client";

import dynamic from "next/dynamic";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ActivePositions } from "./active-positions";
import { RecentTrades } from "./recent-trades";
import { BotStatus } from "./bot-status";
import { usePortfolioHistory } from "@/lib/hooks/use-portfolio-history";
import { format } from "date-fns";

const EquityChart = dynamic(
  () => import("@/components/charts/equity-chart").then((m) => m.EquityChart),
  { ssr: false, loading: () => <Skeleton className="h-[350px] w-full" /> }
);

export function PerformanceTabs() {
  const { history, isLoading } = usePortfolioHistory();

  const chartData =
    history?.timestamp?.map((ts, i) => ({
      date: format(new Date(ts * 1000), "MMM dd"),
      equity: history.equity[i],
    })) ?? [];

  return (
    <Card className="bg-card border-border">
      <CardContent className="p-0">
        <Tabs defaultValue="performance" className="w-full">
          <div className="px-5 pt-4 border-b border-border">
            <TabsList className="bg-transparent gap-2 h-auto p-0">
              <TabsTrigger
                value="performance"
                className="data-[state=active]:bg-pink/10 data-[state=active]:text-pink data-[state=active]:shadow-none rounded-lg px-4 py-2 text-muted-foreground"
              >
                Performance
              </TabsTrigger>
              <TabsTrigger
                value="positions"
                className="data-[state=active]:bg-pink/10 data-[state=active]:text-pink data-[state=active]:shadow-none rounded-lg px-4 py-2 text-muted-foreground"
              >
                Positions
              </TabsTrigger>
              <TabsTrigger
                value="trades"
                className="data-[state=active]:bg-pink/10 data-[state=active]:text-pink data-[state=active]:shadow-none rounded-lg px-4 py-2 text-muted-foreground"
              >
                Trades
              </TabsTrigger>
              <TabsTrigger
                value="risk"
                className="data-[state=active]:bg-pink/10 data-[state=active]:text-pink data-[state=active]:shadow-none rounded-lg px-4 py-2 text-muted-foreground"
              >
                Risk
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="p-5">
            <TabsContent value="performance" className="mt-0">
              {isLoading ? (
                <Skeleton className="h-[350px] w-full" />
              ) : (
                <div className="h-[350px]">
                  <EquityChart data={chartData} />
                </div>
              )}
            </TabsContent>

            <TabsContent value="positions" className="mt-0">
              <ActivePositions embedded />
            </TabsContent>

            <TabsContent value="trades" className="mt-0">
              <RecentTrades embedded />
            </TabsContent>

            <TabsContent value="risk" className="mt-0">
              <BotStatus embedded />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
}
