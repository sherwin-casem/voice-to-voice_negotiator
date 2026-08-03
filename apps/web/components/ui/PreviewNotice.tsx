"use client";

import { useSyncExternalStore } from "react";

import { Alert } from "@/components/ui/Alert";
import { cn } from "@/lib/format";
import {
  dismissPreviewNotice,
  getPreviewNoticeDismissedSnapshot,
  subscribePreviewNotice,
} from "@/lib/client-store";

export function PreviewNoticeBanner({ className }: { className?: string }) {
  const dismissed = useSyncExternalStore(
    subscribePreviewNotice,
    getPreviewNoticeDismissedSnapshot,
    () => false,
  );

  if (dismissed) {
    return null;
  }

  return (
    <div className={cn("mb-6", className)}>
      <Alert variant="warning" title="Preview mode">
        <p>
          Some screens still show sample data (progress trends, evaluation scores, live metrics)
          until backend endpoints are fully wired. Voice interviews and session setup use the real
          API.
        </p>
        <button
          type="button"
          onClick={dismissPreviewNotice}
          className="mt-3 text-xs font-medium text-amber-200 underline-offset-2 hover:underline"
        >
          Dismiss
        </button>
      </Alert>
    </div>
  );
}

/** @deprecated Use app-level PreviewNoticeBanner instead */
export function PreviewDataBanner({ endpoint }: { endpoint: string }) {
  void endpoint;
  return null;
}

/** @deprecated Live metrics panel is labeled at panel level */
export function PreviewMetricsBanner() {
  return null;
}
