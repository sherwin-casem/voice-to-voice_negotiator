"use client";

import { AuthEntryButtonLink, AuthEntryLink } from "@/components/auth/AuthEntryLink";
import { HashLink } from "@/components/navigation/HashLink";
import { GlowArt } from "@/components/ui/GlowArt";
import { cn } from "@/lib/format";
import { routes } from "@/lib/routes";

export function LandingHero() {
  return (
    <section className="relative flex min-h-[92vh] flex-col justify-center px-4 pb-20 pt-28 sm:px-6">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1fr_34rem]">
        <div className="w-full max-w-3xl">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-teal-500/25 bg-teal-500/10 px-3 py-1.5 text-xs font-medium text-teal-300">
          <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-teal-400 shadow-[0_0_8px_#14b8a6]" />
          AI voice interview studio
        </div>

        <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight text-[var(--text-primary)] sm:text-5xl lg:text-6xl">
          Most prep tools score what you{" "}
          <span className="text-teal-300">write</span>. We coach how you{" "}
          <span className="text-cyan-300">speak</span>.
        </h1>

        <p className="mt-6 max-w-xl text-base leading-relaxed text-[var(--text-muted)] sm:text-lg">
          Realistic voice-to-voice mock interviews with a dynamic AI interviewer, multi-agent
          evaluation across seven dimensions, and coaching that tracks your progress over time.
        </p>

        <div className="mt-9 flex flex-wrap items-center gap-3">
          <AuthEntryButtonLink href={routes.createInterview} className="px-6 py-2.5 text-sm">
            Get started →
          </AuthEntryButtonLink>
          <HashLink
            section="flow"
            href={routes.homeSection("flow")}
            className={cn(
              "inline-flex items-center justify-center rounded-full px-6 py-2.5 text-sm font-medium transition-all",
              "border border-[var(--border-glass-strong)] bg-[var(--bg-panel)] text-[var(--text-primary)] hover:bg-[var(--bg-panel-hover)]",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500",
            )}
          >
            See how it works
          </HashLink>
        </div>

        <dl className="mt-14 grid max-w-lg grid-cols-3 gap-4 border-t border-[var(--border-glass)] pt-8">
          <div>
            <dt className="text-section-label">Interview types</dt>
            <dd className="mt-1">
              <AuthEntryLink href={routes.createInterview} className="text-2xl font-semibold text-teal-300 hover:text-teal-200">
                5+
              </AuthEntryLink>
            </dd>
          </div>
          <div>
            <dt className="text-section-label">Eval dimensions</dt>
            <dd className="mt-1">
              <AuthEntryLink href={routes.previewResults} className="text-2xl font-semibold text-teal-300 hover:text-teal-200">
                7
              </AuthEntryLink>
            </dd>
          </div>
          <div>
            <dt className="text-section-label">Voice-first</dt>
            <dd className="mt-1">
              <AuthEntryLink href={routes.createInterview} className="text-2xl font-semibold text-teal-300 hover:text-teal-200">
                100%
              </AuthEntryLink>
            </dd>
          </div>
        </dl>
        </div>

        <GlowArt
          src="/backgrounds/ai-core-hero.png"
          width={1024}
          height={721}
          sizes="(min-width: 1024px) 34rem, 0px"
          masked={false}
          className="hidden w-full scale-110 justify-self-center lg:block [filter:brightness(0.88)_contrast(1.3)] [mask-image:radial-gradient(ellipse_62%_62%_at_50%_50%,#000_38%,transparent_80%)]"
        />
      </div>
    </section>
  );
}
