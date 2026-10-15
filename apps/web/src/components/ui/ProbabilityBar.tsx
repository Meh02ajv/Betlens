"use client";

import { cn } from "@/lib/utils";
import { formatProbability } from "@/lib/utils";

interface ProbabilityBarProps {
  home: number;
  draw?: number;
  away: number;
  homeLabel?: string;
  awayLabel?: string;
  className?: string;
  showLabels?: boolean;
}

/**
 * Horizontal stacked probability bar for win/draw/loss.
 * Navy for home, grey tones for draw and away.
 * Always labelled with numbers (WCAG 2.1 AA).
 */
export function ProbabilityBar({
  home,
  draw,
  away,
  homeLabel = "Home",
  awayLabel = "Away",
  className,
  showLabels = true,
}: ProbabilityBarProps) {
  const homeW = Math.round(home * 100);
  const drawW = draw !== undefined ? Math.round(draw * 100) : 0;
  const awayW = Math.round(away * 100);

  return (
    <div className={cn("space-y-1", className)}>
      {showLabels && (
        <div className="flex justify-between text-caption text-text-secondary font-label">
          <span>{homeLabel}</span>
          {draw !== undefined && <span>Draw</span>}
          <span>{awayLabel}</span>
        </div>
      )}

      {/* Bar */}
      <div
        className="flex h-6 rounded-full overflow-hidden"
        role="img"
        aria-label={`${homeLabel} ${formatProbability(home)}, ${draw !== undefined ? `Draw ${formatProbability(draw)}, ` : ""}${awayLabel} ${formatProbability(away)}`}
      >
        <div
          className="flex items-center justify-center bg-accent text-white text-caption font-label transition-all"
          style={{ width: `${homeW}%` }}
        >
          {homeW >= 12 && `${homeW}%`}
        </div>
        {draw !== undefined && drawW > 0 && (
          <div
            className="flex items-center justify-center bg-text-secondary text-white text-caption font-label transition-all"
            style={{ width: `${drawW}%` }}
          >
            {drawW >= 10 && `${drawW}%`}
          </div>
        )}
        <div
          className="flex items-center justify-center bg-border text-text-primary text-caption font-label transition-all"
          style={{ width: `${awayW}%` }}
        >
          {awayW >= 12 && `${awayW}%`}
        </div>
      </div>

      {/* Numeric labels below */}
      <div className="flex justify-between text-caption font-label tabular-nums">
        <span className="text-accent">{formatProbability(home)}</span>
        {draw !== undefined && (
          <span className="text-text-secondary">{formatProbability(draw)}</span>
        )}
        <span className="text-text-secondary">{formatProbability(away)}</span>
      </div>
    </div>
  );
}