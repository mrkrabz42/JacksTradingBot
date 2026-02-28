interface StatusBadgeProps {
  status: "active" | "inactive" | "warning" | "error";
  label: string;
}

const colors = {
  active: "bg-success",
  inactive: "bg-muted-foreground",
  warning: "bg-yellow-500",
  error: "bg-loss",
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full ${colors[status]}`} />
      <span className="text-sm text-muted-foreground">{label}</span>
    </div>
  );
}
