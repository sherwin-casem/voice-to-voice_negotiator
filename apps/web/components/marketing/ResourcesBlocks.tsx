import Link from "next/link";

export function ResourceGuideGrid({
  guides,
}: {
  guides: ReadonlyArray<{
    title: string;
    description: string;
    bullets: ReadonlyArray<string>;
  }>;
}) {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      {guides.map((guide) => (
        <article key={guide.title} className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">{guide.title}</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)]">{guide.description}</p>
          <ul className="mt-4 space-y-2 text-sm text-[var(--text-muted)]">
            {guide.bullets.map((bullet) => (
              <li key={bullet} className="flex gap-2">
                <span className="text-teal-500" aria-hidden="true">
                  •
                </span>
                {bullet}
              </li>
            ))}
          </ul>
        </article>
      ))}
    </div>
  );
}

export function ResourceTipList({
  tips,
}: {
  tips: ReadonlyArray<{ title: string; detail: string }>;
}) {
  return (
    <ul className="space-y-4">
      {tips.map((tip) => (
        <li key={tip.title} className="glass-panel p-5">
          <p className="font-medium text-[var(--text-primary)]">{tip.title}</p>
          <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{tip.detail}</p>
        </li>
      ))}
    </ul>
  );
}

export function GettingStartedChecklist({
  steps,
}: {
  steps: ReadonlyArray<{ step: string; title: string; detail: string; href: string }>;
}) {
  return (
    <ol className="space-y-4">
        {steps.map((step) => (
          <li key={step.step}>
            <Link
              href={step.href}
              className="glass-panel group flex gap-4 p-5 transition-colors hover:bg-[var(--bg-panel-hover)]"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-500/15 text-sm font-semibold text-teal-300">
                {step.step}
              </span>
              <div>
                <p className="font-medium text-[var(--text-primary)] group-hover:text-teal-300">{step.title}</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">{step.detail}</p>
              </div>
            </Link>
          </li>
        ))}
    </ol>
  );
}
