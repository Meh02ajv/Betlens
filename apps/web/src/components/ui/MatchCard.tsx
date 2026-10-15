"use client";

import Link from "next/link";
import { cn, formatKickoff, formatProbability } from "@/lib/utils";
import type { Match } from "@/types";
import { Logo } from "./Logo";

interface MatchCardProps {
  match: Match;
  homeWinProb?: number;
  awayWinProb?: number;
  className?: string;
}

/**
 * Compact match card showing teams, time/score, live indicator, and mini probability bar.
 */
export function MatchCard({ match, homeWinProb, awayWinProb, className }: MatchCardProps) {
  const isLive = match.status === "live";
  const isFinished = match.status === "finished";

  return (
    <Link
      href={`/matches/${match.id}`}
      className={cn(
        "card flex items-center gap-3 hover:border-accent-hover transition-colors duration-150 cursor-pointer",
        className
      )}
    >
      {/* Home team */}
      <div className="flex-1 flex items-center gap-2 min-w-0">
        <Logo src={match.home_team_logo} alt={match.home_team_name} className="w-6 h-6 flex-shrink-0" />
        <span className="text-body-sm font-label text-text-primary truncate">
          {match.home_team_name}
        </span>
      </div>

      {/* Score / Time */}
      <div className="flex flex-col items-center gap-0.5 flex-shrink-0 min-w-[64px]">
        {isLive && (
          <div className="flex items-center gap-1">
            <span className="live-dot" aria-label="Live" />
            <span className="text-caption text-live font-label">
              {match.minute ? `${match.minute}'` : "LIVE"}
            </span>
          </div>
        )}
        {(isLive || isFinished) && match.home_score !== null ? (
          <span className="text-section-title font-heading tabular-nums text-text-primary">
            {match.home_score} – {match.away_score}
          </span>
        ) : (
          <span className="text-body-sm text-text-secondary tabular-nums">
            {formatKickoff(match.kickoff_at)}
          </span>
        )}
        {match.status === "postponed" && (
          <span className="text-caption text-text-secondary">PPD</span>
        )}
      </div>

      {/* Away team */}
      <div className="flex-1 flex items-center justify-end gap-2 min-w-0">
        <span className="text-body-sm font-label text-text-primary truncate text-right">
          {match.away_team_name}
        </span>
        <Logo src={match.away_team_logo} alt={match.away_team_name} className="w-6 h-6 flex-shrink-0" />
      </div>

      {/* Mini probability bar */}
      {homeWinProb !== undefined && awayWinProb !== undefined && !isFinished && (
        <div className="hidden sm:flex items-center gap-1 flex-shrink-0 w-32">
          <span className="text-caption text-accent tabular-nums w-8 text-right">
            {formatProbability(homeWinProb)}
          </span>
          <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-border">
            <div
              className="h-full bg-accent rounded-full"
              style={{ width: `${homeWinProb * 100}%` }}
            />
          </div>
          <span className="text-caption text-text-secondary tabular-nums w-8">
            {formatProbability(awayWinProb)}
          </span>
        </div>
      )}
    </Link>
  );
}