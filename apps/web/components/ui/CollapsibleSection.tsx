"use client";

import { cn } from "@/lib/format";

export function CollapsibleSection({
  title,
  description,
  defaultOpen = true,
  children,
  className,
}: {
  title: string;
  description?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <details
      open={defaultOpen}
      className={cn(
        "group rounded-xl border border-[var(--border-glass)] bg-white/5",
        className,
      )}
    >
      <summary className="cursor-pointer list-none px-5 py-4 marker:content-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">{title}</h2>
            {description ? (
              <p className="mt-1 text-sm text-[var(--text-muted)]">{description}</p>
            ) : null}
          </div>
          <span
            className="mt-1 text-xs text-[var(--text-dim)] transition-transform group-open:rotate-180"
            aria-hidden="true"
          >
            ▼
          </span>
        </div>
      </summary>
      <div className="border-t border-[var(--border-glass)] px-5 py-4">{children}</div>
    </details>
  );
}
