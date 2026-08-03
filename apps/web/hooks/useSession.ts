"use client";

import { useEffect, useState } from "react";

import { ApiClientError } from "@/lib/api-client";
import { getSession } from "@/lib/interview-api";
import type { SessionResponse } from "@voice/shared";

interface SessionLoadState {
  fetchKey: string;
  session: SessionResponse | null;
  error: string | null;
}

export function useSession(userId: string, sessionId: string) {
  const fetchKey = `${userId}:${sessionId}`;
  const [state, setState] = useState<SessionLoadState | null>(null);

  useEffect(() => {
    if (!userId || !sessionId) {
      return;
    }

    let cancelled = false;

    getSession(userId, sessionId)
      .then((session) => {
        if (!cancelled) {
          setState({ fetchKey, session, error: null });
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setState({
            fetchKey,
            session: null,
            error:
              caught instanceof ApiClientError
                ? caught.message
                : "Unable to load session.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [fetchKey, sessionId, userId]);

  const isCurrent = state?.fetchKey === fetchKey;

  return {
    session: isCurrent ? state.session : null,
    error: isCurrent ? state.error : null,
    isLoading: !userId || !sessionId || !isCurrent,
  };
}
