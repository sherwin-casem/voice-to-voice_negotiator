import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { GlowArt } from "@/components/ui/GlowArt";

export function OverallScoreCard({ score }: { score: number }) {
  return (
    <Card aria-labelledby="overall-score-title" className="gradient-border-glow relative overflow-hidden">
      <GlowArt
        src="/backgrounds/score-ring.png"
        width={512}
        height={512}
        sizes="16rem"
        className="absolute -right-16 -top-16 w-56 opacity-35"
      />
      <div className="relative">
        <CardHeading id="overall-score-title">Overall score</CardHeading>
        <CardDescription>Unified evaluation score (0–100).</CardDescription>
        <p className="mt-4 bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-5xl font-semibold tracking-tight text-transparent">
          {score}
        </p>
      </div>
    </Card>
  );
}
