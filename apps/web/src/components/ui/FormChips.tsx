"use client";

import { cn, parseForm } from "@/lib/utils";

interface FormChipsProps {
  form: string;
  className?: string;
}

/**
 * Last 5 form chips (W/D/L) for standings and team pages.
 */
export function FormChips({ form, className }: FormChipsProps) {
  const results = parseForm(form);

  return (
    <div
      className={cn("flex items-center gap-0.5", className)}
      aria-label={`Recent form: ${results.join(", ")}`}
    >
      {results.map((result, i) => (
        <span
          key={i}
          className={cn(
            "inline-flex items-center justify-center w-5 h-5 rounded-full text-caption font-label text-white",
            {
              "bg-positive": result === "W",
              "bg-text-secondary": result === "D",
              "bg-live": result === "L",
            }
          )}
          aria-hidden
        >
          {result}
        </span>
      ))}
    </div>
  );
}