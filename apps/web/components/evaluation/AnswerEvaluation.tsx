import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function AnswerEvaluationList({
  items,
}: {
  items: Array<{
    question: string;
    answer_excerpt: string;
    feedback: string;
    score: number;
  }>;
}) {
  return (
    <Card aria-labelledby="answer-evaluation-title">
      <CardTitle id="answer-evaluation-title">Detailed answer evaluation</CardTitle>
      <CardDescription>Per-question feedback from the evaluation pipeline.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item, index) => (
          <article key={`${item.question}-${index}`} className="rounded-xl border border-zinc-100 p-4">
            <header className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="text-sm font-medium text-zinc-900">{item.question}</h3>
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700">
                Score {item.score}
              </span>
            </header>
            <p className="mt-2 text-sm italic text-zinc-600">&ldquo;{item.answer_excerpt}&rdquo;</p>
            <p className="mt-2 text-sm leading-6 text-zinc-700">{item.feedback}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

export function BetterAnswersList({
  items,
}: {
  items: Array<{ question: string; example: string }>;
}) {
  return (
    <Card aria-labelledby="better-answers-title">
      <CardTitle id="better-answers-title">AI-recommended better answers</CardTitle>
      <CardDescription>Example responses aligned with coaching guidance.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item, index) => (
          <article key={`${item.question}-${index}`} className="rounded-xl border border-zinc-100 p-4">
            <h3 className="text-sm font-medium text-zinc-900">{item.question}</h3>
            <p className="mt-2 text-sm leading-6 text-zinc-700">{item.example}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

export function PracticeRecommendations({
  items,
}: {
  items: Array<{ title: string; instructions: string; success_criteria: string }>;
}) {
  return (
    <Card aria-labelledby="practice-recommendations-title">
      <CardTitle id="practice-recommendations-title">Practice recommendations</CardTitle>
      <CardDescription>Actionable drills for your next session.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item) => (
          <article key={item.title} className="rounded-xl border border-zinc-100 p-4">
            <h3 className="text-sm font-medium text-zinc-900">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-zinc-700">{item.instructions}</p>
            <p className="mt-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
              Success criteria
            </p>
            <p className="mt-1 text-sm leading-6 text-zinc-700">{item.success_criteria}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}
