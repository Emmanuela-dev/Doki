"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { UserOut } from "@/types/auth";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  setToken: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem("doki-token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<UserOut>("/api/auth/me");
      setUser(me);
    } catch {
      localStorage.removeItem("doki-token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  async function setToken(token: string) {
    localStorage.setItem("doki-token", token);
    setLoading(true);
    await refreshUser();
  }

  function logout() {
    localStorage.removeItem("doki-token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, setToken, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
