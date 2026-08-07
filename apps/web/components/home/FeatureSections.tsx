import { ButtonLink } from "@/components/ui/ButtonLink";
import { GlowArt } from "@/components/ui/GlowArt";
import { Reveal } from "@/components/visuals/Reveal";
import { TiltCard } from "@/components/visuals/TiltCard";
import { PRODUCT_FLOW, routes } from "@/lib/routes";

export function ProductFlowSection() {
  return (
    <section id="flow" className="relative scroll-mt-28 overflow-hidden border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/80">
      <GlowArt
        src="/backgrounds/multi-agent-network.png"
        width={512}
        height={512}
        sizes="(min-width: 1024px) 34rem, 0px"
        className="absolute -right-24 -top-24 hidden w-[34rem] opacity-30 lg:block"
      />
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <Reveal className="mb-10 max-w-2xl">
          <p className="text-section-label">End-to-end flow</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-4xl">
            From session creation to scored feedback in four steps.
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">
            Here is what to expect from your first session through your scored feedback report.
            Each stage builds on the last so you always know what to do next.
          </p>
        </Reveal>

        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PRODUCT_FLOW.map((step, index) => (
            <Reveal as="li" key={step.step} delayMs={index * 90}>
              <article className="glass-panel flex h-full flex-col p-5 transition-all duration-300 hover:-translate-y-1 hover:bg-[var(--bg-panel-hover)] hover:shadow-[0_12px_32px_rgba(20,184,166,0.1)]">
                <p className="text-section-label">Step {step.step}</p>
                <h3 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">{step.title}</h3>
                <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--text-muted)]">{step.detail}</p>
              </article>
            </Reveal>
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
        <Reveal className="max-w-2xl">
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
        </Reveal>
        <Reveal delayMs={120} className="hidden justify-self-center lg:block">
          <TiltCard>
            <GlowArt
              src="/backgrounds/voice-mic.png"
              width={307}
              height={512}
              sizes="(min-width: 1024px) 20rem, 0px"
              className="w-full max-w-xs animate-float-slow"
            />
          </TiltCard>
        </Reveal>
      </div>
    </section>
  );
}
