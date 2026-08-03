import type { InterviewType } from "@voice/shared";

import { cn } from "@/lib/format";

export type InterviewStage = "intro" | "technical" | "behavioral" | "feedback";

const STAGES: { id: InterviewStage; label: string }[] = [
  { id: "intro", label: "Intro" },
  { id: "technical", label: "Technical" },
  { id: "behavioral", label: "Behavioral" },
  { id: "feedback", label: "Feedback" },
];

function resolveActiveStage(
  current: InterviewStage,
  interviewType: InterviewType | undefined,
  isStarted: boolean,
  isEnded: boolean,
): InterviewStage {
  if (isEnded) {
    return "feedback";
  }
  if (!isStarted) {
    return "intro";
  }
  if (current !== "intro") {
    return current;
  }
  if (interviewType === "technical" || interviewType === "system_design") {
    return "technical";
  }
  return "behavioral";
}

export function StageStepper({
  interviewType,
  isStarted,
  isEnded,
  className,
}: {
  interviewType?: InterviewType;
  isStarted: boolean;
  isEnded: boolean;
  className?: string;
}) {
  const active = resolveActiveStage("intro", interviewType, isStarted, isEnded);
  const activeIndex = STAGES.findIndex((s) => s.id === active);

  return (
    <nav
      aria-label="Interview progress"
      className={cn("flex flex-wrap items-center gap-1 sm:gap-2", className)}
    >
      {STAGES.map((stage, index) => {
        const isActive = stage.id === active;
        const isPast = index < activeIndex;
        return (
          <span key={stage.id} className="flex items-center gap-1 sm:gap-2">
            {index > 0 ? (
              <span className="text-[var(--text-dim)]" aria-hidden="true">
                →
              </span>
            ) : null}
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-xs font-medium transition-colors sm:px-3",
                isActive
                  ? "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/40"
                  : isPast
                    ? "text-[var(--text-muted)]"
                    : "text-[var(--text-dim)]",
              )}
              aria-current={isActive ? "step" : undefined}
            >
              {stage.label}
            </span>
          </span>
        );
      })}
    </nav>
  );
}
