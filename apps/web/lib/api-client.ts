import type { ApiResponse } from "@voice/shared";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { userId: string },
): Promise<T> {
  const { userId, headers, ...rest } = options;
  const url = `${getBaseUrl()}${path}`;

  const response = await fetch(url, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
      ...headers,
    },
  });

  const body = (await response.json()) as ApiResponse<T>;

  if (!response.ok || body.error) {
    throw new ApiClientError(
      body.error?.message ?? `Request failed with status ${response.status}`,
      body.error?.code ?? "REQUEST_FAILED",
      response.status,
    );
  }

  if (body.data === null) {
    throw new ApiClientError("Empty response data", "EMPTY_RESPONSE", response.status);
  }

  return body.data;
}

export function getWebSocketUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const parsed = new URL(base);
  parsed.protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
  return `${parsed.origin}${path}`;
}
