"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { cn } from "@/lib/format";
import { pageTransition, reducedMotionVariants, transitionFast } from "@/lib/motion";

/**
 * Subtle route enter animation for App Router pages.
 * Exit is limited in App Router (unmount timing), but enter polish still helps.
 */
export function PageTransition({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const pathname = usePathname();
  const reduceMotion = usePrefersReducedMotion();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        variants={reduceMotion ? reducedMotionVariants : pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={transitionFast}
        className={cn("min-h-0", className)}
      >

        {children}
      </motion.div>
    </AnimatePresence>
  );
}
