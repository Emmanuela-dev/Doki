"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { api, ApiError } from "@/lib/api/client";
import { useAuthGuard } from "@/lib/use-auth-guard";

interface Listing {
  id: string;
  title: string;
  description?: string;
  waste_category_name: string;
  quantity: number;
  quantity_unit: string;
  price_per_unit: number;
  currency: string;
  location_address: string;
  status: string;
}

export default function ListingsPage() {
  const ready = useAuthGuard();
  const [listings, setListings] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .get<Listing[]>("/api/v1/listings/my")
      .then(setListings)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load your listings.");
      });
  }, [ready]);

  if (!ready) return null;

  return (
    <PageShell title="Your listings" subtitle="Manage the organic waste you offer to buyers.">
      {error && <Notice>{error}</Notice>}
      {!error && listings.length === 0 && (
        <EmptyState
          title="No listings yet"
          description="Classify your waste first, then create your first marketplace listing."
          href="/classify"
          action="Classify waste"
        />
      )}
      <div className="grid gap-4">
        {listings.map((listing) => (
          <article key={listing.id} className="rounded-xl border border-line bg-white p-5 shadow-sm dark:bg-surface">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-2xl text-ink">{listing.title}</h2>
                <p className="mt-1 text-sm text-ink/60">{listing.waste_category_name}</p>
              </div>
              <span className="rounded-full bg-moss/10 px-3 py-1 text-xs font-medium capitalize text-moss">
                {listing.status}
              </span>
            </div>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-ink/70">
              <span>{listing.quantity} {listing.quantity_unit}</span>
              <span>{listing.currency} {listing.price_per_unit} per unit</span>
              <span>{listing.location_address}</span>
            </div>
          </article>
        ))}
      </div>
    </PageShell>
  );
}

function PageShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <AppHeader />
      <section className="mt-10">
        <h1 className="font-display text-4xl text-ink">{title}</h1>
        <p className="mt-2 text-ink/65">{subtitle}</p>
      </section>
      <section className="mt-8">{children}</section>
    </main>
  );
}

function EmptyState({ title, description, href, action }: { title: string; description: string; href: string; action: string }) {
  return (
    <div className="rounded-xl border border-dashed border-line p-8 text-center">
      <h2 className="font-display text-2xl text-ink">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-ink/65">{description}</p>
      <a href={href} className="mt-5 inline-block rounded-md bg-moss px-4 py-2 text-sm text-white hover:bg-moss-dark">
        {action}
      </a>
    </div>
  );
}

function Notice({ children }: { children: React.ReactNode }) {
  return <p className="rounded-md bg-clay/10 p-4 text-sm text-clay">{children}</p>;
}
