"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { api, ApiError } from "@/lib/api/client";
import { useAuthGuard } from "@/lib/use-auth-guard";

interface Listing {
  id: string;
  title: string;
  waste_category_name: string;
  quantity: number;
  quantity_unit: string;
  price_per_unit: number;
  currency: string;
  location_address: string;
}

interface ListingResponse {
  results: Listing[];
}

export default function MarketplacePage() {
  const ready = useAuthGuard();
  const [listings, setListings] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .get<ListingResponse>("/api/v1/marketplace/?page=1&page_size=20")
      .then((response) => setListings(response.results))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load the marketplace.");
      });
  }, [ready]);

  if (!ready) return null;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <AppHeader />
      <section className="mt-10">
        <h1 className="font-display text-4xl text-ink">Marketplace</h1>
        <p className="mt-2 text-ink/65">Find organic waste supplied by businesses near you.</p>
      </section>
      <section className="mt-8">
        {error && <p className="rounded-md bg-clay/10 p-4 text-sm text-clay">{error}</p>}
        {!error && listings.length === 0 && (
          <div className="rounded-xl border border-dashed border-line p-8 text-center">
            <h2 className="font-display text-2xl text-ink">No active listings</h2>
            <p className="mt-2 text-sm text-ink/65">New supply will appear here when sellers publish listings.</p>
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          {listings.map((listing) => (
            <article key={listing.id} className="rounded-xl border border-line bg-white p-5 shadow-sm dark:bg-surface">
              <h2 className="font-display text-2xl text-ink">{listing.title}</h2>
              <p className="mt-1 text-sm text-ink/60">{listing.waste_category_name}</p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-ink/70">
                <span>{listing.quantity} {listing.quantity_unit}</span>
                <span>{listing.currency} {listing.price_per_unit} per unit</span>
                <span>{listing.location_address}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
