import type { ApiResponse } from "@voice/shared";

import { env } from "@/lib/env";

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

const DEFAULT_TIMEOUT_MS = 30_000;

async function parseJsonBody<T>(response: Response): Promise<ApiResponse<T>> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    throw new ApiClientError(
      "Server returned a non-JSON response",
      "INVALID_RESPONSE",
      response.status,
    );
  }

  try {
    return (await response.json()) as ApiResponse<T>;
  } catch {
    throw new ApiClientError(
      "Unable to parse server response",
      "INVALID_RESPONSE",
      response.status,
    );
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { userId: string; timeoutMs?: number },
): Promise<T> {
  const { userId, headers, timeoutMs = DEFAULT_TIMEOUT_MS, ...rest } = options;
  const url = `${env.apiUrl}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...rest,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": userId,
        ...headers,
      },
    });

    const body = await parseJsonBody<T>(response);

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
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError("Request timed out", "TIMEOUT", 408);
    }
    if (error instanceof TypeError) {
      throw new ApiClientError("Network request failed", "NETWORK_ERROR", 0);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function getWebSocketUrl(path: string): string {
  const parsed = new URL(env.wsUrl ?? env.apiUrl);
  parsed.protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
  return `${parsed.origin}${path}`;
}
