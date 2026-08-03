import { formatDuration } from "@/lib/format";
import { cn } from "@/lib/format";

export function CountdownTimer({
  elapsedSeconds,
  targetMinutes,
  className,
}: {
  elapsedSeconds: number;
  targetMinutes?: number | null;
  className?: string;
}) {
  const targetSeconds = targetMinutes ? targetMinutes * 60 : null;
  const remaining =
    targetSeconds !== null ? Math.max(0, targetSeconds - elapsedSeconds) : elapsedSeconds;
  const label = targetSeconds !== null ? "Time Remaining" : "Elapsed Time";
  const displaySeconds = targetSeconds !== null ? remaining : elapsedSeconds;

  return (
    <div className={cn("text-center", className)}>
      <p className="text-section-label mb-2">{label}</p>
      <p
        className="font-mono text-4xl font-semibold tracking-wider text-[var(--text-primary)] sm:text-5xl"
        aria-live="polite"
      >
        <time dateTime={`PT${displaySeconds}S`}>{formatDuration(displaySeconds)}</time>
      </p>
    </div>
  );
}
