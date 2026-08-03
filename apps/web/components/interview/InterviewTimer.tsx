import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { formatDuration } from "@/lib/format";

export function InterviewTimer({ elapsedSeconds }: { elapsedSeconds: number }) {
  return (
    <Card aria-labelledby="interview-timer-title">
      <CardTitle id="interview-timer-title">Interview timer</CardTitle>
      <CardDescription>Elapsed time since the session started.</CardDescription>
      <p className="mt-4 font-mono text-3xl font-semibold tracking-tight text-zinc-900">
        <time dateTime={`PT${elapsedSeconds}S`}>{formatDuration(elapsedSeconds)}</time>
      </p>
    </Card>
  );
}
