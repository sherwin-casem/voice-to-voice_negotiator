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

export const API_ROUTES = {
  health: "/api/v1/health",
} as const;
