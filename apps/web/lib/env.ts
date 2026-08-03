const DEFAULT_API_URL = "http://localhost:8000";

function isProductionBuildPhase(): boolean {
  return process.env.NEXT_PHASE === "phase-production-build";
}

function resolvePublicEnv(name: string, value: string | undefined, fallback: string): string {
  if (value && value.trim().length > 0) {
    return value.trim();
  }

  if (process.env.NODE_ENV === "production" && !isProductionBuildPhase()) {
    throw new Error(`${name} must be set in production`);
  }

  return fallback;
}

export const env = {
  apiUrl: resolvePublicEnv(
    "NEXT_PUBLIC_API_URL",
    process.env.NEXT_PUBLIC_API_URL,
    DEFAULT_API_URL,
  ),
  wsUrl: process.env.NEXT_PUBLIC_WS_URL?.trim() || undefined,
  devUserId: process.env.NEXT_PUBLIC_DEV_USER_ID?.trim() || undefined,
} as const;

export function getWebSocketBaseUrl(): string {
  return env.wsUrl ?? env.apiUrl;
}
