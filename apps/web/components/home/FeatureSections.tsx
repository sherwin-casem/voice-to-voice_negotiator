import { ButtonLink } from "@/components/ui/ButtonLink";
import { GlowArt } from "@/components/ui/GlowArt";
import { PRODUCT_FLOW, routes } from "@/lib/routes";

export function ProductFlowSection() {
  return (
    <section id="flow" className="relative scroll-mt-28 border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/80">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="mb-10 max-w-2xl">
          <p className="text-section-label">End-to-end flow</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-4xl">
            From session creation to scored feedback in four steps.
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">
            Here is what to expect from your first session through your scored feedback report.
            Each stage builds on the last so you always know what to do next.
          </p>
        </div>

        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PRODUCT_FLOW.map((step) => (
            <li key={step.step}>
              <article className="glass-panel flex h-full flex-col p-5">
                <p className="text-section-label">Step {step.step}</p>
                <h3 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">{step.title}</h3>
                <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--text-muted)]">{step.detail}</p>
              </article>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function FeatureSectionsTeaser() {
  return (
    <section className="relative scroll-mt-28 border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/90">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 sm:py-24 lg:grid-cols-2">
        <div className="max-w-2xl">
          <p className="text-section-label">Built for real preparation</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-4xl">
            From first question to final score — entirely by voice.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">
            Voice practice, multi-agent evaluation, and longitudinal coaching — everything you need
            to prepare for real interview conversations, not just written flashcards.
          </p>
          <div className="mt-8">
            <ButtonLink href={routes.features} variant="secondary" className="px-6 py-2.5">
              Explore all features →
            </ButtonLink>
          </div>
        </div>
        <GlowArt
          src="/backgrounds/voice-mic.png"
          width={307}
          height={512}
          sizes="(min-width: 1024px) 20rem, 0px"
          className="hidden w-full max-w-xs justify-self-center lg:block"
        />
      </div>
    </section>
  );
}
