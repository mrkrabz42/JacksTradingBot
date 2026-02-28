"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface EquityChartProps {
  data: { date: string; equity: number }[];
}

export function EquityChart({ data }: EquityChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-full min-h-[200px] flex items-center justify-center text-muted-foreground text-sm">
        No portfolio history yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
        <defs>
          <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#FF69B4" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#FF69B4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          tick={{ fill: "#888", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: "#888", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
          domain={["dataMin - 100", "dataMax + 100"]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a1a2e",
            border: "1px solid #2a2a4e",
            borderRadius: "8px",
            color: "#fff",
          }}
          formatter={(value) => [`$${Number(value).toLocaleString()}`, "Equity"]}
        />
        <Area
          type="monotone"
          dataKey="equity"
          stroke="#FF69B4"
          strokeWidth={2}
          fill="url(#equityGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
