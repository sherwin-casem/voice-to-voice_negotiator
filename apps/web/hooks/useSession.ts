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

export function useSession(sessionId: string) {
  const fetchKey = sessionId;
  const [state, setState] = useState<SessionLoadState | null>(null);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    let cancelled = false;

    getSession(sessionId)
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
  }, [fetchKey, sessionId]);

  const isCurrent = state?.fetchKey === fetchKey;

  return {
    session: isCurrent ? state.session : null,
    error: isCurrent ? state.error : null,
    isLoading: !sessionId || !isCurrent,
  };
}
