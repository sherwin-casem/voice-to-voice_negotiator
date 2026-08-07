import { routes } from "@/lib/routes";

export const RESOURCES_HERO = {
  eyebrow: "Resources",
  title: "Interview prep that matches real conversations.",
  description:
    "Guides, voice interview tips, and a clear path into VoxForge — so you know what to practice before you hit record.",
  primaryCta: { label: "Get started", href: routes.createInterview },
  secondaryCta: { label: "View features", href: routes.features },
} as const;

export const RESOURCE_GUIDES = [
  {
    title: "Behavioral interviews",
    description: "Structure past experiences with clarity and measurable impact.",
    bullets: [
      "Use STAR: situation, task, action, result",
      "Lead with the outcome, then explain your role",
      "Prepare 5–7 stories that flex across common themes",
    ],
  },
  {
    title: "Technical interviews",
    description: "Explain your thinking aloud while demonstrating depth.",
    bullets: [
      "Narrate assumptions before diving into solutions",
      "Call out trade-offs, edge cases, and testing approach",
      "Practice debugging stories with a clear timeline",
    ],
  },
  {
    title: "System design",
    description: "Communicate architecture decisions under open-ended prompts.",
    bullets: [
      "Clarify requirements and scale before drawing boxes",
      "Separate high-level flow from deep-dive components",
      "Discuss failure modes, monitoring, and iteration paths",
    ],
  },
  {
    title: "Leadership interviews",
    description: "Show influence, judgment, and team outcomes.",
    bullets: [
      "Frame decisions with context, stakeholders, and risks",
      "Highlight how you aligned people, not just projects",
      "Include what you would do differently next time",
    ],
  },
  {
    title: "HR / culture fit",
    description: "Answer motivation and collaboration questions authentically.",
    bullets: [
      "Connect your goals to the role and company mission",
      "Be specific about how you prefer to work with others",
      "Prepare thoughtful questions for the interviewer",
    ],
  },
] as const;

export const VOICE_TIPS = [
  {
    title: "Use headphones",
    detail: "Reduces echo and helps the AI hear you clearly during live sessions.",
  },
  {
    title: "Lead with the outcome",
    detail: "State your conclusion or impact in the first sentence, then support it.",
  },
  {
    title: "Pause instead of filling silence",
    detail: "A brief pause to structure your answer beats rambling under pressure.",
  },
  {
    title: "Expect follow-ups",
    detail: "Treat every answer as the start of a thread — interviewers probe depth.",
  },
  {
    title: "Review dimension scores",
    detail: "After each session, focus on one weak dimension in your next practice round.",
  },
] as const;

export const GETTING_STARTED = [
  {
    step: "1",
    title: "Create a session",
    detail: "Name your practice round and choose the role you are targeting.",
    href: routes.createInterview,
  },
  {
    step: "2",
    title: "Configure your interview",
    detail: "Pick format, difficulty, and optional resume or job description context.",
    href: routes.createInterview,
  },
  {
    step: "3",
    title: "Complete a voice interview",
    detail: "Practice live with adaptive follow-ups from the AI interviewer.",
    href: routes.createInterview,
  },
  {
    step: "4",
    title: "Review evaluations",
    detail: "Read scores, feedback, and trends on your Evaluations dashboard.",
    href: routes.evaluations,
  },
] as const;

export const RESOURCE_CROSS_LINKS = [
  { label: "Features", href: routes.features, description: "Full product overview" },
  { label: "Pricing", href: routes.pricing, description: "Plans and comparison" },
  { label: "Evaluations", href: routes.evaluations, description: "Session history and trends" },
] as const;
