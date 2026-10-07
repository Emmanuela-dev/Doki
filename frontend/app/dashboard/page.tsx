"use client";

import Link from "next/link";
import { AppHeader } from "@/components/layout/AppHeader";
import { useAuth } from "@/lib/auth-context";
import { useAuthGuard } from "@/lib/use-auth-guard";

export default function DashboardPage() {
  const ready = useAuthGuard();
  const { user } = useAuth();

  if (!ready || !user) return null;

  const isSeller = user.role === "SELLER";

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <AppHeader />

      <section className="mt-12">
        <p className="text-sm font-medium uppercase tracking-wider text-moss">
          {isSeller ? "Seller dashboard" : "Buyer dashboard"}
        </p>
        <h1 className="mt-2 font-display text-4xl text-ink">
          Welcome, {user.full_name}
        </h1>
        <p className="mt-3 max-w-2xl text-ink/65">
          {isSeller
            ? "Manage your organic waste listings and use AI to prepare new listings."
            : "Discover organic waste supply and connect with businesses that can provide it."}
        </p>
      </section>

      <section className="mt-10 grid gap-5 md:grid-cols-2">
        {isSeller ? (
          <>
            <DashboardCard
              title="Classify waste"
              description="Upload a photo and prepare an AI-assisted waste listing."
              href="/classify"
              action="Start classification"
            />
            <DashboardCard
              title="Your listings"
              description="Review and manage the organic waste you offer."
              href="/listings"
              action="View listings"
            />
          </>
        ) : (
          <>
            <DashboardCard
              title="Find organic waste"
              description="Browse available supply from verified businesses."
              href="/marketplace"
              action="Browse marketplace"
            />
            <DashboardCard
              title="Your purchases"
              description="Track your interests and active transactions."
              href="/transactions"
              action="View transactions"
            />
          </>
        )}
      </section>
    </main>
  );
}

function DashboardCard({
  title,
  description,
  href,
  action,
}: {
  title: string;
  description: string;
  href: string;
  action: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-xl border border-line bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:bg-surface"
    >
      <h2 className="font-display text-2xl text-ink">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-ink/65">{description}</p>
      <span className="mt-6 inline-block text-sm font-medium text-moss">{action} →</span>
    </Link>
  );
}
