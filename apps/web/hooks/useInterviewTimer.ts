"use client";

import { useEffect, useState } from "react";

export function useInterviewTimer(active: boolean): number {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!active) {
      return;
    }

    const interval = window.setInterval(() => {
      setElapsedSeconds((previous) => previous + 1);
    }, 1000);

    return () => window.clearInterval(interval);
  }, [active]);

  return elapsedSeconds;
}
