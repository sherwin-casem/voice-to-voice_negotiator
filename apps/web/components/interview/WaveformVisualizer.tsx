"use client";

import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/format";

const BAR_COUNT = 24;

export function WaveformVisualizer({
  level,
  isActive,
  className,
}: {
  level: number;
  isActive: boolean;
  className?: string;
}) {
  const [activeBars, setActiveBars] = useState<number[]>(() =>
    Array.from({ length: BAR_COUNT }, () => 0.15),
  );

  const inactiveBars = useMemo(
    () => Array.from({ length: BAR_COUNT }, () => 0.12),
    [],
  );

  useEffect(() => {
    if (!isActive) {
      return;
    }

    const interval = window.setInterval(() => {
      setActiveBars(
        Array.from({ length: BAR_COUNT }, (_, index) => {
          const wave = Math.sin(Date.now() / 120 + index * 0.5) * 0.25;
          const base = level * 0.7 + 0.15;
          return Math.min(1, Math.max(0.08, base + wave + Math.random() * 0.15));
        }),
      );
    }, 80);

    return () => window.clearInterval(interval);
  }, [isActive, level]);

  const heights = isActive ? activeBars : inactiveBars;

  return (
    <div
      className={cn("flex h-8 items-end gap-0.5", className)}
      role="img"
      aria-label={isActive ? "Audio activity waveform" : "Audio inactive"}
    >
      {heights.map((height, index) => (
        <div
          key={index}
          className="w-1 rounded-sm bg-gradient-to-t from-teal-600 to-cyan-400 transition-all duration-75"
          style={{ height: `${height * 100}%` }}
        />
      ))}
    </div>
  );
}
