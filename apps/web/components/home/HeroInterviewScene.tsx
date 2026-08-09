"use client";

import Image from "next/image";

import { cn } from "@/lib/format";

/**
 * Large neural-plexus brain for the landing hero — sits in the scene like
 * the CampusIQ reference (full-bleed visual, not a framed card).
 */
export function HeroInterviewScene({ className }: { className?: string }) {
  return (
    <div className={cn("pointer-events-none relative h-full w-full", className)} aria-hidden>
      <div className="absolute inset-[10%] rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.35),transparent_65%)] blur-3xl" />
      <Image
        src="/backgrounds/landing-neural-brain.png"
        alt=""
        width={1024}
        height={1024}
        priority
        unoptimized
        sizes="(min-width: 1024px) 48vw, 90vw"
        className="relative z-10 h-full w-full scale-110 object-contain mix-blend-screen animate-float-slow"
      />
    </div>
  );
}
