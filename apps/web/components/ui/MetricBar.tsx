import { cn } from "@/lib/format";

export interface MetricBarProps {
  label: string;
  value: string | number;
  percent?: number;
  variant?: "teal" | "success";
  className?: string;
}

export function MetricBar({
  label,
  value,
  percent,
  variant = "teal",
  className,
}: MetricBarProps) {
  const numericPercent =
    percent ??
    (typeof value === "number" ? value : value === "High" ? 90 : value === "Low" ? 25 : 70);

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className="font-medium text-[var(--text-primary)]">{value}</span>
      </div>
      <div
        className="metric-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={numericPercent}
        aria-label={`${label}: ${value}`}
      >
        <div
          className={cn("metric-fill", variant === "success" && "metric-fill-success")}
          style={{ width: `${Math.min(100, Math.max(0, numericPercent))}%` }}
        />
      </div>
    </div>
  );
}
