import Link from "next/link";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function Home() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <h1 className="font-display text-4xl text-ink">DoKi</h1>
      <p className="max-w-sm text-ink/70">The B2B marketplace for organic waste.</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link href="/login" className="rounded-md border border-line px-4 py-2 text-ink hover:bg-surface">
          Log in
        </Link>
        <Link href="/register" className="rounded-md bg-moss px-4 py-2 text-white hover:bg-moss-dark">
          Create account
        </Link>
        <Link href="/classify" className="rounded-md border border-line px-4 py-2 text-ink hover:bg-surface">
          Classify waste
        </Link>
      </div>
    </main>
  );
}