import type { ApiResponse } from "@voice/shared";

import { env } from "@/lib/env";

export interface AuthUser {
  id: string;
  email: string;
  displayName?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

const AUTH_EVENT = "vvn-auth-change";

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
}

export function clearAuthState(): void {
  accessToken = null;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
}

export function subscribeAuth(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }
  const handleChange = () => onStoreChange();
  window.addEventListener(AUTH_EVENT, handleChange);
  return () => window.removeEventListener(AUTH_EVENT, handleChange);
}

function mapAuthUser(raw: { id: string; email: string; display_name?: string | null }): AuthUser {
  return {
    id: raw.id,
    email: raw.email,
    displayName: raw.display_name ?? null,
  };
}

function normalizeAuthResponse(raw: {
  access_token: string;
  token_type: string;
  user: { id: string; email: string; display_name?: string | null };
}): AuthResponse {
  return {
    access_token: raw.access_token,
    token_type: raw.token_type,
    user: mapAuthUser(raw.user),
  };
}

async function parseJsonBody<T>(response: Response): Promise<ApiResponse<T>> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    if (response.status === 404) {
      throw new Error(
        "Authentication service is unavailable. Ensure the API server is running and exposes /api/v1/auth/* routes.",
      );
    }
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as ApiResponse<T>;
}

export async function authFetch<T>(
  path: string,
  options: RequestInit & { accessToken?: string | null } = {},
): Promise<T> {
  const { accessToken: tokenOverride, headers, ...rest } = options;
  const token = tokenOverride ?? accessToken;
  const response = await fetch(`${env.apiUrl}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const body = await parseJsonBody<T>(response);
  if (!response.ok || body.error) {
    throw new Error(body.error?.message ?? `Request failed with status ${response.status}`);
  }
  if (body.data === null) {
    throw new Error("Empty response data");
  }
  return body.data;
}

export function registerAccount(email: string, password: string): Promise<AuthResponse> {
  return authFetch<{ access_token: string; token_type: string; user: { id: string; email: string; display_name?: string | null } }>(
    "/api/v1/auth/register",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  ).then(normalizeAuthResponse);
}

export function loginAccount(email: string, password: string): Promise<AuthResponse> {
  return authFetch<{ access_token: string; token_type: string; user: { id: string; email: string; display_name?: string | null } }>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  ).then(normalizeAuthResponse);
}

export function refreshSession(): Promise<AuthResponse> {
  return authFetch<{ access_token: string; token_type: string; user: { id: string; email: string; display_name?: string | null } }>(
    "/api/v1/auth/refresh",
    {
      method: "POST",
      body: JSON.stringify({}),
    },
  ).then(normalizeAuthResponse);
}

export function logoutAccount(): Promise<{ success: boolean }> {
  return authFetch<{ success: boolean }>("/api/v1/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function fetchCurrentUser(token?: string | null): Promise<AuthUser> {
  return authFetch<{ id: string; email: string; display_name?: string | null }>("/api/v1/auth/me", {
    method: "GET",
    accessToken: token,
  }).then(mapAuthUser);
}

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = refreshSession()
    .then((response) => {
      setAccessToken(response.access_token);
      return response.access_token;
    })
    .catch(() => {
      clearAuthState();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

export async function getValidAccessToken(): Promise<string | null> {
  const existing = getAccessToken();
  if (existing) {
    return existing;
  }
  return refreshAccessToken();
}
