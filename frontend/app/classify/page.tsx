"use client";

import { useEffect, useState } from "react";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { AppHeader } from "@/components/layout/AppHeader";
import { ImageUploadCard } from "@/components/ai/ImageUploadCard";
import { ClassificationResult } from "@/components/ai/ClassificationResult";
import { ClassificationHistory } from "@/components/ai/ClassificationHistory";
import { api } from "@/lib/api/client";
import type { Classification } from "@/types/ai";

export default function ClassifyPage() {
  const ready = useAuthGuard();
  const [latest, setLatest] = useState<Classification | null>(null);
  const [history, setHistory] = useState<Classification[]>([]);

  useEffect(() => {
    if (!ready) return;
    api
      .get<Classification[]>("/api/ai/classifications")
      .then(setHistory)
      .catch(() => {});
  }, [ready]);

  function handleClassified(result: Classification) {
    setLatest(result);
    setHistory((prev) => [result, ...prev]);
  }

  function handleConfirmed(updated: Classification) {
    setLatest(updated);
    setHistory((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
  }

  if (!ready) return null;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <AppHeader />

      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <ImageUploadCard onClassified={handleClassified} />
          {latest && <ClassificationResult classification={latest} onConfirmed={handleConfirmed} />}
        </div>

        <div>
          <h2 className="font-display text-xl text-ink">Your classifications</h2>
          <div className="mt-4">
            <ClassificationHistory items={history} />
          </div>
        </div>
      </div>
    </main>
  );
}