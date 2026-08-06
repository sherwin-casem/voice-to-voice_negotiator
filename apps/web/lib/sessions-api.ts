import { API_ROUTES, type SessionListResponse, type SessionSummaryResponse } from "@voice/shared";

import { apiFetch } from "./api-client";

export type SessionSummary = SessionSummaryResponse;

export function listSessions(limit = 20, offset = 0): Promise<SessionListResponse> {
  return apiFetch<SessionListResponse>(`${API_ROUTES.sessions}?limit=${limit}&offset=${offset}`, {
    method: "GET",
  });
}
