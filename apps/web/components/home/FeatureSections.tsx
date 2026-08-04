const FEATURES = [
  {
    id: "features",
    eyebrow: "Voice practice",
    title: "Interview the way it actually happens",
    body:
      "Speak naturally with a live AI interviewer that adapts follow-ups to your answers — behavioral, technical, system design, HR, and leadership formats.",
  },
  {
    id: "evaluation",
    eyebrow: "Multi-agent evaluation",
    title: "Feedback from every angle",
    body:
      "Separate agents score communication, technical depth, structure, confidence, and more — then a unified report highlights strengths, gaps, and better answer examples.",
  },
  {
    id: "practice",
    eyebrow: "Longitudinal coaching",
    title: "Track how your voice improves",
    body:
      "Resume and job-description aware sessions, session history, and progress trends so each practice round builds on the last.",
  },
] as const;

export function FeatureSections() {
  return (
    <div className="relative border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/90">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <div className="mb-14 max-w-2xl">
          <p className="text-section-label">Built for real preparation</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-4xl">
            From first question to final score — entirely by voice.
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {FEATURES.map((feature) => (
            <article
              key={feature.id}
              id={feature.id}
              className="glass-panel scroll-mt-28 p-6 transition-colors hover:bg-[var(--bg-panel-hover)]"
            >
              <p className="text-section-label text-teal-400/90">{feature.eyebrow}</p>
              <h3 className="mt-3 text-lg font-semibold text-[var(--text-primary)]">{feature.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)]">{feature.body}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
