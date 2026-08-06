"use client";

import { useEffect, useState } from "react";

import { ApiClientError } from "@/lib/api-client";
import { listSessions, type SessionSummary } from "@/lib/sessions-api";

export function useSessionHistory(limit = 20) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    listSessions(limit)
      .then((response) => {
        if (!cancelled) {
          setSessions(response.items);
          setError(null);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setSessions([]);
          setError(caught instanceof ApiClientError ? caught.message : "Unable to load sessions.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [limit]);

  return { sessions, error, isLoading };
}
