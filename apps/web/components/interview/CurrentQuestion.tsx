"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

import { GlassPanel } from "@/components/ui/GlassPanel";

export function CurrentQuestion({
  question,
  sequenceNum,
}: {
  question: string | null;
  sequenceNum: number | null;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <AnimatePresence mode="wait">
      {question ? (
        <motion.div
          key={`${sequenceNum}-${question.slice(0, 24)}`}
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -6 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        >
          <GlassPanel className="border-teal-500/15 bg-gradient-to-br from-teal-500/10 to-transparent p-4" aria-live="polite">
            {sequenceNum ? (
              <p className="text-section-label mb-2">Question {sequenceNum}</p>
            ) : null}
            <p className="text-base leading-relaxed text-[var(--text-primary)] sm:text-[1.05rem]">
              {question}
            </p>
          </GlassPanel>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
