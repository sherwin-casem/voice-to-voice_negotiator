import {
  API_ROUTES,
  type ConfigureSessionRequest,
  type CreateSessionRequest,
  type JobDescriptionResponse,
  type ResumeResponse,
  type SessionResponse,
} from "@voice/shared";

import { apiFetch } from "./api-client";

export function createSession(body: CreateSessionRequest): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.sessions, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getSession(sessionId: string): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.session(sessionId), {
    method: "GET",
  });
}

export function configureSession(
  sessionId: string,
  body: ConfigureSessionRequest,
): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.session(sessionId), {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function endSession(sessionId: string): Promise<SessionResponse> {
  return apiFetch<SessionResponse>(API_ROUTES.endSession(sessionId), {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function createResume(body: { title: string; raw_text: string }): Promise<ResumeResponse> {
  return apiFetch<ResumeResponse>(API_ROUTES.resumes, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createJobDescription(body: {
  title: string;
  raw_text: string;
  company_name?: string | null;
}): Promise<JobDescriptionResponse> {
  return apiFetch<JobDescriptionResponse>(API_ROUTES.jobDescriptions, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
