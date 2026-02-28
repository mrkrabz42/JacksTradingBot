"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";

interface MiniSparklineProps {
  data: number[];
  color?: string;
}

export function MiniSparkline({ data, color = "#FF69B4" }: MiniSparklineProps) {
  const chartData = data.map((v, i) => ({ v, i }));

  return (
    <ResponsiveContainer width={80} height={32}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
