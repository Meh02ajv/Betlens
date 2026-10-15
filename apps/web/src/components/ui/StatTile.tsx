"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatTileProps {
  label: string;
  value: string | number;
  delta?: number;
  unit?: string;
  className?: string;
}

/**
 * Large number stat tile with label and optional trend delta.
 */
export function StatTile({ label, value, delta, unit, className }: StatTileProps) {
  return (
    <div className={cn("card flex flex-col gap-1", className)}>
      <span className="text-caption text-text-secondary font-label uppercase tracking-wide">
        {label}
      </span>
      <div className="flex items-end gap-1">
        <span className="text-page-title font-heading tabular-nums text-text-primary">
          {value}
        </span>
        {unit && (
          <span className="text-body-sm text-text-secondary mb-1">{unit}</span>
        )}
      </div>
      {delta !== undefined && (
        <div
          className={cn(
            "flex items-center gap-0.5 text-caption font-label tabular-nums",
            delta > 0 ? "text-positive" : delta < 0 ? "text-live" : "text-text-secondary"
          )}
        >
          {delta > 0 ? (
            <TrendingUp className="w-3 h-3" aria-hidden />
          ) : delta < 0 ? (
            <TrendingDown className="w-3 h-3" aria-hidden />
          ) : (
            <Minus className="w-3 h-3" aria-hidden />
          )}
          <span>
            {delta > 0 ? "+" : ""}
            {delta}
          </span>
        </div>
      )}
    </div>
  );
}