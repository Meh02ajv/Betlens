"use client";

import { cn, confidenceColor, confidenceLabel } from "@/lib/utils";

interface ConfidenceBadgeProps {
  confidence: "low" | "medium" | "high";
  className?: string;
}

/**
 * Small outlined pill showing Low / Medium / High confidence.
 * Includes a tooltip explaining the meaning.
 */
export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  const label = confidence.charAt(0).toUpperCase() + confidence.slice(1);
  const tooltip = confidenceLabel(confidence);
  const colorClass = confidenceColor(confidence);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-caption font-label border",
        colorClass,
        className
      )}
      title={tooltip}
      aria-label={`Confidence: ${label}. ${tooltip}`}
    >
      <span
        className={cn("w-1.5 h-1.5 rounded-full", {
          "bg-positive": confidence === "high",
          "bg-accent": confidence === "medium",
          "bg-text-secondary": confidence === "low",
        })}
      />
      {label}
    </span>
  );
}