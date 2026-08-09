import type { Transition, Variants } from "framer-motion";

/** Shared easing — soft, premium, not bouncy. */
export const easeOutExpo: Transition["ease"] = [0.22, 1, 0.36, 1];

export const transitionFast: Transition = {
  duration: 0.35,
  ease: easeOutExpo,
};

export const transitionBase: Transition = {
  duration: 0.55,
  ease: easeOutExpo,
};

export const transitionSlow: Transition = {
  duration: 0.75,
  ease: easeOutExpo,
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 22 },
  visible: { opacity: 1, y: 0 },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

export const fadeScale: Variants = {
  hidden: { opacity: 0, scale: 0.97 },
  visible: { opacity: 1, scale: 1 },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.09,
      delayChildren: 0.04,
    },
  },
};

export const pageTransition: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
};

export const reducedMotionVariants = {
  hidden: { opacity: 1, y: 0, scale: 1 },
  visible: { opacity: 1, y: 0, scale: 1 },
  initial: { opacity: 1, y: 0 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 1, y: 0 },
} as const;
