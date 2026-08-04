"use client";

import Link from "next/link";

import { cn } from "@/lib/format";

export type FunnelStep = "create" | "setup" | "live" | "results";

const FUNNEL_STEPS: { id: FunnelStep; label: string; path: (sessionId?: string) => string }[] = [
  { id: "create", label: "Create", path: () => "/interviews/new" },
  { id: "setup", label: "Setup", path: (id) => `/interviews/${id}/setup` },
  { id: "live", label: "Live", path: (id) => `/interviews/${id}/live` },
  { id: "results", label: "Results", path: (id) => `/interviews/${id}/results` },
];

export function InterviewFunnelStepper({
  current,
  sessionId,
  className,
}: {
  current: FunnelStep;
  sessionId?: string;
  className?: string;
}) {
  const currentIndex = FUNNEL_STEPS.findIndex((step) => step.id === current);

  return (
    <nav
      aria-label="Interview setup progress"
      className={cn("flex flex-wrap items-center gap-2 sm:gap-3", className)}
    >
      {FUNNEL_STEPS.map((step, index) => {
        const isCurrent = step.id === current;
        const isPast = index < currentIndex;
        const isFuture = index > currentIndex;
        const href = step.path(sessionId);
        const canLink = isPast && (step.id === "create" || Boolean(sessionId));

        const stepClass = cn(
          "rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors sm:px-4",
          isCurrent
            ? "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/40"
            : isPast
              ? "text-[var(--text-muted)] hover:text-teal-300"
              : "text-[var(--text-dim)]",
        );

        return (
          <span key={step.id} className="flex items-center gap-2 sm:gap-3">
            {index > 0 ? (
              <span className="text-sm text-[var(--text-muted)]" aria-hidden="true">
                →
              </span>
            ) : null}
            {canLink ? (
              <Link href={href} className={stepClass} aria-current={isCurrent ? "step" : undefined}>
                {step.label}
              </Link>
            ) : (
              <span
                className={cn(stepClass, isFuture && "cursor-default")}
                aria-current={isCurrent ? "step" : undefined}
              >
                {step.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
