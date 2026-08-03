import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

interface DimensionScoresProps {
  scores: Record<string, number | null>;
}

function formatLabel(key: string): string {
  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function DimensionScores({ scores }: DimensionScoresProps) {
  return (
    <Card aria-labelledby="dimension-scores-title">
      <CardTitle id="dimension-scores-title">Dimension scores</CardTitle>
      <CardDescription>Breakdown across evaluation dimensions.</CardDescription>
      <ul className="mt-4 space-y-3">
        {Object.entries(scores).map(([key, value]) => (
          <li key={key}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="text-zinc-700">{formatLabel(key)}</span>
              <span className="font-medium text-zinc-900">{value ?? "N/A"}</span>
            </div>
            {value !== null ? (
              <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
                <div
                  className="h-full rounded-full bg-zinc-900"
                  style={{ width: `${value}%` }}
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={value}
                  aria-label={`${formatLabel(key)} score`}
                />
              </div>
            ) : (
              <p className="text-xs text-zinc-500">Not applicable for this interview type.</p>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
