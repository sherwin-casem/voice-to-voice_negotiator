export function FeaturePillarGrid({
  pillars,
}: {
  pillars: ReadonlyArray<{
    eyebrow: string;
    title: string;
    body: string;
    bullets: ReadonlyArray<string>;
  }>;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {pillars.map((pillar) => (
        <article key={pillar.title} className="glass-panel flex flex-col p-6">
          <p className="text-section-label text-teal-400/90">{pillar.eyebrow}</p>
          <h3 className="mt-3 text-lg font-semibold text-[var(--text-primary)]">{pillar.title}</h3>
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)]">{pillar.body}</p>
          <ul className="mt-4 space-y-2 text-sm text-[var(--text-muted)]">
            {pillar.bullets.map((bullet) => (
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

export function FlowSteps({
  steps,
}: {
  steps: ReadonlyArray<{ step: string; title: string; detail: string }>;
}) {
  return (
    <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {steps.map((step) => (
        <li key={step.step}>
          <article className="glass-panel flex h-full flex-col p-5">
            <p className="text-section-label">Step {step.step}</p>
            <h3 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">{step.title}</h3>
            <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--text-muted)]">{step.detail}</p>
          </article>
        </li>
      ))}
    </ol>
  );
}

export function DimensionGrid({
  dimensions,
}: {
  dimensions: ReadonlyArray<{ name: string; description: string }>;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {dimensions.map((dimension) => (
        <article key={dimension.name} className="glass-panel p-5">
          <h3 className="font-semibold text-[var(--text-primary)]">{dimension.name}</h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{dimension.description}</p>
        </article>
      ))}
    </div>
  );
}

export function InterviewFormatGrid({
  formats,
}: {
  formats: ReadonlyArray<{ name: string; description: string }>;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {formats.map((format) => (
        <article key={format.name} className="rounded-xl border border-[var(--border-glass)] bg-white/5 p-5">
          <h3 className="font-semibold text-teal-300">{format.name}</h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{format.description}</p>
        </article>
      ))}
    </div>
  );
}

export function StatsBand({
  stats,
}: {
  stats: ReadonlyArray<{ label: string; value: string }>;
}) {
  return (
    <dl className="glass-panel grid grid-cols-3 gap-4 p-6 sm:p-8">
      {stats.map((stat) => (
        <div key={stat.label} className="text-center sm:text-left">
          <dt className="text-section-label">{stat.label}</dt>
          <dd className="mt-1 text-2xl font-semibold text-teal-300 sm:text-3xl">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function ProblemSolutionBlock({
  problem,
  solution,
}: {
  problem: string;
  solution: string;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <article className="glass-panel p-6">
        <p className="text-section-label text-amber-300/90">The gap</p>
        <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">{problem}</p>
      </article>
      <article className="glass-panel border-teal-500/20 bg-gradient-to-br from-teal-500/10 to-cyan-500/5 p-6">
        <p className="text-section-label text-teal-400/90">The VoxForge approach</p>
        <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">{solution}</p>
      </article>
    </div>
  );
}
