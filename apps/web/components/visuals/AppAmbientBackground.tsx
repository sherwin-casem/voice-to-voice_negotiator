"use client";

import { GlowArt } from "@/components/ui/GlowArt";
import { cn } from "@/lib/format";

/**
 * Subtle decorative backdrop for authenticated app pages. Uses existing
 * 3D PNG assets with mix-blend-screen so they dissolve into the navy theme.
 */
export function AppAmbientBackground({
  variant = "default",
  className,
}: {
  variant?: "default" | "evaluations" | "live";
  className?: string;
}) {
  const art =
    variant === "evaluations"
      ? {
          src: "/backgrounds/insight-sphere.png",
          width: 512,
          height: 512,
          className: "right-[-8rem] top-[-6rem] w-[26rem] opacity-20",
        }
      : variant === "live"
        ? {
            src: "/backgrounds/voice-portal-booth.png",
            width: 1024,
            height: 576,
            className: "left-1/2 top-[-4rem] w-[48rem] max-w-none -translate-x-1/2 opacity-25",
          }
        : {
            src: "/backgrounds/multi-agent-network.png",
            width: 512,
            height: 512,
            className: "right-[-10rem] top-[-8rem] w-[30rem] opacity-15",
          };

  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden>
      <GlowArt
        src={art.src}
        width={art.width}
        height={art.height}
        sizes="(min-width: 1024px) 30rem, 0px"
        masked={false}
        className={cn("absolute hidden lg:block", art.className)}
      />
    </div>
  );
}
