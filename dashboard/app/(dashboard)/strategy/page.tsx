"use client";

import { useEffect, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { MetricsGrid } from "@/components/strategy/metrics-grid";
import { TradeTable } from "@/components/strategy/trade-table";
import { RulesPanel } from "@/components/strategy/rules-panel";
import { InsightsPanel } from "@/components/strategy/insights-panel";
import { CoachPanel } from "@/components/strategy/coach-panel";
import { BookOpen, TrendingUp } from "lucide-react";

function ResizeHandle() {
  return (
    <Separator className="w-1 mx-1 relative group/handle">
      <div className="absolute inset-y-0 left-0 right-0 rounded-full transition-colors duration-200 group-hover/handle:bg-pink cursor-col-resize" />
      <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 w-0.5 h-6 rounded-full bg-border group-hover/handle:bg-pink transition-colors duration-200" />
    </Separator>
  );
}

export default function StrategyPage() {
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const check = () => setIsDesktop(window.innerWidth >= 1024);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-pink" />
            <h1 className="text-2xl font-bold text-white">Strategy Performance</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            SMA Crossover (20/50) — Click any trade to see the bot&apos;s reasoning and leave feedback
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-card border border-border rounded-lg px-3 py-1.5">
          <BookOpen className="h-3.5 w-3.5" />
          <span>Teaching Mode</span>
        </div>
      </div>

      <MetricsGrid />
      <TradeTable />

      {/* Module 3: Three-panel layout with resizable panels */}
      {isDesktop ? (
        <Group
          id="strategy-panels"
          orientation="horizontal"
          defaultLayout={{ rules: 30, insights: 35, coach: 35 }}
        >
          <Panel id="rules" defaultSize="30%" minSize="20%">
            <RulesPanel />
          </Panel>
          <ResizeHandle />
          <Panel id="insights" defaultSize="35%" minSize="20%">
            <InsightsPanel />
          </Panel>
          <ResizeHandle />
          <Panel id="coach" defaultSize="35%" minSize="20%">
            <CoachPanel />
          </Panel>
        </Group>
      ) : (
        <div className="space-y-6">
          <RulesPanel />
          <InsightsPanel />
          <CoachPanel />
        </div>
      )}

      <p className="text-xs text-muted-foreground italic">
        Trades fetched from Alpaca paper account. Click a trade row to expand bot explanations and add your feedback.
      </p>
    </div>
  );
}
