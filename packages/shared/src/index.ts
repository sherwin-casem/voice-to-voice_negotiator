export interface ApiError {
  code: string;
  message: string;
  request_id?: string | null;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

export interface HealthData {
  status: string;
}

export type HealthResponse = ApiResponse<HealthData>;

export type InterviewType =
  | "behavioral"
  | "technical"
  | "system_design"
  | "leadership"
  | "hr";

export type InterviewSessionStatus =
  | "created"
  | "configured"
  | "active"
  | "completing"
  | "completed"
  | "abandoned"
  | "evaluation_failed";

export type DifficultyLevel = "junior" | "mid" | "senior";

export const DIFFICULTY_LEVEL_LABELS: Record<DifficultyLevel, string> = {
  junior: "Junior",
  mid: "Mid-level",
  senior: "Senior",
};

export interface SessionResponse {
  id: string;
  user_id: string;
  status: InterviewSessionStatus;
  interview_type: InterviewType;
  title: string | null;
  config: Record<string, unknown>;
  question_count: number;
  resume_id: string | null;
  job_description_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  end_reason: string | null;
}

export interface QuestionResponse {
  id: string;
  session_id: string;
  sequence_num: number;
  question_text: string;
  topic_tag: string | null;
  follow_up_intent: string | null;
  is_follow_up: boolean;
  asked_at: string;
  agent_metadata: Record<string, unknown>;
}

export interface AnswerResponse {
  id: string;
  session_id: string;
  question_id: string;
  answer_text: string;
  answered_at: string;
  duration_ms: number | null;
  word_count: number | null;
}

export interface QuestionResultResponse {
  session: SessionResponse;
  question: QuestionResponse;
  should_end_session: boolean;
}

export interface SubmitAnswerResponse {
  session: SessionResponse;
  answer: AnswerResponse;
}

export type DocumentParseStatus = "pending" | "parsed" | "failed";

export interface ResumeResponse {
  id: string;
  title: string;
  summary_text: string | null;
  parse_status: DocumentParseStatus;
  created_at: string;
}

export interface JobDescriptionResponse {
  id: string;
  title: string;
  company_name: string | null;
  summary_text: string | null;
  parse_status: DocumentParseStatus;
  created_at: string;
}

export interface SessionSummaryResponse {
  id: string;
  title: string | null;
  interview_type: InterviewType;
  status: InterviewSessionStatus;
  ended_at: string | null;
  target_role: string | null;
  overall_score: number | null;
}

export interface SessionListResponse {
  items: SessionSummaryResponse[];
  limit: number;
  offset: number;
}

export interface UserResponse {
  id: string;
  email: string;
  display_name?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface DimensionTrendResponse {
  dimension: string;
  label: string;
  direction: string;
  recent_average: number;
  prior_average: number;
  delta: number;
  sessions_compared: number;
  comparable_sessions: number;
}

export interface ProgressAnalysisResponse {
  user_id: string;
  sessions_analyzed: number;
  window_size: number;
  dimension_trends: DimensionTrendResponse[];
  recurring_weaknesses: Array<{
    pattern: string;
    label: string;
    occurrences: number;
    session_count: number;
    frequency: number;
    is_persistent: boolean;
  }>;
  improvements: string[];
  persistent_weaknesses: string[];
  narrative_summary: string;
}

export interface CreateSessionRequest {
  title?: string | null;
}

export interface ConfigureSessionRequest {
  interview_type: InterviewType;
  difficulty: DifficultyLevel;
  target_role?: string | null;
  company_context?: string | null;
  max_questions?: number | null;
  target_duration_minutes?: number | null;
  title?: string | null;
  resume_id?: string | null;
  job_description_id?: string | null;
}

export const API_ROUTES = {
  health: "/api/v1/health",
  sessions: "/api/v1/sessions",
  session: (id: string) => `/api/v1/sessions/${id}`,
  startSession: (id: string) => `/api/v1/sessions/${id}/start`,
  nextQuestion: (id: string) => `/api/v1/sessions/${id}/questions/next`,
  submitAnswer: (id: string) => `/api/v1/sessions/${id}/answers`,
  endSession: (id: string) => `/api/v1/sessions/${id}/end`,
  sessionEvaluation: (id: string) => `/api/v1/sessions/${id}/evaluation`,
  resumes: "/api/v1/context/resumes",
  resume: (id: string) => `/api/v1/context/resumes/${id}`,
  resumeUpload: "/api/v1/context/resumes/upload",
  jobDescriptions: "/api/v1/context/job-descriptions",
  jobDescription: (id: string) => `/api/v1/context/job-descriptions/${id}`,
  jobDescriptionUpload: "/api/v1/context/job-descriptions/upload",
  progress: "/api/v1/progress",
  authRegister: "/api/v1/auth/register",
  authLogin: "/api/v1/auth/login",
  authLogout: "/api/v1/auth/logout",
  authRefresh: "/api/v1/auth/refresh",
  authMe: "/api/v1/auth/me",
  authWsTicket: "/api/v1/auth/ws-ticket",
  voiceWebSocket: (sessionId: string, ticket: string) =>
    `/api/v1/ws/interview/${sessionId}?ticket=${encodeURIComponent(ticket)}`,
} as const;

export const INTERVIEW_TYPE_LABELS: Record<InterviewType, string> = {
  behavioral: "Behavioral",
  technical: "Technical",
  system_design: "System Design",
  leadership: "Leadership",
  hr: "HR",
};

/** Persona shown in the live interview UI and used by the interviewer agent. */
export const INTERVIEWER_ROLE_LABELS: Record<InterviewType, string> = {
  behavioral: "Hiring Manager",
  technical: "Engineering Manager",
  system_design: "CTO",
  leadership: "CEO",
  hr: "HR Partner",
};

export function getInterviewerRole(interviewType: InterviewType | undefined): string {
  if (!interviewType) {
    return "Interviewer";
  }
  return INTERVIEWER_ROLE_LABELS[interviewType];
}

export const SESSION_STATUS_LABELS: Record<InterviewSessionStatus, string> = {
  created: "Created",
  configured: "Configured",
  active: "Active",
  completing: "Completing",
  completed: "Completed",
  abandoned: "Abandoned",
  evaluation_failed: "Evaluation Failed",
};
