import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function OverallScoreCard({ score }: { score: number }) {
  return (
    <Card aria-labelledby="overall-score-title">
      <CardTitle id="overall-score-title">Overall score</CardTitle>
      <CardDescription>Unified evaluation score (0–100).</CardDescription>
      <p className="mt-4 text-5xl font-semibold tracking-tight text-zinc-900">{score}</p>
    </Card>
  );
}
