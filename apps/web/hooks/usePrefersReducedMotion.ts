"use client";

import { useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

/**
 * SSR-stable reduced-motion flag.
 * `useReducedMotion()` is `null` on the server and a real boolean on the client,
 * which can change Framer Motion props across hydration. Until mount, always
 * return `false` so the first client render matches the server tree.
 */
export function usePrefersReducedMotion(): boolean {
  const reduced = useReducedMotion();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  return ready ? Boolean(reduced) : false;
}
