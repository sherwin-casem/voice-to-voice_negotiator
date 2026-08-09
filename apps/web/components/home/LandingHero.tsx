"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

import { AuthEntryButtonLink } from "@/components/auth/AuthEntryLink";
import { HeroInterviewScene } from "@/components/home/HeroInterviewScene";
import { HashLink } from "@/components/navigation/HashLink";
import { MotionItem, MotionStagger } from "@/components/visuals/Reveal";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { cn } from "@/lib/format";
import { routes } from "@/lib/routes";

/**
 * Immersive landing hero — nebula atmosphere + neural brain,
 * with Framer Motion entrance stagger.
 */
export function LandingHero() {
  const reduceMotion = usePrefersReducedMotion();
  const [enter, setEnter] = useState(false);

  useEffect(() => {
    setEnter(true);
  }, []);

  const sceneReady = enter || reduceMotion;

  return (
    <section className="relative min-h-[100svh] overflow-hidden">
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <Image
          src="/backgrounds/landing-nebula-bg.png"
          alt=""
          fill
          priority
          unoptimized
          sizes="100vw"
          className="object-cover object-center opacity-90"
        />
        <div className="absolute inset-0 bg-[#050b16]/55" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#050b16] via-[#050b16]/75 to-transparent lg:via-[#050b16]/40" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[var(--bg-deep)] to-transparent" />
      </div>

      <motion.div
        className="pointer-events-none absolute -right-[8%] top-[12%] hidden h-[78%] w-[58%] lg:block xl:-right-[4%] xl:w-[52%]"
        aria-hidden
        initial={false}
        animate={
          sceneReady
            ? { opacity: 1, x: 0, scale: 1 }
            : { opacity: 0, x: 48, scale: 0.96 }
        }
        transition={{
          duration: reduceMotion ? 0 : 0.9,
          ease: [0.22, 1, 0.36, 1],
          delay: reduceMotion ? 0 : 0.15,
        }}
      >
        <HeroInterviewScene />
      </motion.div>

      <div
        aria-hidden
        className="pointer-events-none absolute -left-20 top-1/3 hidden h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.12),transparent_70%)] blur-2xl lg:block"
      />

      <div className="relative mx-auto flex min-h-[100svh] w-full max-w-7xl flex-col justify-center px-4 pb-20 pt-28 sm:px-6">
        <motion.div
          className="relative mx-auto mb-8 h-56 w-full max-w-sm lg:hidden"
          initial={false}
          animate={sceneReady ? { opacity: 1, y: 0 } : { opacity: 0, y: 16 }}
          transition={{ duration: reduceMotion ? 0 : 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <HeroInterviewScene />
        </motion.div>

        <MotionStagger className="relative z-10 max-w-xl lg:max-w-2xl">
          <MotionItem className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-teal-200/90 backdrop-blur-md">
            <span
              aria-hidden
              className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-teal-400 shadow-[0_0_8px_#14b8a6]"
            />
            AI voice interview studio
          </MotionItem>

          <MotionItem>
            <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-[3.4rem] lg:leading-[1.06]">
              Most prep tools score what you{" "}
              <span className="font-serif text-[1.08em] italic font-normal text-teal-300">
                write
              </span>
              . We coach how you{" "}
              <span className="bg-gradient-to-r from-teal-300 to-cyan-300 bg-clip-text font-serif text-[1.08em] italic font-normal text-transparent">
                speak
              </span>
              .
            </h1>
          </MotionItem>

          <MotionItem>
            <p className="mt-6 max-w-lg text-base leading-relaxed text-slate-300/90 sm:text-lg">
              Realistic voice-to-voice mock interviews with a dynamic AI interviewer, multi-agent
              evaluation across seven dimensions, and coaching that tracks your progress over time.
            </p>
          </MotionItem>

          <MotionItem className="mt-9 flex flex-wrap items-center gap-3">
            <AuthEntryButtonLink
              href={routes.createInterview}
              className="px-7 py-3 text-sm shadow-[0_0_40px_rgba(20,184,166,0.35)]"
            >
              Get started →
            </AuthEntryButtonLink>
            <HashLink
              section="flow"
              href={routes.homeSection("flow")}
              className={cn(
                "inline-flex items-center justify-center rounded-full px-7 py-3 text-sm font-medium transition-all",
                "border border-white/15 bg-white/5 text-white backdrop-blur-sm hover:bg-white/10",
                "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500",
              )}
            >
              See how it works
            </HashLink>
          </MotionItem>
        </MotionStagger>
      </div>
    </section>
  );
}
