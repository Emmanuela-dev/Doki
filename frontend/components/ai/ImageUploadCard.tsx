"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import type { Classification } from "@/types/ai";

interface ImageUploadCardProps {
  onClassified: (result: Classification) => void;
}

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_SIZE_MB = 5;

export function ImageUploadCard({ onClassified }: ImageUploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleFile(selected: File | null) {
    setError(null);
    if (!selected) return;

    if (!ALLOWED_TYPES.includes(selected.type)) {
      setError("Only JPEG, PNG, or WEBP images are allowed.");
      return;
    }
    if (selected.size / (1024 * 1024) > MAX_SIZE_MB) {
      setError(`Image must be under ${MAX_SIZE_MB}MB.`);
      return;
    }

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  }

  async function handleClassify() {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const result = await api.postForm<Classification>("/api/ai/classify", formData);
      onClassified(result);
      setFile(null);
      setPreview(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Classification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-xl text-ink">Classify waste</h2>
      <p className="mt-1 text-sm text-ink/60">
        Upload a photo of your organic waste and DoKi&apos;s AI will suggest a category.
      </p>

      <div
        className="mt-5 flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-line bg-paper px-4 py-8 text-center transition-colors hover:border-moss"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFile(e.dataTransfer.files?.[0] ?? null);
        }}
      >
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="Selected waste" className="h-40 w-full max-w-xs rounded-md object-cover" />
        ) : (
          <>
            <p className="text-sm text-ink/70">Drag a photo here, or click to browse</p>
            <p className="text-xs text-ink/40">JPEG, PNG, or WEBP — up to {MAX_SIZE_MB}MB</p>
          </>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />

      {error && <p className="mt-3 text-sm text-clay">{error}</p>}

      <Button className="mt-5 w-full" onClick={handleClassify} disabled={!file} loading={loading}>
        Classify photo
      </Button>
    </div>
  );
}