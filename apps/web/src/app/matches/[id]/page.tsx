"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { sportsApi, predictionsApi, oddsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { ProbabilityBar } from "@/components/ui/ProbabilityBar";
import { ConfidenceBadge } from "@/components/ui/ConfidenceBadge";
import { FactorList } from "@/components/ui/FactorList";
import { Skeleton, PredictionSkeleton } from "@/components/ui/Skeleton";
import { formatKickoff, formatProbability } from "@/lib/utils";
import type { Match, MatchPrediction, OddsEntry } from "@/types";

type Tab = "overview" | "lineups" | "odds" | "live";

export default function MatchPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("overview");
  const [match, setMatch] = useState<Match | null>(null);
  const [prediction, setPrediction] = useState<MatchPrediction | null>(null);
  const [odds, setOdds] = useState<OddsEntry[]>([]);
  const [lineups, setLineups] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [predLoading, setPredLoading] = useState(true);

  useEffect(() => {
    sportsApi.getMatch(id).then(setMatch).finally(() => setLoading(false));
    predictionsApi
      .getMatchPredictions(id)
      .then(setPrediction)
      .catch(() => setPrediction(null))
      .finally(() => setPredLoading(false));
  }, [id]);

  const loadOdds = async () => {
    if (odds.length === 0) {
      const data = await oddsApi.getMatchOdds(id);
      setOdds(data);
    }
  };

  const loadLineups = async () => {
    if (lineups.length === 0) {
      const data = await sportsApi.getMatchLineups(id);
      setLineups(data);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "lineups", label: "Lineups" },
    { id: "odds", label: "Odds" },
    { id: "live", label: "Live" },
  ];

  const isLive = match?.status === "live";
  const isFinished = match?.status === "finished";

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Match header */}
        <div className="card">
          {loading ? (
            <Skeleton className="h-20 w-full" />
          ) : match ? (
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-6 w-full">
                {/* Home */}
                <div className="flex-1 flex flex-col items-center gap-2">
                  {match.home_team_logo && (
                    <img src={match.home_team_logo} alt={match.home_team_name} className="w-12 h-12 object-contain" />
                  )}
                  <span className="font-label text-text-primary text-center">{match.home_team_name}</span>
                </div>

                {/* Score / Time */}
                <div className="flex flex-col items-center gap-1 flex-shrink-0">
                  {isLive && (
                    <div className="flex items-center gap-1">
                      <span className="live-dot" />
                      <span className="text-caption text-live font-label">
                        {match.minute ? `${match.minute}'` : "LIVE"}
                      </span>
                    </div>
                  )}
                  {(isLive || isFinished) && match.home_score !== null ? (
                    <span className="text-hero font-heading tabular-nums text-text-primary">
                      {match.home_score} – {match.away_score}
                    </span>
                  ) : (
                    <span className="text-section-title font-heading text-text-primary">
                      {formatKickoff(match.kickoff_at)}
                    </span>
                  )}
                  <span className="text-caption text-text-secondary">{match.round}</span>
                  {match.venue_name && (
                    <span className="text-caption text-text-secondary">{match.venue_name}</span>
                  )}
                </div>

                {/* Away */}
                <div className="flex-1 flex flex-col items-center gap-2">
                  {match.away_team_logo && (
                    <img src={match.away_team_logo} alt={match.away_team_name} className="w-12 h-12 object-contain" />
                  )}
                  <span className="font-label text-text-primary text-center">{match.away_team_name}</span>
                </div>
              </div>

              {/* Ask assistant CTA */}
              <Link
                href={`/assistant?context=match:${id}`}
                className="btn-secondary text-body-sm"
              >
                Ask the assistant about this match
              </Link>
            </div>
          ) : null}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border gap-1" role="tablist">
          {tabs.map(({ id: tabId, label }) => (
            <button
              key={tabId}
              role="tab"
              aria-selected={tab === tabId}
              onClick={() => {
                setTab(tabId);
                if (tabId === "odds") loadOdds();
                if (tabId === "lineups") loadLineups();
              }}
              className={`px-4 py-2 text-body-sm font-label border-b-2 transition-colors ${
                tab === tabId
                  ? "border-accent text-accent"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {label}
              {tabId === "live" && isLive && (
                <span className="ml-1.5 live-dot inline-block" />
              )}
            </button>
          ))}
        </div>

        {/* Overview tab */}
        {tab === "overview" && (
          <div className="space-y-6">
            {/* Probability panel */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-section-title font-heading text-text-primary">
                  Match probabilities
                </h2>
                {prediction && <ConfidenceBadge confidence={prediction.confidence} />}
              </div>

              {predLoading ? (
                <PredictionSkeleton />
              ) : prediction ? (
                <div className="space-y-6">
                  {/* 1X2 bar */}
                  {prediction.markets.home !== undefined && (
                    <ProbabilityBar
                      home={prediction.markets.home}
                      draw={prediction.markets.draw}
                      away={prediction.markets.away ?? 0}
                      homeLabel={match?.home_team_name ?? "Home"}
                      awayLabel={match?.away_team_name ?? "Away"}
                    />
                  )}

                  {/* Expected goals */}
                  {prediction.expected_goals && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <p className="text-page-title font-heading text-accent tabular-nums">
                          {prediction.expected_goals.home.toFixed(2)}
                        </p>
                        <p className="text-caption text-text-secondary">xG {match?.home_team_name}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-page-title font-heading text-accent tabular-nums">
                          {prediction.expected_goals.away.toFixed(2)}
                        </p>
                        <p className="text-caption text-text-secondary">xG {match?.away_team_name}</p>
                      </div>
                    </div>
                  )}

                  {/* Key markets */}
                  {prediction.markets.totals && (
                    <div>
                      <h3 className="text-body-sm font-label text-text-secondary mb-2">Goals markets</h3>
                      <div className="space-y-1">
                        {prediction.markets.totals.map((t) => (
                          <div key={t.line} className="flex items-center justify-between text-body-sm">
                            <span className="text-text-secondary">Over {t.line}</span>
                            <div className="flex gap-4 tabular-nums">
                              <span className="text-accent">{formatProbability(t.over)}</span>
                              <span className="text-text-secondary">{formatProbability(t.under)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* BTTS */}
                  {prediction.markets.btts && (
                    <div className="flex items-center justify-between text-body-sm">
                      <span className="text-text-secondary">Both teams to score</span>
                      <div className="flex gap-4 tabular-nums">
                        <span className="text-accent">Yes {formatProbability(prediction.markets.btts.yes)}</span>
                        <span className="text-text-secondary">No {formatProbability(prediction.markets.btts.no)}</span>
                      </div>
                    </div>
                  )}

                  {/* Correct score */}
                  {prediction.markets.correct_score && (
                    <div>
                      <h3 className="text-body-sm font-label text-text-secondary mb-2">Top scorelines</h3>
                      <div className="grid grid-cols-3 gap-2">
                        {prediction.markets.correct_score.slice(0, 6).map((cs) => (
                          <div key={cs.score} className="text-center bg-surface rounded-button py-2">
                            <p className="font-label text-text-primary tabular-nums">{cs.score}</p>
                            <p className="text-caption text-text-secondary tabular-nums">
                              {formatProbability(cs.p)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Factors */}
                  <FactorList factors={prediction.factors} />

                  <p className="disclaimer">
                    Estimates based on statistical models. No outcome is guaranteed.
                  </p>
                </div>
              ) : (
                <p className="text-body-sm text-text-secondary">
                  No predictions available for this match yet.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Lineups tab */}
        {tab === "lineups" && (
          <div className="card">
            {lineups.length === 0 ? (
              <p className="text-body-sm text-text-secondary text-center py-8">
                Lineups not yet confirmed. Check back closer to kickoff.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-6">
                {(lineups as Array<{ team_id: string; formation: string; is_confirmed: boolean; starters: Array<{ position: string }> }>).map((lu) => (
                  <div key={lu.team_id}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="font-label text-text-primary">{lu.formation}</span>
                      {!lu.is_confirmed && (
                        <span className="badge badge-low">Predicted</span>
                      )}
                    </div>
                    <ul className="space-y-1">
                      {lu.starters.map((p, i) => (
                        <li key={i} className="text-body-sm text-text-secondary">
                          {p.position}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Odds tab */}
        {tab === "odds" && (
          <div className="card">
            <h2 className="text-section-title font-heading text-text-primary mb-4">Odds comparison</h2>
            {odds.length === 0 ? (
              <p className="text-body-sm text-text-secondary text-center py-8">
                No odds data available.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-body-sm tabular-nums">
                  <thead>
                    <tr className="text-caption text-text-secondary font-label border-b border-border">
                      <th className="text-left py-2">Bookmaker</th>
                      <th className="text-left py-2">Market</th>
                      <th className="text-left py-2">Selection</th>
                      <th className="text-right py-2">Odds</th>
                      <th className="text-right py-2">Implied</th>
                    </tr>
                  </thead>
                  <tbody>
                    {odds.map((o) => (
                      <tr key={o.id} className="border-b border-border hover:bg-surface">
                        <td className="py-2 text-text-primary">{o.bookmaker}</td>
                        <td className="py-2 text-text-secondary">{o.market}</td>
                        <td className="py-2 text-text-secondary capitalize">{o.selection}</td>
                        <td className="py-2 text-right font-label text-text-primary">{o.price_decimal.toFixed(2)}</td>
                        <td className="py-2 text-right text-text-secondary">
                          {formatProbability(o.implied_probability)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="mt-4 disclaimer">
              Implied probability shown after margin removal. BetLens does not accept bets.
            </p>
          </div>
        )}

        {/* Live tab */}
        {tab === "live" && (
          <div className="card text-center py-8">
            {isLive ? (
              <p className="text-body-sm text-text-secondary">
                Live events stream coming soon. Refresh for latest score.
              </p>
            ) : (
              <p className="text-body-sm text-text-secondary">
                {isFinished ? "Match has finished." : "Match has not started yet."}
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}