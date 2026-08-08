"use client";

import dynamic from "next/dynamic";

import { AuthEntryButtonLink, AuthEntryLink } from "@/components/auth/AuthEntryLink";
import { HeroCinematicBackdrop } from "@/components/home/HeroCinematicBackdrop";
import { HashLink } from "@/components/navigation/HashLink";
import { Reveal } from "@/components/visuals/Reveal";
import { cn } from "@/lib/format";
import { routes } from "@/lib/routes";

const HeroInterviewScene = dynamic(
  () => import("@/components/home/HeroInterviewScene").then((mod) => mod.HeroInterviewScene),
  { ssr: false },
);

const STATS = [
  { label: "Interview types", value: "5+", href: routes.createInterview },
  { label: "Eval dimensions", value: "7", href: routes.previewResults },
  { label: "Voice-first", value: "100%", href: routes.createInterview },
] as const;

export function LandingHero() {
  return (
    <section className="relative min-h-[100svh] overflow-hidden">
      <HeroCinematicBackdrop />

      <div className="relative mx-auto flex w-full max-w-7xl flex-col px-4 pb-16 pt-28 sm:px-6 lg:min-h-[100svh] lg:justify-center lg:pb-24 lg:pt-32">
        {/* Mobile / tablet: 3D focal art first */}
        <Reveal className="mx-auto mb-10 w-full max-w-lg lg:hidden">
          <HeroInterviewScene className="h-[clamp(260px,42vw,360px)]" />
        </Reveal>

        <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-14">
          <div className="relative z-10 max-w-2xl">
            <Reveal>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-500/10 px-3.5 py-1.5 text-xs font-medium text-teal-300 shadow-[0_0_24px_rgba(20,184,166,0.15)]">
                <span
                  aria-hidden
                  className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-teal-400 shadow-[0_0_8px_#14b8a6]"
                />
                AI voice interview studio
              </div>

              <h1 className="text-4xl font-semibold leading-[1.06] tracking-tight text-[var(--text-primary)] sm:text-5xl lg:text-[3.35rem] lg:leading-[1.05]">
                Most prep tools score what you{" "}
                <span className="hero-text-shimmer text-teal-300">write</span>. We coach how you{" "}
                <span className="hero-text-shimmer-cyan text-cyan-300">speak</span>.
              </h1>

              <p className="mt-6 max-w-xl text-base leading-relaxed text-[var(--text-muted)] sm:text-lg">
                Realistic voice-to-voice mock interviews with a dynamic AI interviewer, multi-agent
                evaluation across seven dimensions, and coaching that tracks your progress over time.
              </p>
            </Reveal>

            <Reveal delayMs={120}>
              <div className="mt-9 flex flex-wrap items-center gap-3">
                <AuthEntryButtonLink
                  href={routes.createInterview}
                  className="px-6 py-3 text-sm shadow-[0_0_32px_rgba(20,184,166,0.25)]"
                >
                  Get started →
                </AuthEntryButtonLink>
                <HashLink
                  section="flow"
                  href={routes.homeSection("flow")}
                  className={cn(
                    "inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-medium transition-all",
                    "border border-[var(--border-glass-strong)] bg-[var(--bg-panel)] text-[var(--text-primary)] hover:bg-[var(--bg-panel-hover)]",
                    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500",
                  )}
                >
                  See how it works
                </HashLink>
              </div>
            </Reveal>

            <Reveal delayMs={220}>
              <dl className="mt-12 grid grid-cols-3 gap-3 sm:gap-4">
                {STATS.map((stat) => (
                  <div
                    key={stat.label}
                    className="glass-panel group p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-teal-500/25 hover:shadow-[0_8px_28px_rgba(20,184,166,0.12)]"
                  >
                    <dt className="text-section-label">{stat.label}</dt>
                    <dd className="mt-2">
                      <AuthEntryLink
                        href={stat.href}
                        className="text-2xl font-semibold text-teal-300 transition-colors group-hover:text-cyan-300"
                      >
                        {stat.value}
                      </AuthEntryLink>
                    </dd>
                  </div>
                ))}
              </dl>
            </Reveal>
          </div>

          <Reveal delayMs={150} className="relative hidden lg:block">
            <div className="relative">
              <div className="absolute -inset-8 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.18),transparent_70%)] blur-2xl" />
              <HeroInterviewScene className="h-[clamp(420px,52vh,580px)]" />
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
