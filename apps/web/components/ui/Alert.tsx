import { cn } from "@/lib/format";

export function Alert({
  title,
  children,
  variant = "info",
}: {
  title?: string;
  children: React.ReactNode;
  variant?: "info" | "warning" | "error" | "success";
}) {
  const styles = {
    info: "border-cyan-500/30 bg-cyan-500/10 text-cyan-100",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-100",
    error: "border-red-500/30 bg-red-500/10 text-red-100",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
  }[variant];

  return (
    <div className={cn("rounded-xl border px-4 py-3 text-sm", styles)} role="status">
      {title ? <p className="font-medium">{title}</p> : null}
      <div className={title ? "mt-1 opacity-90" : undefined}>{children}</div>
    </div>
  );
}

export function PreviewDataBanner({ endpoint }: { endpoint: string }) {
  return (
    <Alert variant="warning" title="Preview data">
      Showing sample data because <code className="font-mono text-xs opacity-80">{endpoint}</code>{" "}
      is not available yet. Live session actions still use the real API where implemented.
    </Alert>
  );
}

export function PreviewMetricsBanner() {
  return (
    <p className="text-xs text-[var(--text-dim)]">
      Preview metrics — live scoring coming soon
    </p>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div
      className="flex items-center gap-2 text-sm text-[var(--text-muted)]"
      role="status"
      aria-live="polite"
    >
      <span
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-teal-400"
        aria-hidden="true"
      />
      <span>{label}</span>
    </div>
  );
}
