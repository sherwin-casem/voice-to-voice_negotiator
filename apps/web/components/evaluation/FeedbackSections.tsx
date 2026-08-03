import { Card, CardDescription, CardHeading } from "@/components/ui/Card";

export function FeedbackList({
  title,
  description,
  items,
  emptyMessage,
  bare = false,
}: {
  title: string;
  description: string;
  items: string[];
  emptyMessage: string;
  bare?: boolean;
}) {
  const titleId = `${title.replace(/\s+/g, "-").toLowerCase()}-title`;

  const content =
    items.length === 0 ? (
      <p className="text-sm text-[var(--text-dim)]">{emptyMessage}</p>
    ) : (
      <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--text-muted)]">
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    );

  if (bare) {
    return content;
  }

  return (
    <Card aria-labelledby={titleId}>
      <CardHeading id={titleId}>{title}</CardHeading>
      <CardDescription>{description}</CardDescription>
      <div className="mt-4">{content}</div>
    </Card>
  );
}

export function PriorityImprovements({
  items,
  bare = false,
}: {
  items: Array<{
    area: string;
    priority: number;
    recommendation: string;
    rationale: string;
  }>;
  bare?: boolean;
}) {
  const list = (
    <ol className="space-y-4">
      {items.map((item) => (
        <li
          key={`${item.area}-${item.priority}`}
          className="rounded-xl border border-[var(--border-glass)] bg-white/5 p-4"
        >
          <p className="text-section-label">
            Priority {item.priority} · {item.area}
          </p>
          <p className="mt-2 text-sm font-medium text-[var(--text-primary)]">
            {item.recommendation}
          </p>
          <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{item.rationale}</p>
        </li>
      ))}
    </ol>
  );

  if (bare) {
    return list;
  }

  return (
    <Card aria-labelledby="priority-improvements-title">
      <CardHeading id="priority-improvements-title">Improvement priorities</CardHeading>
      <CardDescription>Ranked coaching focus areas.</CardDescription>
      <div className="mt-4">{list}</div>
    </Card>
  );
}
