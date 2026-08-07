"use client";

import { useEffect, useRef, useState } from "react";

import { ApiClientError } from "@/lib/api-client";
import {
  getSessionEvaluation,
  type SessionEvaluationResponse,
} from "@/lib/evaluation-api";

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 100; // ~5 minutes

/**
 * Load a session's evaluation, polling while the background multi-agent run
 * is still pending or running.
 */
export function useSessionEvaluation(sessionId: string, enabled = true) {
  const [data, setData] = useState<SessionEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(enabled && Boolean(sessionId));
  const attemptsRef = useRef(0);

  useEffect(() => {
    if (!enabled || !sessionId) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    attemptsRef.current = 0;
    setData(null);
    setError(null);
    setIsLoading(true);

    async function poll() {
      try {
        const response = await getSessionEvaluation(sessionId);
        if (cancelled) {
          return;
        }
        setData(response);
        setError(null);

        const stillRunning =
          response.evaluation_status === "pending" ||
          response.evaluation_status === "running";
        if (stillRunning && attemptsRef.current < MAX_POLL_ATTEMPTS) {
          attemptsRef.current += 1;
          timer = setTimeout(() => void poll(), POLL_INTERVAL_MS);
        } else {
          setIsLoading(false);
        }
      } catch (caught) {
        if (cancelled) {
          return;
        }
        setError(
          caught instanceof ApiClientError
            ? caught.message
            : "Unable to load the evaluation.",
        );
        setIsLoading(false);
      }
    }

    void poll();

    return () => {
      cancelled = true;
      if (timer !== null) {
        clearTimeout(timer);
      }
    };
  }, [enabled, sessionId]);

  const isEvaluating =
    isLoading ||
    data?.evaluation_status === "pending" ||
    data?.evaluation_status === "running";

  return { data, error, isLoading, isEvaluating };
}
