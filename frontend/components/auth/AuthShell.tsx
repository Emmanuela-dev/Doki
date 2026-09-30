import Image from "next/image";
import Link from "next/link";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

interface AuthShellProps {
  image: string;
  imageAlt: string;
  quote: string;
  children: React.ReactNode;
}

export function AuthShell({ image, imageAlt, quote, children }: AuthShellProps) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden lg:block">
        <Image src={image} alt={imageAlt} fill priority sizes="50vw" className="object-cover" />
        <div className="absolute inset-0 bg-linear-to-t from-black/70 via-black/10 to-transparent" />
        <div className="absolute bottom-10 left-10 right-10">
          <p className="font-display text-2xl italic leading-snug text-white">“{quote}”</p>
        </div>
      </div>

      <div className="flex flex-col justify-center px-6 py-12 sm:px-12 lg:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-col gap-8">
          <div className="flex items-center justify-between">
            <Link href="/" className="font-display text-xl text-ink">
              DoKi
            </Link>
            <ThemeToggle />
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}