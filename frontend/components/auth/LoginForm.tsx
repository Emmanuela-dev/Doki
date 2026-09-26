"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import type { LoginPayload, TokenResponse } from "@/types/auth";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const payload: LoginPayload = {
      email: String(form.get("email")),
      password: String(form.get("password")),
    };

    try {
      const res = await api.post<TokenResponse>("/api/auth/login", payload);
      localStorage.setItem("doki-token", res.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <h1 className="font-display text-3xl text-ink">Welcome back</h1>
        <p className="mt-1 text-sm text-ink/60">Log in to your DoKi account.</p>
      </div>

      <Input label="Email" name="email" type="email" required autoComplete="email" />
      <Input label="Password" name="password" type="password" required autoComplete="current-password" />

      {error && <p className="text-sm text-clay">{error}</p>}

      <Button type="submit" loading={loading}>
        Log in
      </Button>

      <p className="text-center text-sm text-ink/60">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-medium text-moss hover:underline">
          Create one
        </Link>
      </p>
    </form>
  );
}