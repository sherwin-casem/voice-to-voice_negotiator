import type { InterviewSessionStatus } from "@voice/shared";
import { SESSION_STATUS_LABELS } from "@voice/shared";

import { cn } from "@/lib/format";

const STATUS_STYLES: Record<InterviewSessionStatus, string> = {
  created: "bg-zinc-100 text-zinc-700",
  configured: "bg-blue-50 text-blue-700",
  active: "bg-emerald-50 text-emerald-700",
  completing: "bg-amber-50 text-amber-700",
  completed: "bg-emerald-100 text-emerald-800",
  abandoned: "bg-red-50 text-red-700",
  evaluation_failed: "bg-red-100 text-red-800",
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
