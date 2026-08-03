import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { MetricBar } from "@/components/ui/MetricBar";

interface DimensionScoresProps {
  scores: Record<string, number | null>;
}

function formatLabel(key: string): string {
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function DimensionScores({ scores, bare = false }: DimensionScoresProps & { bare?: boolean }) {
  const list = (
    <ul className="space-y-4">
      {Object.entries(scores).map(([key, value]) => (
        <li key={key}>
          {value !== null ? (
            <MetricBar label={formatLabel(key)} value={`${value}%`} percent={value} />
          ) : (
            <div>
              <p className="text-sm text-[var(--text-muted)]">{formatLabel(key)}</p>
              <p className="text-xs text-[var(--text-dim)]">
                Not applicable for this interview type.
              </p>
            </div>
          )}
        </li>
      ))}
    </ul>
  );

  if (bare) {
    return list;
  }

  return (
    <Card aria-labelledby="dimension-scores-title">
      <CardHeading id="dimension-scores-title">Dimension scores</CardHeading>
      <CardDescription>Breakdown across evaluation dimensions.</CardDescription>
      <div className="mt-4">{list}</div>
    </Card>
  );
}
