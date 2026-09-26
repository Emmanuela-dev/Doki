import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ label, error, id, ...props }, ref) => {
  const inputId = id ?? props.name;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm text-ink/80">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        className="rounded-md border border-line bg-surface px-3.5 py-2.5 text-ink placeholder:text-ink/40 outline-none transition-colors focus:border-moss focus:ring-1 focus:ring-moss"
        {...props}
      />
      {error && <span className="text-sm text-clay">{error}</span>}
    </div>
  );
});
Input.displayName = "Input";