"use client";

import { useCallback, useRef } from "react";

import { usePrefersReducedMotion } from "@/components/visuals/usePrefersReducedMotion";
import { cn } from "@/lib/format";

const MAX_TILT_DEG = 7;

/**
 * Pointer-tracking 3D perspective tilt for decorative hero artwork.
 * Purely presentational: children keep their own semantics, the wrapper
 * only applies a GPU-composited rotateX/rotateY transform. Inert for
 * touch-only devices (no hover) and for `prefers-reduced-motion` users.
 */
export function TiltCard({
  children,
  className,
  maxTiltDeg = MAX_TILT_DEG,
}: {
  children: React.ReactNode;
  className?: string;
  maxTiltDeg?: number;
}) {
  const innerRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<number>(0);
  const reducedMotion = usePrefersReducedMotion();

  const handleMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (reducedMotion || event.pointerType !== "mouse") return;
      const target = event.currentTarget;
      const rect = target.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;

      cancelAnimationFrame(frameRef.current);
      frameRef.current = requestAnimationFrame(() => {
        if (!innerRef.current) return;
        innerRef.current.style.transform = `rotateX(${(-y * maxTiltDeg).toFixed(2)}deg) rotateY(${(x * maxTiltDeg).toFixed(2)}deg) scale(1.02)`;
      });
    },
    [maxTiltDeg, reducedMotion],
  );

  const handleLeave = useCallback(() => {
    cancelAnimationFrame(frameRef.current);
    if (innerRef.current) {
      innerRef.current.style.transform = "";
    }
  }, []);

  return (
    <div
      className={cn("[perspective:1000px]", className)}
      onPointerMove={handleMove}
      onPointerLeave={handleLeave}
    >
      <div
        ref={innerRef}
        className="transition-transform duration-300 ease-out will-change-transform [transform-style:preserve-3d]"
      >
        {children}
      </div>
    </div>
  );
}
