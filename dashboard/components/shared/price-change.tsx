import { formatCurrency, formatPercent } from "@/lib/utils";

interface PriceChangeProps {
  value: number;
  percent?: number;
  showDollar?: boolean;
}

export function PriceChange({ value, percent, showDollar = true }: PriceChangeProps) {
  const isPositive = value >= 0;
  const color = isPositive ? "text-success" : "text-loss";

  return (
    <span className={`font-medium ${color}`}>
      {showDollar && formatCurrency(Math.abs(value))}{" "}
      {percent !== undefined && `(${formatPercent(percent)})`}
    </span>
  );
}
