import type { InterviewSessionStatus, InterviewType } from "@voice/shared";

/** Preview-only data until session list/history REST endpoints exist. */
export interface HistorySessionPreview {
  id: string;
  title: string;
  interview_type: InterviewType;
  status: InterviewSessionStatus;
  overall_score: number | null;
  completed_at: string | null;
  target_role: string | null;
}

export const MOCK_HISTORY_SESSIONS: HistorySessionPreview[] = [
  {
    id: "preview-1",
    title: "Backend Engineer — Technical",
    interview_type: "technical",
    status: "completed",
    overall_score: 78,
    completed_at: "2026-07-28T14:30:00Z",
    target_role: "Senior Backend Engineer",
  },
  {
    id: "preview-2",
    title: "Leadership Round",
    interview_type: "leadership",
    status: "completed",
    overall_score: 71,
    completed_at: "2026-07-22T09:15:00Z",
    target_role: "Engineering Manager",
  },
  {
    id: "preview-3",
    title: "Behavioral Practice",
    interview_type: "behavioral",
    status: "abandoned",
    overall_score: null,
    completed_at: null,
    target_role: "Product Manager",
  },
];

export interface ProgressSnapshotPreview {
  dimension: string;
  latest: number;
  previous: number;
}

export const MOCK_PROGRESS_TRENDS: ProgressSnapshotPreview[] = [
  { dimension: "Communication", latest: 78, previous: 72 },
  { dimension: "Technical", latest: 74, previous: 68 },
  { dimension: "Relevance", latest: 81, previous: 79 },
  { dimension: "Structure", latest: 70, previous: 65 },
];

export function getHistorySessionById(sessionId: string): HistorySessionPreview | undefined {
  return MOCK_HISTORY_SESSIONS.find((session) => session.id === sessionId);
}

export function canViewSessionResults(session: HistorySessionPreview): boolean {
  return session.status === "completed";
}
