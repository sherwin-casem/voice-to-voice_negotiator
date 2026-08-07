"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";

import { cn } from "@/lib/format";

/**
 * Scroll-entrance reveal driven by IntersectionObserver and the `.reveal`
 * CSS utilities in globals.css. Renders content immediately (SSR-safe) and
 * only animates once, the first time the element scrolls into view.
 * `prefers-reduced-motion` is handled in CSS, so no JS branch is needed.
 */
export function Reveal({
  children,
  className,
  delayMs = 0,
  as: Tag = "div",
}: {
  children: React.ReactNode;
  className?: string;
  /** Stagger offset for grouped items (e.g. cards in a grid). */
  delayMs?: number;
  as?: "div" | "section" | "li" | "article" | "span";
}) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    // Elements already in the viewport on mount (above the fold) reveal
    // immediately; everything else reveals on first intersection.
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ref={ref as any}
      className={cn("reveal", visible && "reveal-visible", className)}
      style={delayMs ? ({ "--reveal-delay": `${delayMs}ms` } as CSSProperties) : undefined}
    >
      {children}
    </Tag>
  );
}
