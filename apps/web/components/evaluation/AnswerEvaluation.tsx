import { Card, CardDescription, CardHeading } from "@/components/ui/Card";

const articleClass =
  "rounded-xl border border-[var(--border-glass)] bg-white/5 p-4";

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
      <CardHeading id="answer-evaluation-title">Detailed answer evaluation</CardHeading>
      <CardDescription>Per-question feedback from the evaluation pipeline.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item, index) => (
          <article key={`${item.question}-${index}`} className={articleClass}>
            <header className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="text-sm font-medium text-[var(--text-primary)]">{item.question}</h3>
              <span className="rounded-full bg-teal-500/20 px-2 py-0.5 text-xs font-medium text-teal-300">
                Score {item.score}
              </span>
            </header>
            <p className="mt-2 text-sm italic text-[var(--text-muted)]">
              &ldquo;{item.answer_excerpt}&rdquo;
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{item.feedback}</p>
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
      <CardHeading id="better-answers-title">AI-recommended better answers</CardHeading>
      <CardDescription>Example responses aligned with coaching guidance.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item, index) => (
          <article key={`${item.question}-${index}`} className={articleClass}>
            <h3 className="text-sm font-medium text-[var(--text-primary)]">{item.question}</h3>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{item.example}</p>
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
      <CardHeading id="practice-recommendations-title">Practice recommendations</CardHeading>
      <CardDescription>Actionable drills for your next session.</CardDescription>
      <div className="mt-4 space-y-4">
        {items.map((item) => (
          <article key={item.title} className={articleClass}>
            <h3 className="text-sm font-medium text-[var(--text-primary)]">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{item.instructions}</p>
            <p className="text-section-label mt-3">Success criteria</p>
            <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{item.success_criteria}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}
