import { routes } from "@/lib/routes";

export const FEATURES_HERO = {
  eyebrow: "Product overview",
  title: "Coach how you speak, not just what you write.",
  description:
    "VoxForge is a voice-first interview studio. Practice realistic mock interviews out loud, get multi-agent evaluation across seven dimensions, and track improvement over time — built for candidates who want to perform under real conversational pressure.",
  primaryCta: { label: "Start practicing", href: routes.createInterview },
  secondaryCta: { label: "View evaluation", href: routes.previewResults },
} as const;

export const PROBLEM_SOLUTION = {
  eyebrow: "Why voice-first",
  title: "Written prep and spoken performance are not the same skill.",
  problem:
    "Most interview tools let you type answers at your own pace. That helps with content, but it does not train delivery — pacing, clarity under pressure, or thinking out loud when an interviewer pushes back.",
  solution:
    "VoxForge puts you in a live voice conversation with an AI interviewer that adapts follow-ups to what you actually say. You practice the format that matters: speaking clearly, structuring answers in real time, and recovering when you lose your thread.",
} as const;

export const EXPANDED_PILLARS = [
  {
    eyebrow: "Voice practice",
    title: "Interview the way it actually happens",
    body:
      "Speak naturally with a live AI interviewer that adapts follow-ups to your answers. Choose behavioral, technical, system design, HR, or leadership formats — each with difficulty levels matched to your target role.",
    bullets: [
      "Real-time voice conversation — no typing or multiple choice",
      "Dynamic follow-ups based on your answers",
      "Resume and job-description aware questioning",
    ],
  },
  {
    eyebrow: "Multi-agent evaluation",
    title: "Feedback from every angle",
    body:
      "Separate evaluation agents score distinct dimensions, then a unified report synthesizes strengths, gaps, priority improvements, and better answer examples you can rehearse immediately.",
    bullets: [
      "Seven scored dimensions with evidence-backed feedback",
      "Per-answer evaluations and suggested rewrites",
      "Actionable coaching recommendations for your next session",
    ],
  },
  {
    eyebrow: "Longitudinal coaching",
    title: "Track how your voice improves",
    body:
      "Every session builds on the last. Review history, dimension trends, and session scores so you can see whether your communication, structure, and technical depth are actually improving.",
    bullets: [
      "Session history and completion tracking",
      "Dimension trend comparisons over time",
      "Focused prep based on recurring weak spots",
    ],
  },
] as const;

export const EVALUATION_DIMENSIONS = [
  {
    name: "Communication",
    description: "Clarity, articulation, and how effectively you convey ideas aloud.",
  },
  {
    name: "Technical knowledge",
    description: "Depth and accuracy of domain expertise relevant to the role.",
  },
  {
    name: "Relevance",
    description: "How directly your answers address the question and role context.",
  },
  {
    name: "Structure",
    description: "Logical flow — frameworks, sequencing, and conclusion strength.",
  },
  {
    name: "Confidence",
    description: "Composure, assertiveness, and steadiness under follow-up pressure.",
  },
  {
    name: "Conciseness",
    description: "Signal-to-noise ratio — saying enough without rambling.",
  },
  {
    name: "Problem solving",
    description: "How you break down ambiguous questions and reason through trade-offs.",
  },
] as const;

export const INTERVIEW_FORMATS = [
  {
    name: "Behavioral",
    description: "Past experiences, conflict, ownership, and impact — STAR-ready practice.",
  },
  {
    name: "Technical",
    description: "Role-specific depth checks, debugging narratives, and implementation detail.",
  },
  {
    name: "System design",
    description: "Architecture discussions, scalability trade-offs, and component reasoning.",
  },
  {
    name: "Leadership",
    description: "Team influence, decision-making, and cross-functional alignment scenarios.",
  },
  {
    name: "HR / culture",
    description: "Motivation, collaboration style, and values alignment conversations.",
  },
] as const;

export const FEATURES_STATS = [
  { label: "Interview types", value: "5+" },
  { label: "Eval dimensions", value: "7" },
  { label: "Voice-first", value: "100%" },
] as const;

export const FEATURES_CTA = {
  title: "Ready to practice out loud?",
  description: "Start a session in minutes, or browse prep guides in Resources.",
  primaryCta: { label: "Start practicing", href: routes.createInterview },
  secondaryCta: { label: "Browse resources", href: routes.resources },
} as const;
