const DEFAULT_DEV_API_URL = "";
const DEFAULT_SERVER_API_URL = "http://127.0.0.1:8000";

function isProductionBuildPhase(): boolean {
  return process.env.NEXT_PHASE === "phase-production-build";
}

function resolvePublicEnv(name: string, value: string | undefined, fallback: string): string {
  if (value !== undefined && value.trim().length > 0) {
    return value.trim();
  }

  if (process.env.NODE_ENV === "production" && !isProductionBuildPhase()) {
    throw new Error(`${name} must be set in production`);
  }

  return fallback;
}

export const env = {
  /** Empty string uses same-origin `/api/*` (Next.js rewrite to the backend). */
  apiUrl: resolvePublicEnv(
    "NEXT_PUBLIC_API_URL",
    process.env.NEXT_PUBLIC_API_URL,
    DEFAULT_DEV_API_URL,
  ),
  wsUrl: process.env.NEXT_PUBLIC_WS_URL?.trim() || undefined,
  devUserId: process.env.NEXT_PUBLIC_DEV_USER_ID?.trim() || undefined,
} as const;

/** Backend origin for WebSocket connections and server-side fetches. */
export function getApiOrigin(): string {
  if (env.apiUrl) {
    return env.apiUrl;
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return process.env.API_PROXY_TARGET?.trim() || DEFAULT_SERVER_API_URL;
}

export function getWebSocketBaseUrl(): string {
  if (env.wsUrl) {
    return env.wsUrl;
  }
  const origin = getApiOrigin();
  return origin.replace(/^http/i, "ws");
}
