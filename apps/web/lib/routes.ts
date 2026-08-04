export const PREVIEW_SESSION_ID = "preview-1";

export const routes = {
  home: "/",
  createInterview: "/interviews/new",
  progress: "/progress",
  previewResults: `/interviews/${PREVIEW_SESSION_ID}/results?preview=1`,
  homeSection: (section: "features" | "evaluation" | "practice" | "flow") => `/#${section}`,
  sessionSetup: (sessionId: string) => `/interviews/${sessionId}/setup`,
  sessionLive: (sessionId: string) => `/interviews/${sessionId}/live`,
  sessionResults: (sessionId: string, preview = false) =>
    preview
      ? `/interviews/${sessionId}/results?preview=1`
      : `/interviews/${sessionId}/results`,
} as const;

export type HomeSection = "features" | "evaluation" | "practice" | "flow";

export const PRODUCT_FLOW = [
  {
    step: "1",
    title: "Create",
    detail: "Name your session and begin setup.",
    href: routes.createInterview,
  },
  {
    step: "2",
    title: "Configure",
    detail: "Pick interview type, difficulty, and context.",
    href: routes.createInterview,
  },
  {
    step: "3",
    title: "Practice live",
    detail: "Voice interview with a dynamic AI interviewer.",
    href: routes.createInterview,
  },
  {
    step: "4",
    title: "Review scores",
    detail: "Multi-agent evaluation and coaching feedback.",
    href: routes.previewResults,
  },
] as const;

export const FEATURE_CARDS = [
  {
    id: "features" as const,
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
    cta: "View sample evaluation",
  },
  {
    id: "practice" as const,
    eyebrow: "Longitudinal coaching",
    title: "Track how your voice improves",
    body:
      "Resume and job-description aware sessions, session history, and progress trends so each practice round builds on the last.",
    href: routes.progress,
    cta: "Open progress dashboard",
  },
] as const;

export const SITE_NAV_LINKS = [
  { label: "Features", href: routes.homeSection("features"), isHash: true },
  { label: "Create Interview", href: routes.createInterview, isHash: false },
  { label: "Sample Results", href: routes.previewResults, isHash: false },
  { label: "Progress", href: routes.progress, isHash: false },
] as const;
