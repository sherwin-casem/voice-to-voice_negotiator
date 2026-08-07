"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from "react";

import {
  clearAuthState,
  fetchCurrentUser,
  getAccessToken,
  loginAccount,
  logoutAccount,
  refreshAccessToken,
  registerAccount,
  setAccessToken,
  subscribeAuth,
  type AuthUser,
} from "@/lib/auth-api";
import {
  getClientReadySnapshot,
  getServerReadySnapshot,
  subscribeClientReady,
} from "@/lib/client-store";

interface AppContextValue {
  user: AuthUser | null;
  userId: string;
  accessToken: string | null;
  isAuthReady: boolean;
  isAuthenticated: boolean;
  isUserReady: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tokenVersion, setTokenVersion] = useState(0);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const isUserReady = useSyncExternalStore(
    subscribeClientReady,
    getClientReadySnapshot,
    getServerReadySnapshot,
  );

  useEffect(() => subscribeAuth(() => setTokenVersion((value) => value + 1)), []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapAuth() {
      try {
        const refreshed = await refreshAccessToken();
        if (cancelled) {
          return;
        }
        if (refreshed) {
          try {
            const profile = await fetchCurrentUser(refreshed);
            if (!cancelled) {
              setUser(profile);
            }
          } catch {
            // Token looked valid but /me failed — treat as logged out.
            if (!cancelled) {
              clearAuthState();
              setUser(null);
            }
          }
        } else if (!cancelled) {
          setUser(null);
        }
      } finally {
        // Always unlock the UI for the active mount. Strict Mode may cancel the
        // first run; the remounted effect must still be able to finish, and a
        // cancelled run must not leave the page stuck on "Checking session".
        setIsAuthReady(true);
      }
    }

    void bootstrapAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  const applyAuthResponse = useCallback(async (accessTokenValue: string) => {
    setAccessToken(accessTokenValue);
    const profile = await fetchCurrentUser(accessTokenValue);
    setUser(profile);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await loginAccount(email, password);
      await applyAuthResponse(response.access_token);
    },
    [applyAuthResponse],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      const response = await registerAccount(email, password);
      await applyAuthResponse(response.access_token);
    },
    [applyAuthResponse],
  );

  const logout = useCallback(async () => {
    try {
      await logoutAccount();
    } finally {
      clearAuthState();
      setUser(null);
    }
  }, []);

  const accessToken = getAccessToken();
  void tokenVersion;

  const value = useMemo(
    () => ({
      user,
      userId: user?.id ?? "",
      accessToken,
      isAuthReady,
      isAuthenticated: Boolean(user && accessToken),
      isUserReady,
      login,
      register,
      logout,
    }),
    [accessToken, isAuthReady, isUserReady, login, logout, register, user, tokenVersion],
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
