"use client";

import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Factor } from "@/types";

interface FactorListProps {
  factors: Factor[];
  className?: string;
}

/**
 * "Why this number?" panel listing the top factors with direction and magnitude.
 */
export function FactorList({ factors, className }: FactorListProps) {
  if (!factors.length) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <h4 className="text-body-sm font-label text-text-secondary">Why this number?</h4>
      <ul className="space-y-1.5" aria-label="Prediction factors">
        {factors.slice(0, 5).map((factor, i) => (
          <li key={i} className="flex items-center gap-2">
            {factor.direction === "up" ? (
              <TrendingUp
                className="w-4 h-4 text-positive flex-shrink-0"
                aria-label="Raises probability"
              />
            ) : (
              <TrendingDown
                className="w-4 h-4 text-live flex-shrink-0"
                aria-label="Lowers probability"
              />
            )}
            <span className="text-body-sm text-text-primary flex-1">{factor.label}</span>
            <span
              className={cn(
                "text-caption font-label tabular-nums",
                factor.direction === "up" ? "text-positive" : "text-live"
              )}
            >
              {factor.direction === "up" ? "+" : "-"}
              {(factor.impact * 100).toFixed(1)}pp
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}