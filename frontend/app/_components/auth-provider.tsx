"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { apiFetch } from "@/app/_lib/api";

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  is_active: boolean;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => Promise<void>;
  setToken: (token: string) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async (accessToken: string) => {
    const res = await apiFetch("/api/v1/users/me", { token: accessToken });
    if (res.ok) {
      const data = await res.json();
      setUser(data);
    }
  }, []);

  const setToken = useCallback(
    (newToken: string) => {
      setTokenState(newToken);
      fetchUser(newToken);
    },
    [fetchUser],
  );

  const login = useCallback(
    (newToken: string) => {
      setToken(newToken);
    },
    [setToken],
  );

  const logout = useCallback(async () => {
    await apiFetch("/api/v1/auth/logout", { method: "POST", token });
    setTokenState(null);
    setUser(null);
  }, [token]);

  // On mount: try to restore session via refresh cookie
  useEffect(() => {
    async function restore() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/refresh`,
          { method: "POST", credentials: "include" },
        );
        if (res.ok) {
          const data = await res.json();
          await fetchUser(data.access_token);
          setTokenState(data.access_token);
        }
      } finally {
        setIsLoading(false);
      }
    }
    restore();
  }, [fetchUser]);

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, logout, setToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
