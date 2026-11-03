"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { UserOut } from "@/types/auth";

const TOKEN_COOKIE = "doki-token";

function setCookie(name: string, value: string) {
  document.cookie = `${name}=${value}; path=/; max-age=604800; SameSite=Lax`;
}

function clearCookie(name: string) {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
}

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
      clearCookie(TOKEN_COOKIE);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(refreshUser);
  }, [refreshUser]);

  async function setToken(token: string) {
    localStorage.setItem("doki-token", token);
    setCookie(TOKEN_COOKIE, token);
    setLoading(true);
    await refreshUser();
  }

  function logout() {
    localStorage.removeItem("doki-token");
    clearCookie(TOKEN_COOKIE);
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
