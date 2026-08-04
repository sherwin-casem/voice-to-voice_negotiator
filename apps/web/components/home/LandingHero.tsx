import { ButtonLink } from "@/components/ui/ButtonLink";

export function LandingHero() {
  return (
    <section className="relative flex min-h-[92vh] flex-col justify-center px-4 pb-20 pt-28 sm:px-6">
      <div className="mx-auto w-full max-w-3xl">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-teal-500/25 bg-teal-500/10 px-3 py-1.5 text-xs font-medium text-teal-300">
          <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-teal-400 shadow-[0_0_8px_#14b8a6]" />
          AI voice interview studio
        </div>

        <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight text-[var(--text-primary)] sm:text-5xl lg:text-6xl">
          Most prep tools score what you{" "}
          <em className="bg-gradient-to-r from-teal-300 to-cyan-300 bg-clip-text font-[family-name:var(--font-instrument-serif)] not-italic text-transparent">
            write
          </em>
          . We coach how you{" "}
          <em className="bg-gradient-to-r from-cyan-300 to-teal-200 bg-clip-text font-[family-name:var(--font-instrument-serif)] not-italic text-transparent">
            speak
          </em>
          .
        </h1>

        <p className="mt-6 max-w-xl text-base leading-relaxed text-[var(--text-muted)] sm:text-lg">
          Realistic voice-to-voice mock interviews with a dynamic AI interviewer, multi-agent
          evaluation across seven dimensions, and coaching that tracks your progress over time.
        </p>

        <div className="mt-9 flex flex-wrap items-center gap-3">
          <ButtonLink href="/interviews/new" className="px-6 py-2.5 text-sm">
            Start practicing →
          </ButtonLink>
          <ButtonLink href="#features" variant="secondary" className="px-6 py-2.5 text-sm">
            See how it works
          </ButtonLink>
        </div>

        <dl className="mt-14 grid max-w-lg grid-cols-3 gap-4 border-t border-[var(--border-glass)] pt-8">
          <div>
            <dt className="text-section-label">Interview types</dt>
            <dd className="mt-1 text-2xl font-semibold text-teal-300">5+</dd>
          </div>
          <div>
            <dt className="text-section-label">Eval dimensions</dt>
            <dd className="mt-1 text-2xl font-semibold text-teal-300">7</dd>
          </div>
          <div>
            <dt className="text-section-label">Voice-first</dt>
            <dd className="mt-1 text-2xl font-semibold text-teal-300">100%</dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
