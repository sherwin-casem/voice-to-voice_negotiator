"use client";

import Image from "next/image";

import { cn } from "@/lib/format";

/**
 * Resources hero art — glass cubes must stay visibly opaque.
 * No Reveal wrapper, no aggressive mask, no ambient-only placeholder.
 */
export function ResourcesHeroArt({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative flex h-[min(28rem,55vh)] w-[min(20rem,32vw)] items-center justify-center",
        className,
      )}
      aria-hidden
    >
      <div className="pointer-events-none absolute inset-[12%] rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.25),transparent_70%)] blur-3xl" />

      <Image
        src="/backgrounds/resources-hero-modern.png"
        alt=""
        width={768}
        height={1024}
        priority
        unoptimized
        sizes="320px"
        className="relative z-10 h-full w-full object-contain mix-blend-screen drop-shadow-[0_0_40px_rgba(20,184,166,0.35)]"
      />
    </div>
  );
}
