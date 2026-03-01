"use client";

import { PathwayCard } from "@/components/cards/pathway-card";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-6">
        <PathwayCard />
      </div>
    </div>
  );
}
