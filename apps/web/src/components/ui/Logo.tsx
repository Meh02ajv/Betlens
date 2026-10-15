"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface LogoProps {
  src: string | null | undefined;
  alt: string;
  className?: string;
}

export function Logo({ src, alt, className }: LogoProps) {
  const [failed, setFailed] = useState(false);
  const fallback = alt.trim().slice(0, 2).toUpperCase();

  if (!src || failed) {
    return (
      <span
        aria-label={alt}
        className={cn(
          "inline-flex items-center justify-center rounded-full bg-accent-tint text-accent text-caption font-label",
          className
        )}
      >
        {fallback}
      </span>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={cn("object-contain", className)}
      onError={() => setFailed(true)}
    />
  );
}