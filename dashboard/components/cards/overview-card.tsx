"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface OverviewCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  change?: string;
  changeColor?: string;
  loading?: boolean;
}

export function OverviewCard({ icon, label, value, change, changeColor, loading }: OverviewCardProps) {
  if (loading) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="p-5">
          <div className="animate-pulse space-y-3">
            <div className="h-4 w-20 bg-border rounded" />
            <div className="h-7 w-28 bg-border rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border hover:border-pink/30 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-muted-foreground">{icon}</span>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</p>
        </div>
        <p className="text-2xl font-bold text-white">{value}</p>
        {change && (
          <p className={cn("text-sm font-medium mt-1", changeColor ?? "text-muted-foreground")}>
            {change}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
