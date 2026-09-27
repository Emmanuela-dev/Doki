"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth-context";

export function AppHeader() {
  const { user, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <div className="flex items-center justify-between">
      <Link href="/" className="font-display text-xl text-ink">
        DoKi
      </Link>

      <div className="flex items-center gap-4">
        {user && (
          <div className="hidden flex-col items-end leading-tight sm:flex">
            <span className="text-sm font-medium text-ink">{user.business_name}</span>
            <span className="text-xs text-ink/50">
              {user.full_name} · {user.role === "SELLER" ? "Seller" : "Buyer"}
            </span>
          </div>
        )}
        <ThemeToggle />
        {user && (
          <button
            onClick={handleLogout}
            className="rounded-md border border-line px-3 py-1.5 text-sm text-ink/70 transition-colors hover:bg-surface"
          >
            Log out
          </button>
        )}
      </div>
    </div>
  );
}