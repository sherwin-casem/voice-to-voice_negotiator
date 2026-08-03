import { env } from "@/lib/env";

const STORAGE_KEY = "vvn-dev-user-id";
const USER_ID_EVENT = "vvn-user-id-change";
const PREVIEW_NOTICE_EVENT = "vvn-preview-notice-change";
export const PREVIEW_NOTICE_STORAGE_KEY = "vvn-preview-notice-dismissed";

function generateUuid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "00000000-0000-4000-8000-000000000001";
}

export function getServerUserId(): string {
  return env.devUserId ?? "";
}

export function readStoredUserId(): string {
  if (typeof window === "undefined") {
    return getServerUserId();
  }
  return window.localStorage.getItem(STORAGE_KEY) ?? getServerUserId();
}

export function ensureStoredUserId(): string {
  const existing = readStoredUserId();
  if (typeof window === "undefined") {
    return existing;
  }
  if (window.localStorage.getItem(STORAGE_KEY)) {
    return existing;
  }
  const created = existing || generateUuid();
  window.localStorage.setItem(STORAGE_KEY, created);
  window.dispatchEvent(new Event(USER_ID_EVENT));
  return created;
}

export function subscribeUserId(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  ensureStoredUserId();

  const handleChange = () => onStoreChange();
  window.addEventListener("storage", handleChange);
  window.addEventListener(USER_ID_EVENT, handleChange);
  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(USER_ID_EVENT, handleChange);
  };
}

export function getDevUserId(): string {
  return ensureStoredUserId();
}

export function setDevUserId(userId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, userId);
  window.dispatchEvent(new Event(USER_ID_EVENT));
}

export function subscribePreviewNotice(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleChange = () => onStoreChange();
  window.addEventListener("storage", handleChange);
  window.addEventListener(PREVIEW_NOTICE_EVENT, handleChange);
  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(PREVIEW_NOTICE_EVENT, handleChange);
  };
}

export function getPreviewNoticeDismissedSnapshot(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return window.localStorage.getItem(PREVIEW_NOTICE_STORAGE_KEY) === "1";
}

export function dismissPreviewNotice(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(PREVIEW_NOTICE_STORAGE_KEY, "1");
  window.dispatchEvent(new Event(PREVIEW_NOTICE_EVENT));
}

export function subscribeClientReady(onStoreChange: () => void): () => void {
  void onStoreChange;
  return () => {};
}

export function getClientReadySnapshot(): boolean {
  return typeof window !== "undefined";
}

export function getServerReadySnapshot(): boolean {
  return false;
}
