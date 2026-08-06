import { routes } from "@/lib/routes";

export const PRICING_HERO = {
  eyebrow: "Pricing",
  title: "Simple plans for serious interview prep.",
  description:
    "Start free and upgrade when you want unlimited practice, deeper evaluation reports, and progress tracking. Pricing may evolve during early access — all plans currently route to the same onboarding flow.",
} as const;

export const PRICING_TIERS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with core voice interview practice.",
    highlights: [
      "3 practice sessions per month",
      "Core voice interviews",
      "Basic evaluation summary",
      "Behavioral and technical formats",
    ],
    cta: { label: "Get started free", href: routes.createInterview },
    featured: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    period: "per month",
    description: "For candidates preparing for multiple rounds or role changes.",
    highlights: [
      "Unlimited practice sessions",
      "Full multi-agent evaluation reports",
      "Resume and job description context",
      "Dimension trends and session history",
      "Better-answer examples and coaching tips",
    ],
    cta: { label: "Start with Pro", href: routes.createInterview },
    featured: true,
  },
  {
    id: "team",
    name: "Team",
    price: "Custom",
    period: "contact us",
    description: "For bootcamps, career coaches, and hiring prep programs.",
    highlights: [
      "Multiple seats and shared dashboards",
      "Cohort progress visibility",
      "Manager and coach review workflows",
      "Priority support and onboarding",
    ],
    cta: { label: "Contact for Team", href: routes.createInterview },
    featured: false,
  },
] as const;

export const PRICING_COMPARISON = {
  categories: [
    {
      name: "Practice",
      features: [
        { label: "Voice interviews", free: true, pro: true, team: true },
        { label: "Sessions per month", free: "3", pro: "Unlimited", team: "Unlimited" },
        { label: "Interview formats", free: "Core", pro: "All", team: "All" },
        { label: "Resume / JD context", free: false, pro: true, team: true },
      ],
    },
    {
      name: "Evaluation",
      features: [
        { label: "Overall score", free: true, pro: true, team: true },
        { label: "Multi-agent dimension breakdown", free: false, pro: true, team: true },
        { label: "Per-answer feedback", free: false, pro: true, team: true },
        { label: "Better-answer examples", free: false, pro: true, team: true },
      ],
    },
    {
      name: "Progress",
      features: [
        { label: "Session history", free: "Limited", pro: true, team: true },
        { label: "Dimension trends", free: false, pro: true, team: true },
        { label: "Shared team dashboards", free: false, pro: false, team: true },
      ],
    },
  ],
} as const;

export const PRICING_FAQ = [
  {
    question: "Is billing live today?",
    answer:
      "Not yet. Plans are displayed so you know what to expect. All CTAs currently start the free onboarding flow. Paid tiers and checkout will roll out in a future release.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "When paid plans launch, you will be able to cancel before your next billing cycle. No long-term contracts are planned for individual Pro subscriptions.",
  },
  {
    question: "What data do you store from my interviews?",
    answer:
      "Session metadata, transcripts, and evaluation outputs are stored to power your history and coaching feedback. Review our privacy practices before sharing sensitive employer or personal information.",
  },
  {
    question: "What is included in early access?",
    answer:
      "Voice interviews, session setup, and evaluation reports are actively being improved. Some progress and metrics views may show placeholder data while backend endpoints are completed.",
  },
] as const;

export const PRICING_CTA = {
  title: "Start preparing today",
  description: "Create your first session free — no credit card required during early access.",
  primaryCta: { label: "Get started free", href: routes.createInterview },
  secondaryCta: { label: "See all features", href: routes.features },
} as const;
