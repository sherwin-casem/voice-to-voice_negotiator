"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { pageTransition, reducedMotionVariants, transitionFast } from "@/lib/motion";

/**
 * Subtle route enter animation for App Router pages.
 * Exit is limited in App Router (unmount timing), but enter polish still helps.
 */
export function PageTransition({ children }: { children: React.ReactNode }) {
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
        className="min-h-0"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
