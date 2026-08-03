import { Card, CardDescription, CardHeading } from "@/components/ui/Card";

export function OverallScoreCard({ score }: { score: number }) {
  return (
    <Card aria-labelledby="overall-score-title" className="gradient-border-glow">
      <CardHeading id="overall-score-title">Overall score</CardHeading>
      <CardDescription>Unified evaluation score (0–100).</CardDescription>
      <p className="mt-4 bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-5xl font-semibold tracking-tight text-transparent">
        {score}
      </p>
    </Card>
  );
}
