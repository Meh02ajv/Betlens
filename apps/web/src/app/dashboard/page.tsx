"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usersApi } from "@/lib/api";
import { formatKickoff, formatProbability } from "@/lib/utils";
import { AppShell } from "@/components/layout/AppShell";
import { MatchCard } from "@/components/ui/MatchCard";
import { Logo } from "@/components/ui/Logo";
import { StatTile } from "@/components/ui/StatTile";
import { Skeleton } from "@/components/ui/Skeleton";
import type { Dashboard } from "@/types";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    setLoading(true);
    setError(null);
    usersApi
      .getDashboard(selectedDate)
      .then(setDashboard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedDate]);

  return (
    <AppShell>
      <div className="space-y-8">
        {/* Greeting */}
        <div>
          {loading ? (
            <Skeleton className="h-8 w-48" />
          ) : (
            <h1 className="text-page-title font-heading text-text-primary">
              {dashboard?.greeting ?? "Welcome back!"}
            </h1>
          )}
          <p className="text-body-sm text-text-secondary mt-1">
            {new Date().toLocaleDateString("en-GB", {
              weekday: "long",
              day: "numeric",
              month: "long",
            })}
          </p>
        </div>

        {error && (
          <div className="card border-live text-live text-body-sm">
            Failed to load dashboard: {error}
          </div>
        )}

        {/* Your teams */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-section-title font-heading text-text-primary">Your teams</h2>
            <Link href="/settings" className="text-body-sm text-accent hover:underline">
              Edit teams
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 rounded-card" />
              ))}
            </div>
          ) : dashboard?.your_teams.length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-body-sm text-text-secondary mb-3">
                You haven&apos;t followed any teams yet.
              </p>
              <Link href="/onboarding" className="btn-primary">
                Choose your teams
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {dashboard?.your_teams.map((item) => (
                <Link
                  key={item.team_id}
                  href={`/teams/${item.team_id}`}
                  className="card hover:border-accent-hover transition-colors"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Logo src={item.team_logo} alt={item.team_name} className="w-8 h-8" />
                    <span className="font-label text-text-primary">{item.team_name}</span>
                  </div>
                  {item.next_match && (
                    <p className="text-caption text-text-secondary">
                      Next: {formatKickoff(item.next_match.kickoff_at)}
                    </p>
                  )}
                  {item.win_probability !== null && item.win_probability !== undefined && (
                    <p className="text-caption text-accent mt-1 tabular-nums">
                      Win prob: {formatProbability(item.win_probability)}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </section>

        {/* Matches for selected date */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-section-title font-heading text-text-primary">Matches</h2>
            <div className="flex items-center gap-3">
              <label htmlFor="dashboard-date" className="text-body-sm text-text-secondary">Date</label>
              <input
                id="dashboard-date"
                type="date"
                className="input w-auto"
                value={selectedDate}
                onChange={(event) => setSelectedDate(event.target.value)}
              />
              <Link href="/competitions" className="text-body-sm text-accent hover:underline">
                All competitions
              </Link>
            </div>
          </div>

          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 rounded-card" />
              ))}
            </div>
          ) : !dashboard?.today_matches.length ? (
            <div className="card text-center py-8">
              <p className="text-body-sm text-text-secondary">No matches today.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {dashboard.today_matches.slice(0, 10).map((match) => (
                <MatchCard key={match.id} match={match} />
              ))}
            </div>
          )}
        </section>

        {/* Value spotlight */}
        {dashboard?.value_spotlight && dashboard.value_spotlight.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-section-title font-heading text-text-primary">
                Value spotlight
              </h2>
              <Link href="/value" className="text-body-sm text-accent hover:underline">
                See all
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {dashboard.value_spotlight.map((v) => (
                <div key={v.id} className="card border-l-4 border-l-positive">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-body-sm font-label text-text-primary capitalize">
                      {v.market} — {v.selection}
                    </span>
                    <span className="text-caption text-positive font-label tabular-nums">
                      +{(v.edge * 100).toFixed(1)}pp
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-caption text-text-secondary tabular-nums">
                    <span>Model: {formatProbability(v.model_probability)}</span>
                    <span>Market: {formatProbability(v.implied_probability)}</span>
                  </div>
                  <p className="mt-2 text-caption text-text-secondary disclaimer">
                    Estimates based on statistical models. No outcome is guaranteed.
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Quick ask */}
        <section>
          <div className="card bg-accent-tint border-accent">
            <h2 className="text-section-title font-heading text-accent mb-2">Quick ask</h2>
            <p className="text-body-sm text-text-secondary mb-3">
              Ask the AI assistant anything about tonight&apos;s matches.
            </p>
            <Link href="/assistant" className="btn-primary">
              Open assistant
            </Link>
          </div>
        </section>
      </div>
    </AppShell>
  );
}