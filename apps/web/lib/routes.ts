export const PREVIEW_SESSION_ID = "preview-1";

export const routes = {
  home: "/",
  features: "/features",
  pricing: "/pricing",
  resources: "/resources",
  login: "/login",
  register: "/register",
  createInterview: "/interviews/new",
  evaluations: "/evaluations",
  previewResults: `/interviews/${PREVIEW_SESSION_ID}/results?preview=1`,
  homeSection: (section: "features" | "evaluation" | "practice" | "flow") => `/#${section}`,
  sessionSetup: (sessionId: string) => `/interviews/${sessionId}/setup`,
  sessionLive: (sessionId: string) => `/interviews/${sessionId}/live`,
  sessionResults: (sessionId: string, preview = false) =>
    preview
      ? `/interviews/${sessionId}/results?preview=1`
      : `/interviews/${sessionId}/results`,
} as const;

export function isProtectedAppRoute(href: string): boolean {
  const [path, query = ""] = href.split("?");
  if (path.startsWith("/interviews/") && query.includes("preview=1")) {
    return false;
  }
  return path === routes.evaluations || path === routes.createInterview || path.startsWith("/interviews/");
}

export function registerWithNext(next: string): string {
  return `${routes.register}?next=${encodeURIComponent(next)}`;
}

/**
 * Restrict post-auth redirect targets to same-origin paths so a crafted
 * `?next=` cannot send users to an external site (open redirect).
 */
export function sanitizeNextPath(next: string | null | undefined, fallback: string): string {
  if (!next) {
    return fallback;
  }
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}

export function resolveAuthEntryHref(targetHref: string, isAuthenticated: boolean): string {
  if (isAuthenticated || !isProtectedAppRoute(targetHref)) {
    return targetHref;
  }
  return registerWithNext(targetHref);
}

export type HomeSection = "features" | "evaluation" | "practice" | "flow";

export const PRODUCT_FLOW = [
  {
    step: "1",
    title: "Create",
    detail:
      "Start by naming your practice session — for example, the role and interview round you're targeting. This creates a workspace where your setup, voice recording, and evaluation results stay together.",
  },
  {
    step: "2",
    title: "Configure",
    detail:
      "Choose the interview format (behavioral, technical, system design, HR, or leadership), set difficulty level, and optionally attach your resume and job description so questions stay relevant to the role you're preparing for.",
  },
  {
    step: "3",
    title: "Practice live",
    detail:
      "Join a real-time voice interview with an AI interviewer that listens to your answers and asks adaptive follow-ups — just like a live panel. Speak naturally; there are no typed responses or multiple-choice shortcuts.",
  },
  {
    step: "4",
    title: "Review scores",
    detail:
      "After the session, multiple evaluation agents score your responses across dimensions like communication, structure, and technical depth. Review unified scores, strengths, gaps, and concrete suggestions for stronger answers.",
  },
] as const;

export const FEATURE_CARDS = [
  {
    id: "practice" as const,
    eyebrow: "Voice practice",
    title: "Interview the way it actually happens",
    body:
      "Speak naturally with a live AI interviewer that adapts follow-ups to your answers — behavioral, technical, system design, HR, and leadership formats.",
    href: routes.createInterview,
    cta: "Create interview",
  },
  {
    id: "evaluation" as const,
    eyebrow: "Multi-agent evaluation",
    title: "Feedback from every angle",
    body:
      "Separate agents score communication, technical depth, structure, confidence, and more — then a unified report highlights strengths, gaps, and better answer examples.",
    href: routes.previewResults,
    cta: "View evaluation",
  },
  {
    id: "coaching" as const,
    eyebrow: "Longitudinal coaching",
    title: "Track how your voice improves",
    body:
      "Resume and job-description aware sessions, session history, and progress trends so each practice round builds on the last.",
    href: routes.evaluations,
    cta: "Open evaluations dashboard",
  },
] as const;

export const SITE_NAV_LINKS = [
  { label: "Features", href: routes.features },
  { label: "Evaluations", href: routes.evaluations },
  { label: "Resources", href: routes.resources },
  { label: "Pricing", href: routes.pricing },
] as const;
