import {
  API_ROUTES,
  type ConfigureSessionRequest,
  type CreateSessionRequest,
  type JobDescriptionResponse,
  type QuestionResultResponse,
  type ResumeResponse,
  type SessionResponse,
  type SubmitAnswerResponse,
} from "@voice/shared";

import { apiFetch } from "./api-client";

export function createSession(userId: string, body: CreateSessionRequest): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.sessions, {
    method: "POST",
    userId,
    body: JSON.stringify(body),
  });
}

export function getSession(userId: string, sessionId: string): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.session(sessionId), {
    method: "GET",
    userId,
  });
}

export function configureSession(
  userId: string,
  sessionId: string,
  body: ConfigureSessionRequest,
): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.session(sessionId), {
    method: "PATCH",
    userId,
    body: JSON.stringify(body),
  });
}

export function startSession(userId: string, sessionId: string): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.startSession(sessionId), {
    method: "POST",
    userId,
    body: JSON.stringify({}),
  });
}

export function fetchNextQuestion(
  userId: string,
  sessionId: string,
): Promise<QuestionResultResponse> {
  return apiFetch<QuestionResultResponse>(API_ROUTES.nextQuestion(sessionId), {
    method: "POST",
    userId,
    body: JSON.stringify({}),
  });
}

export function submitAnswer(
  userId: string,
  sessionId: string,
  body: { question_id: string; answer_text: string; duration_ms?: number },
): Promise<SubmitAnswerResponse> {
  return apiFetch<SubmitAnswerResponse>(API_ROUTES.submitAnswer(sessionId), {
    method: "POST",
    userId,
    body: JSON.stringify(body),
  });
}

export function endSession(userId: string, sessionId: string): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.endSession(sessionId), {
    method: "POST",
    userId,
    body: JSON.stringify({}),
  });
}

export function createResume(
  userId: string,
  body: { title: string; raw_text: string },
): Promise<ResumeResponse> {
  return apiFetch<ResumeResponse>(API_ROUTES.resumes, {
    method: "POST",
    userId,
    body: JSON.stringify(body),
  });
}

export function createJobDescription(
  userId: string,
  body: { title: string; raw_text: string; company_name?: string | null },
): Promise<JobDescriptionResponse> {
  return apiFetch<JobDescriptionResponse>(API_ROUTES.jobDescriptions, {
    method: "POST",
    userId,
    body: JSON.stringify(body),
  });
}
