"use client";

import { createContext, useContext, useMemo, useState } from "react";

import { env } from "@/lib/env";
import { getDevUserId, setDevUserId } from "@/lib/user-id";

interface AppContextValue {
  userId: string;
  setUserId: (value: string) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

function readInitialUserId(): string {
  if (typeof window === "undefined") {
    return env.devUserId ?? "";
  }
  return getDevUserId();
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserIdState] = useState(readInitialUserId);

  const value = useMemo(
    () => ({
      userId,
      setUserId: (next: string) => {
        setDevUserId(next);
        setUserIdState(next);
      },
    }),
    [userId],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return context;
}
