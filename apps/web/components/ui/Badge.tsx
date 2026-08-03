import type { InterviewSessionStatus } from "@voice/shared";
import { SESSION_STATUS_LABELS } from "@voice/shared";

import { cn } from "@/lib/format";

const STATUS_STYLES: Record<InterviewSessionStatus, string> = {
  created: "bg-white/10 text-[var(--text-muted)]",
  configured: "bg-cyan-500/15 text-cyan-300",
  active: "bg-teal-500/20 text-teal-300",
  completing: "bg-amber-500/15 text-amber-300",
  completed: "bg-emerald-500/20 text-emerald-300",
  abandoned: "bg-red-500/15 text-red-300",
  evaluation_failed: "bg-red-500/20 text-red-300",
};

export function Badge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function SessionStatusBadge({ status }: { status: InterviewSessionStatus }) {
  return <Badge className={STATUS_STYLES[status]}>{SESSION_STATUS_LABELS[status]}</Badge>;
}

export function PracticeModeBadge() {
  return (
    <Badge className="gap-1.5 border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-teal-300">
      <span className="h-1.5 w-1.5 rounded-full bg-teal-400" aria-hidden="true" />
      Practice Mode
    </Badge>
  );
}
