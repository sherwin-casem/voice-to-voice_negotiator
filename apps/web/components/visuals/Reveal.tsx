"use client";

import { motion, type HTMLMotionProps } from "framer-motion";
import { useEffect, useState } from "react";

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { fadeUp, reducedMotionVariants, transitionBase } from "@/lib/motion";
import { cn } from "@/lib/format";

type RevealTag = "div" | "section" | "li" | "article" | "span";

const motionTags = {
  div: motion.div,
  section: motion.section,
  li: motion.li,
  article: motion.article,
  span: motion.span,
} as const;

/**
 * Scroll-entrance reveal powered by Framer Motion.
 * Keeps the previous Reveal API so existing call sites keep working.
 */
export function Reveal({
  children,
  className,
  delayMs = 0,
  as: tag = "div",
}: {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
  as?: RevealTag;
}) {
  const reduceMotion = usePrefersReducedMotion();
  const MotionTag = motionTags[tag];

  return (
    <MotionTag
      className={cn(className)}
      variants={reduceMotion ? reducedMotionVariants : fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.15, margin: "0px 0px -6% 0px" }}
      transition={{
        ...transitionBase,
        delay: reduceMotion ? 0 : delayMs / 1000,
      }}
    >
      {children}
    </MotionTag>
  );
}

/** Stagger parent for hero / grids. Children should use `variants={fadeUp}`. */
export function MotionStagger({
  children,
  className,
  ...props
}: HTMLMotionProps<"div">) {
  const reduceMotion = usePrefersReducedMotion();
  const [enter, setEnter] = useState(false);

  useEffect(() => {
    setEnter(true);
  }, []);

  return (
    <motion.div
      className={className}
      initial="hidden"
      animate={enter ? "visible" : "hidden"}
      variants={
        reduceMotion
          ? reducedMotionVariants
          : {
              hidden: {},
              visible: {
                transition: { staggerChildren: 0.1, delayChildren: 0.06 },
              },
            }
      }
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function MotionItem({
  children,
  className,
  ...props
}: HTMLMotionProps<"div">) {
  const reduceMotion = usePrefersReducedMotion();

  return (
    <motion.div
      className={className}
      variants={reduceMotion ? reducedMotionVariants : fadeUp}
      transition={transitionBase}
      {...props}
    >
      {children}
    </motion.div>
  );
}
