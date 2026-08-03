import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function CurrentQuestion({
  question,
  sequenceNum,
}: {
  question: string | null;
  sequenceNum: number | null;
}) {
  return (
    <Card aria-labelledby="current-question-title">
      <CardTitle id="current-question-title">Current question</CardTitle>
      <CardDescription>
        {sequenceNum ? `Question ${sequenceNum}` : "Waiting for the next question"}
      </CardDescription>
      <p className="mt-4 text-base leading-7 text-zinc-900" aria-live="polite">
        {question ?? "No question yet. Start the interview to receive the first prompt."}
      </p>
    </Card>
  );
}
