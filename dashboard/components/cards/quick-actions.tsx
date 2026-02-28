"use client";

import { Play, Pause, Search, FlaskConical } from "lucide-react";

const ACTIONS = [
  { label: "Start Bot", icon: Play, color: "text-success", bg: "bg-success/10 hover:bg-success/20" },
  { label: "Pause", icon: Pause, color: "text-yellow-500", bg: "bg-yellow-500/10 hover:bg-yellow-500/20" },
  { label: "Force Scan", icon: Search, color: "text-cyan", bg: "bg-cyan/10 hover:bg-cyan/20" },
  { label: "Backtest", icon: FlaskConical, color: "text-pink", bg: "bg-pink/10 hover:bg-pink/20" },
] as const;

export function QuickActions() {
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Quick Actions</p>
      <div className="grid grid-cols-2 gap-2">
        {ACTIONS.map(({ label, icon: Icon, color, bg }) => (
          <button
            key={label}
            onClick={() => alert(`${label} — coming soon!`)}
            className={`flex flex-col items-center gap-1.5 py-3 px-2 rounded-lg transition-colors ${bg}`}
          >
            <Icon className={`h-4 w-4 ${color}`} />
            <span className={`text-xs font-medium ${color}`}>{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
