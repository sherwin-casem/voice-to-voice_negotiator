import { API_ROUTES } from "@voice/shared";

import { apiFetch } from "@/lib/api-client";

export type EvaluationStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "unavailable";

export interface EvaluationDimensionScores {
  communication: number | null;
  technical: number | null;
  relevance: number | null;
  structure: number | null;
  confidence: number | null;
  conciseness: number | null;
  problem_solving: number | null;
}

export interface EvaluationImprovementItem {
  area: string;
  priority: number;
  recommendation: string;
  rationale: string | null;
}

export interface PracticeRecommendationItem {
  title: string;
  instructions: string;
  success_criteria: string;
}

export interface BetterAnswerItem {
  question: string | null;
  example: string;
}

export interface AgentStatusItem {
  agent_name: string;
  status: string;
  skipped: boolean;
  summary: string | null;
}

export interface SessionEvaluationData {
  overall_score: number;
  dimension_scores: EvaluationDimensionScores;
  strengths: string[];
  weaknesses: string[];
  priority_improvements: EvaluationImprovementItem[];
  better_answers: BetterAnswerItem[];
  practice_recommendations: PracticeRecommendationItem[];
  did_well: string[];
  should_improve: string[];
  judge_summary: string | null;
  coach_summary: string | null;
  hire_recommendation: string | null;
  weights_applied: Record<string, number>;
}

export interface SessionEvaluationResponse {
  session_id: string;
  session_status: string;
  evaluation_status: EvaluationStatus;
  evaluation: SessionEvaluationData | null;
  error_message: string | null;
  agents: AgentStatusItem[];
}

export function getSessionEvaluation(sessionId: string): Promise<SessionEvaluationResponse> {
  return apiFetch<SessionEvaluationResponse>(API_ROUTES.sessionEvaluation(sessionId), {
    method: "GET",
  });
}
