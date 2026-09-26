import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
}

export function Button({ loading, children, className = "", disabled, ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-md bg-moss px-4 py-2.5 font-medium text-white transition-colors hover:bg-moss-dark disabled:opacity-60 ${className}`}
      {...props}
    >
      {loading ? "Please wait…" : children}
    </button>
  );
}