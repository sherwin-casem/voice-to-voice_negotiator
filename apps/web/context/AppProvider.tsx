"use client";

import { createContext, useContext, useMemo, useSyncExternalStore } from "react";

import {
  getServerReadySnapshot,
  getClientReadySnapshot,
  readStoredUserId,
  getServerUserId,
  setDevUserId,
  subscribeClientReady,
  subscribeUserId,
} from "@/lib/client-store";

interface AppContextValue {
  userId: string;
  isUserReady: boolean;
  setUserId: (value: string) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const userId = useSyncExternalStore(subscribeUserId, readStoredUserId, getServerUserId);
  const isUserReady = useSyncExternalStore(
    subscribeClientReady,
    getClientReadySnapshot,
    getServerReadySnapshot,
  );

  const value = useMemo(
    () => ({
      userId,
      isUserReady,
      setUserId: setDevUserId,
    }),
    [isUserReady, userId],
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
