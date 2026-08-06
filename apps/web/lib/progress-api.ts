import { API_ROUTES, type ProgressAnalysisResponse } from "@voice/shared";

import { apiFetch } from "./api-client";

export type ProgressAnalysis = ProgressAnalysisResponse;

export function getProgressAnalysis(window = 5): Promise<ProgressAnalysis> {
  return apiFetch<ProgressAnalysis>(`${API_ROUTES.progress}?window=${window}`, {
    method: "GET",
  });
}
