const STORAGE_KEY = "vvn-dev-user-id";

function generateUuid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "00000000-0000-4000-8000-000000000001";
}

export function getDevUserId(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_DEV_USER_ID ?? "00000000-0000-4000-8000-000000000001";
  }

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const created = generateUuid();
  window.localStorage.setItem(STORAGE_KEY, created);
  return created;
}

export function setDevUserId(userId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, userId);
}
