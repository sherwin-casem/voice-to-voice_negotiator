"use client";

import { motion } from "framer-motion";

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
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
  const reduceMotion = usePrefersReducedMotion();
  const numericPercent =
    percent ??
    (typeof value === "number" ? value : value === "High" ? 90 : value === "Low" ? 25 : 70);
  const width = Math.min(100, Math.max(0, numericPercent));

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
        {reduceMotion ? (
          <div
            className={cn("metric-fill", variant === "success" && "metric-fill-success")}
            style={{ width: `${width}%` }}
          />
        ) : (
          <motion.div
            className={cn("metric-fill", variant === "success" && "metric-fill-success")}
            initial={{ width: 0 }}
            whileInView={{ width: `${width}%` }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          />
        )}
      </div>
    </div>
  );
}
