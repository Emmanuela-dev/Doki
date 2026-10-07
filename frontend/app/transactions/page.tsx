"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { api, ApiError } from "@/lib/api/client";
import { useAuthGuard } from "@/lib/use-auth-guard";

interface Transaction {
  id: string;
  listing_title: string;
  quantity_requested: number;
  quantity_unit: string;
  total_amount?: number;
  currency: string;
  status: string;
  created_at: string;
}

export default function TransactionsPage() {
  const ready = useAuthGuard();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .get<Transaction[]>("/api/v1/transactions/?role_view=buyer")
      .then(setTransactions)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load your transactions.");
      });
  }, [ready]);

  if (!ready) return null;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <AppHeader />
      <section className="mt-10">
        <h1 className="font-display text-4xl text-ink">Your transactions</h1>
        <p className="mt-2 text-ink/65">Track purchase requests and delivery progress.</p>
      </section>
      <section className="mt-8">
        {error && <p className="rounded-md bg-clay/10 p-4 text-sm text-clay">{error}</p>}
        {!error && transactions.length === 0 && (
          <div className="rounded-xl border border-dashed border-line p-8 text-center">
            <h2 className="font-display text-2xl text-ink">No transactions yet</h2>
            <p className="mt-2 text-sm text-ink/65">Your purchase requests will appear here.</p>
          </div>
        )}
        <div className="grid gap-4">
          {transactions.map((transaction) => (
            <article key={transaction.id} className="rounded-xl border border-line bg-white p-5 shadow-sm dark:bg-surface">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h2 className="font-display text-2xl text-ink">{transaction.listing_title}</h2>
                <span className="rounded-full bg-moss/10 px-3 py-1 text-xs font-medium capitalize text-moss">
                  {transaction.status}
                </span>
              </div>
              <p className="mt-3 text-sm text-ink/70">
                {transaction.quantity_requested} {transaction.quantity_unit}
                {transaction.total_amount != null && ` · ${transaction.currency} ${transaction.total_amount}`}
              </p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
