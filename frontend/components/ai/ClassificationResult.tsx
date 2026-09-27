"use client";

import { useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import type { Classification } from "@/types/ai";

interface ClassificationResultProps {
  classification: Classification;
  onConfirmed: (updated: Classification) => void;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  High: "bg-moss/15 text-moss-dark",
  Medium: "bg-clay/15 text-clay",
  Low: "bg-clay/20 text-clay",
};

export function ClassificationResult({ classification, onConfirmed }: ClassificationResultProps) {
  const [editing, setEditing] = useState(false);
  const [wasteType, setWasteType] = useState(classification.waste_type);
  const [description, setDescription] = useState(classification.description);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isConfirmed = classification.status === "confirmed";

  async function handleConfirm() {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.put<Classification>(
        `/api/ai/classifications/${classification.id}/confirm`,
        editing ? { waste_type: wasteType, description } : {}
      );
      onConfirmed(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not confirm. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-6">
      <div className="flex items-start justify-between gap-4">
        <h2 className="font-display text-xl text-ink">AI result</h2>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
            isConfirmed ? "bg-moss/15 text-moss-dark" : "bg-line text-ink/60"
          }`}
        >
          {isConfirmed ? "Confirmed" : "Pending review"}
        </span>
      </div>

      <div className="relative mt-4 h-48 w-full overflow-hidden rounded-lg">
        <Image src={classification.image_url} alt={classification.waste_type} fill sizes="100vw" className="object-cover" />
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            CONFIDENCE_STYLES[classification.confidence] ?? "bg-line text-ink/60"
          }`}
        >
          {classification.confidence} confidence
        </span>
      </div>

      {editing ? (
        <div className="mt-4 flex flex-col gap-3">
          <div>
            <label className="text-sm text-ink/80">Waste type</label>
            <input
              value={wasteType}
              onChange={(e) => setWasteType(e.target.value)}
              className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 text-ink outline-none focus:border-moss"
            />
          </div>
          <div>
            <label className="text-sm text-ink/80">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 text-ink outline-none focus:border-moss"
            />
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <p className="font-display text-lg text-ink">{classification.waste_type}</p>
          <p className="mt-1 text-sm text-ink/70">{classification.description}</p>
        </div>
      )}

      {classification.possible_uses.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-ink/80">Possible uses</p>
          <ul className="mt-1.5 flex flex-wrap gap-2">
            {classification.possible_uses.map((use) => (
              <li key={use} className="rounded-full border border-line px-3 py-1 text-xs text-ink/70">
                {use}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-clay">{error}</p>}

      {!isConfirmed && (
        <div className="mt-5 flex gap-3">
          {editing ? (
            <>
              <Button onClick={handleConfirm} loading={loading}>
                Save &amp; confirm
              </Button>
              <button
                onClick={() => setEditing(false)}
                className="rounded-md border border-line px-4 py-2.5 text-sm text-ink/70 hover:bg-paper"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <Button onClick={handleConfirm} loading={loading}>
                Confirm as-is
              </Button>
              <button
                onClick={() => setEditing(true)}
                className="rounded-md border border-line px-4 py-2.5 text-sm text-ink/70 hover:bg-paper"
              >
                Correct it
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}