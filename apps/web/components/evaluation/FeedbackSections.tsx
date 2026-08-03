import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function FeedbackList({
  title,
  description,
  items,
  emptyMessage,
}: {
  title: string;
  description: string;
  items: string[];
  emptyMessage: string;
}) {
  return (
    <Card aria-labelledby={`${title.replace(/\s+/g, "-").toLowerCase()}-title`}>
      <CardTitle id={`${title.replace(/\s+/g, "-").toLowerCase()}-title`}>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
      {items.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-500">{emptyMessage}</p>
      ) : (
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-zinc-700">
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function PriorityImprovements({
  items,
}: {
  items: Array<{
    area: string;
    priority: number;
    recommendation: string;
    rationale: string;
  }>;
}) {
  return (
    <Card aria-labelledby="priority-improvements-title">
      <CardTitle id="priority-improvements-title">Improvement priorities</CardTitle>
      <CardDescription>Ranked coaching focus areas.</CardDescription>
      <ol className="mt-4 space-y-4">
        {items.map((item) => (
          <li key={`${item.area}-${item.priority}`} className="rounded-xl border border-zinc-100 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Priority {item.priority} · {item.area}
            </p>
            <p className="mt-2 text-sm font-medium text-zinc-900">{item.recommendation}</p>
            <p className="mt-1 text-sm leading-6 text-zinc-600">{item.rationale}</p>
          </li>
        ))}
      </ol>
    </Card>
  );
}
