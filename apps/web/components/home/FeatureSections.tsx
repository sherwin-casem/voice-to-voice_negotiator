import Link from "next/link";

import { ButtonLink } from "@/components/ui/ButtonLink";
import { FEATURE_CARDS, PRODUCT_FLOW, routes } from "@/lib/routes";

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
            Every step below opens the real app experience — start a session, configure your
            interview, practice live, or explore a sample evaluation report.
          </p>
        </div>

        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PRODUCT_FLOW.map((step) => (
            <li key={step.step}>
              <Link
                href={step.href}
                className="group glass-panel flex h-full flex-col p-5 transition-colors hover:bg-[var(--bg-panel-hover)]"
              >
                <p className="text-section-label">Step {step.step}</p>
                <h3 className="mt-2 text-lg font-semibold text-[var(--text-primary)] group-hover:text-teal-300">
                  {step.title}
                </h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-[var(--text-muted)]">{step.detail}</p>
                <span className="mt-4 text-sm font-medium text-teal-400 group-hover:text-teal-300">
                  Open →
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

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
          {FEATURE_CARDS.map((feature) => (
            <article
              key={feature.id}
              id={feature.id}
              className="glass-panel scroll-mt-28 flex flex-col p-6 transition-colors hover:bg-[var(--bg-panel-hover)]"
            >
              <p className="text-section-label text-teal-400/90">{feature.eyebrow}</p>
              <h3 className="mt-3 text-lg font-semibold text-[var(--text-primary)]">{feature.title}</h3>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--text-muted)]">{feature.body}</p>
              <ButtonLink href={feature.href} variant="secondary" className="mt-6 w-full justify-center py-2">
                {feature.cta} →
              </ButtonLink>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
