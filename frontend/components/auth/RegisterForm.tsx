"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import type { RegisterPayload, UserRole } from "@/types/auth";

export function RegisterForm() {
  const router = useRouter();
  const [role, setRole] = useState<UserRole>("SELLER");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const payload: RegisterPayload = {
      full_name: String(form.get("full_name")),
      business_name: String(form.get("business_name")),
      email: String(form.get("email")),
      phone: String(form.get("phone")),
      password: String(form.get("password")),
      role,
    };

    try {
      await api.post("/api/auth/register", payload);
      router.push("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <h1 className="font-display text-3xl text-ink">Create your account</h1>
        <p className="mt-1 text-sm text-ink/60">List waste or find supply on DoKi.</p>
      </div>

      <div className="flex rounded-md border border-line p-1">
        {(["SELLER", "BUYER"] as UserRole[]).map((r) => (
          <button
            type="button"
            key={r}
            onClick={() => setRole(r)}
            className={`flex-1 rounded-sm py-2 text-sm font-medium transition-colors ${
              role === r ? "bg-moss text-white" : "text-ink/70 hover:bg-surface"
            }`}
          >
            {r === "SELLER" ? "I have waste to sell" : "I need waste supply"}
          </button>
        ))}
      </div>

      <Input label="Full name" name="full_name" required autoComplete="name" />
      <Input label="Business name" name="business_name" required autoComplete="organization" />
      <Input label="Email" name="email" type="email" required autoComplete="email" />
      <Input label="Phone" name="phone" type="tel" required autoComplete="tel" />
      <Input label="Password" name="password" type="password" required autoComplete="new-password" minLength={8} />

      {error && <p className="text-sm text-clay">{error}</p>}

      <Button type="submit" loading={loading}>
        Create account
      </Button>

      <p className="text-center text-sm text-ink/60">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-moss hover:underline">
          Log in
        </Link>
      </p>
    </form>
  );
}