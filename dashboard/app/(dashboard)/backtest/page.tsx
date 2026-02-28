"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Group, Panel, Separator } from "react-resizable-panels";
import { BacktestToolbar } from "@/components/backtest/backtest-toolbar";
import { BacktestMetrics } from "@/components/backtest/backtest-metrics";
import { useBacktest } from "@/lib/hooks/use-backtest";
import { CandlestickChart as CandlestickChartIcon, Radio } from "lucide-react";

const CandlestickChart = dynamic(
  () => import("@/components/backtest/candlestick-chart").then(m => m.CandlestickChart),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-card rounded-xl animate-pulse">
        <span className="text-muted-foreground text-sm">Loading chart...</span>
      </div>
    ),
  },
);

function ResizeHandle() {
  return (
    <Separator className="h-1 my-1 relative group/handle">
      <div className="absolute inset-x-0 top-0 bottom-0 rounded-full transition-colors duration-200 group-hover/handle:bg-pink cursor-row-resize" />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-0.5 w-6 rounded-full bg-border group-hover/handle:bg-pink transition-colors duration-200" />
    </Separator>
  );
}

export default function BacktestPage() {
  const { data, liveBars, isLoading, isLive, error, run } = useBacktest();
  const [scrollTarget, setScrollTarget] = useState<string | null>(null);

  const handleEventClick = (timestamp: string) => {
    setScrollTarget(null);
    setTimeout(() => setScrollTarget(timestamp), 0);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] gap-3 p-4">
      <BacktestToolbar onRun={run} isLoading={isLoading} />

      {error && (
        <div className="px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {!data && !isLoading && !error && (
        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-3">
          <CandlestickChartIcon className="h-12 w-12 opacity-30" />
          <p className="text-sm">Configure parameters above and run a backtest</p>
        </div>
      )}

      {isLoading && !data && (
        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-3">
          <div className="h-8 w-8 border-2 border-pink border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Fetching market data...</p>
        </div>
      )}

      {data && (
        <Group id="backtest-panels" orientation="vertical" className="flex-1 min-h-0">
          <Panel id="chart" defaultSize="65%" minSize="30%">
            <div className="h-full bg-card border border-border rounded-xl overflow-hidden relative">
              {/* Live indicator */}
              {isLive && (
                <div className="absolute top-2 right-2 z-10 flex items-center gap-1.5 px-2 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-md">
                  <Radio className="h-3 w-3 text-emerald-400 animate-pulse" />
                  <span className="text-[10px] font-medium text-emerald-400 uppercase">Live</span>
                </div>
              )}
              <div className="p-1 h-full">
                <CandlestickChart
                  bars={data.bars}
                  swings={data.swings}
                  mssEvents={data.mss_events}
                  sweepEvents={data.sweep_events}
                  liquidityPools={data.liquidity_pools}
                  liveBars={liveBars}
                  scrollToTimestamp={scrollTarget}
                />
              </div>
            </div>
          </Panel>

          <ResizeHandle />

          <Panel id="metrics" defaultSize="35%" minSize="15%">
            <div className="h-full bg-card border border-border rounded-xl overflow-hidden">
              <BacktestMetrics
                metrics={data.metrics}
                mssEvents={data.mss_events}
                sweepEvents={data.sweep_events}
                onEventClick={handleEventClick}
              />
            </div>
          </Panel>
        </Group>
      )}
    </div>
  );
}
