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
    info: "border-blue-200 bg-blue-50 text-blue-900",
    warning: "border-amber-200 bg-amber-50 text-amber-900",
    error: "border-red-200 bg-red-50 text-red-900",
    success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  }[variant];

  return (
    <div className={cn("rounded-xl border px-4 py-3 text-sm", styles)} role="status">
      {title ? <p className="font-medium">{title}</p> : null}
      <div className={title ? "mt-1" : undefined}>{children}</div>
    </div>
  );
}

export function PreviewDataBanner({ endpoint }: { endpoint: string }) {
  return (
    <Alert variant="warning" title="Preview data">
      Showing sample data because <code className="font-mono text-xs">{endpoint}</code> is not
      available yet. Live session actions still use the real API where implemented.
    </Alert>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-zinc-600" role="status" aria-live="polite">
      <span
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900"
        aria-hidden="true"
      />
      <span>{label}</span>
    </div>
  );
}
