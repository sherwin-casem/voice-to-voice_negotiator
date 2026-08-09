import { GlassPanel } from "@/components/ui/GlassPanel";
import { formatDuration, cn } from "@/lib/format";

export function CountdownTimer({
  elapsedSeconds,
  targetMinutes,
  className,
  running = false,
}: {
  elapsedSeconds: number;
  targetMinutes?: number | null;
  className?: string;
  running?: boolean;
}) {
  const targetSeconds = targetMinutes ? targetMinutes * 60 : null;
  const remaining =
    targetSeconds !== null ? Math.max(0, targetSeconds - elapsedSeconds) : elapsedSeconds;
  const label = targetSeconds !== null ? "Time remaining" : "Elapsed time";
  const displaySeconds = targetSeconds !== null ? remaining : elapsedSeconds;
  const nearlyDone =
    targetSeconds !== null && remaining > 0 && remaining <= Math.min(60, targetSeconds * 0.1);

  return (
    <div className={cn("text-center", className)}>
      <p className="text-section-label mb-3">{label}</p>
      <p
        className={cn(
          "font-mono text-4xl font-semibold tracking-wider sm:text-5xl",
          nearlyDone ? "text-amber-300" : "text-[var(--text-primary)]",
          running && !nearlyDone && "text-teal-100",
        )}
        aria-live="polite"
      >
        <time dateTime={`PT${displaySeconds}S`}>{formatDuration(displaySeconds)}</time>
      </p>
      {targetMinutes ? (
        <p className="mt-2 text-xs text-[var(--text-dim)]">Target {targetMinutes} min</p>
      ) : (
        <p className="mt-2 text-xs text-[var(--text-dim)]">
          {running ? "Interview in progress" : "Timer starts when you begin"}
        </p>
      )}
    </div>
  );
}
