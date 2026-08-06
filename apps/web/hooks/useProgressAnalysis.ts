"use client";

import { useEffect, useState } from "react";

import { ApiClientError } from "@/lib/api-client";
import { getProgressAnalysis, type ProgressAnalysis } from "@/lib/progress-api";

export function useProgressAnalysis(window = 5) {
  const [data, setData] = useState<ProgressAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    getProgressAnalysis(window)
      .then((analysis) => {
        if (!cancelled) {
          setData(analysis);
          setError(null);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setData(null);
          setError(
            caught instanceof ApiClientError ? caught.message : "Unable to load progress analysis.",
          );
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
  }, [window]);

  return { data, error, isLoading };
}
