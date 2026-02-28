interface MetricTileProps {
  label: string;
  value: string;
  change?: string;
  changeColor?: string;
}

export function MetricTile({ label, value, change, changeColor }: MetricTileProps) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
      {change && (
        <p className={`text-xs font-medium ${changeColor ?? "text-muted-foreground"}`}>
          {change}
        </p>
      )}
    </div>
  );
}
