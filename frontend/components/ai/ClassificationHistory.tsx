"use client";

import Image from "next/image";
import type { Classification } from "@/types/ai";

interface ClassificationHistoryProps {
  items: Classification[];
}

export function ClassificationHistory({ items }: ClassificationHistoryProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-line p-6 text-center text-sm text-ink/50">
        No classifications yet — upload a photo to get started.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <div key={item.id} className="flex items-center gap-4 rounded-lg border border-line bg-surface p-3">
          <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-md">
            <Image src={item.image_url} alt={item.waste_type} fill sizes="56px" className="object-cover" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">{item.waste_type}</p>
            <p className="truncate text-xs text-ink/50">{new Date(item.created_at).toLocaleDateString()}</p>
          </div>
          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
              item.status === "confirmed" ? "bg-moss/15 text-moss-dark" : "bg-line text-ink/60"
            }`}
          >
            {item.status === "confirmed" ? "Confirmed" : "Pending"}
          </span>
        </div>
      ))}
    </div>
  );
}