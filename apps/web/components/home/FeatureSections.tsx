"use client";

import dynamic from "next/dynamic";

import { ButtonLink } from "@/components/ui/ButtonLink";
import { GlowArt } from "@/components/ui/GlowArt";
import { Reveal } from "@/components/visuals/Reveal";
import { PRODUCT_FLOW, routes } from "@/lib/routes";

const FeatureWaveScene = dynamic(
  () => import("@/components/home/FeatureWaveScene").then((mod) => mod.FeatureWaveScene),
  { ssr: false },
);

export function ProductFlowSection() {
  return (
    <section id="flow" className="relative scroll-mt-28 overflow-hidden border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/90">
      <GlowArt
        src="/backgrounds/multi-agent-network.png"
        width={512}
        height={512}
        sizes="(min-width: 1024px) 34rem, 0px"
        className="absolute -right-24 -top-24 hidden w-[34rem] opacity-25 lg:block"
      />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(20,184,166,0.08),transparent_70%)]" />

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

        <ol className="relative grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Animated connector line (desktop) */}
          <div
            aria-hidden
            className="pointer-events-none absolute left-[12.5%] right-[12.5%] top-1/2 hidden h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-teal-500/40 to-transparent lg:block"
          />

          {PRODUCT_FLOW.map((step, index) => (
            <Reveal as="li" key={step.step} delayMs={index * 90}>
              <article className="glass-panel group relative flex h-full flex-col overflow-hidden p-5 transition-all duration-300 hover:-translate-y-1 hover:border-teal-500/20 hover:bg-[var(--bg-panel-hover)] hover:shadow-[0_12px_32px_rgba(20,184,166,0.12)]">
                <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-teal-500/10 blur-2xl transition-opacity group-hover:opacity-100" />
                <div className="relative mb-3 flex h-9 w-9 items-center justify-center rounded-full border border-teal-500/30 bg-teal-500/10 text-sm font-semibold text-teal-300 shadow-[0_0_16px_rgba(20,184,166,0.2)]">
                  {step.step}
                </div>
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
    <section className="relative scroll-mt-28 overflow-hidden border-t border-[var(--border-glass)] bg-[var(--bg-deep)]">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_60%_at_80%_50%,rgba(34,211,238,0.08),transparent_70%)]" />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 sm:py-24 lg:grid-cols-2">
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

        <Reveal delayMs={120} className="flex justify-center lg:justify-end">
          <div className="relative">
            <div className="absolute -inset-6 rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.12),transparent_70%)] blur-xl" />
            <FeatureWaveScene />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
