"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { sportsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { MatchCard } from "@/components/ui/MatchCard";
import { FormChips } from "@/components/ui/FormChips";
import { Skeleton, StandingsSkeleton } from "@/components/ui/Skeleton";
import { Logo } from "@/components/ui/Logo";
import type { Competition, Standing, Match } from "@/types";

type Tab = "standings" | "fixtures" | "outlook";

export default function CompetitionPage() {
  const { slug } = useParams<{ slug: string }>();
  const [tab, setTab] = useState<Tab>("standings");
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [fixtures, setFixtures] = useState<Match[]>([]);
  const [outlook, setOutlook] = useState<unknown[]>([]);
  const [matchday, setMatchday] = useState<number | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      sportsApi.getCompetition(slug),
      sportsApi.getStandings(slug),
      sportsApi.getFixtures(slug, undefined, matchday),
    ])
      .then(([comp, st, fx]) => {
        setCompetition(comp as Competition);
        setStandings(st);
        setFixtures(fx);
      })
      .finally(() => setLoading(false));
  }, [slug, matchday]);

  const loadOutlook = async () => {
    if (outlook.length === 0) {
      const data = await sportsApi.getOutlook(slug);
      setOutlook(data);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "standings", label: "Standings" },
    { id: "fixtures", label: "Fixtures" },
    { id: "outlook", label: "Season Outlook" },
  ];

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Logo src={competition?.logo_url} alt={competition?.name ?? "Competition"} className="w-12 h-12" />
          <div>
            {loading ? (
              <Skeleton className="h-8 w-48" />
            ) : (
              <h1 className="text-page-title font-heading text-text-primary">
                {competition?.name}
              </h1>
            )}
            <p className="text-body-sm text-text-secondary">{competition?.country}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border gap-1" role="tablist">
          {tabs.map(({ id, label }) => (
            <button
              key={id}
              role="tab"
              aria-selected={tab === id}
              onClick={() => {
                setTab(id);
                if (id === "outlook") loadOutlook();
              }}
              className={`px-4 py-2 text-body-sm font-label border-b-2 transition-colors ${
                tab === id
                  ? "border-accent text-accent"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Standings */}
        {tab === "standings" && (
          <div>
            {loading ? (
              <StandingsSkeleton />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-body-sm tabular-nums" aria-label="League standings">
                  <thead>
                    <tr className="text-caption text-text-secondary font-label border-b border-border">
                      <th className="text-left py-2 w-8">#</th>
                      <th className="text-left py-2">Team</th>
                      <th className="text-center py-2 w-8">P</th>
                      <th className="text-center py-2 w-8">W</th>
                      <th className="text-center py-2 w-8">D</th>
                      <th className="text-center py-2 w-8">L</th>
                      <th className="text-center py-2 w-10">GD</th>
                      <th className="text-center py-2 w-10 font-heading text-text-primary">Pts</th>
                      <th className="text-center py-2 hidden sm:table-cell">Form</th>
                    </tr>
                  </thead>
                  <tbody>
                    {standings.map((s, i) => (
                      <tr
                        key={s.team_id}
                        className={`border-b border-border hover:bg-surface transition-colors ${
                          i % 2 === 0 ? "" : "bg-surface/50"
                        }`}
                      >
                        <td className="py-2 text-text-secondary">{s.rank}</td>
                        <td className="py-2">
                          <div className="flex items-center gap-2">
                            <Logo src={s.team_logo} alt={s.team_name} className="w-5 h-5" />
                            <span className="font-label text-text-primary">{s.team_name}</span>
                          </div>
                        </td>
                        <td className="py-2 text-center text-text-secondary">{s.played}</td>
                        <td className="py-2 text-center text-text-secondary">{s.won}</td>
                        <td className="py-2 text-center text-text-secondary">{s.drawn}</td>
                        <td className="py-2 text-center text-text-secondary">{s.lost}</td>
                        <td className="py-2 text-center text-text-secondary">
                          {s.goal_difference > 0 ? `+${s.goal_difference}` : s.goal_difference}
                        </td>
                        <td className="py-2 text-center font-heading text-text-primary">{s.points}</td>
                        <td className="py-2 hidden sm:table-cell">
                          <FormChips form={s.form} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Fixtures */}
        {tab === "fixtures" && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <label htmlFor="matchday" className="text-body-sm font-label text-text-primary">
                Matchday
              </label>
              <select
                id="matchday"
                className="input max-w-xs"
                value={matchday ?? ""}
                onChange={(event) => setMatchday(event.target.value ? Number(event.target.value) : undefined)}
              >
                <option value="">All matchdays</option>
                {Array.from({ length: 38 }, (_, index) => index + 1).map((day) => (
                  <option key={day} value={day}>Matchday {day}</option>
                ))}
              </select>
            </div>
            {loading ? (
              [1, 2, 3].map((i) => <Skeleton key={i} className="h-16 rounded-card" />)
            ) : fixtures.length === 0 ? (
              <p className="text-body-sm text-text-secondary text-center py-8">No fixtures found.</p>
            ) : (
              fixtures.map((match) => <MatchCard key={match.id} match={match} />)
            )}
          </div>
        )}

        {/* Outlook */}
        {tab === "outlook" && (
          <div className="space-y-3">
            {(outlook as Array<{ team_id: string; team_name: string; team_logo: string | null; outcome_probabilities: Record<string, number> }>).map((sim) => (
              <div key={sim.team_id} className="card">
                <div className="flex items-center gap-3 mb-3">
                  <Logo src={sim.team_logo} alt={sim.team_name} className="w-6 h-6" />
                  <span className="font-label text-text-primary">{sim.team_name}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(sim.outcome_probabilities).map(([key, prob]) => (
                    <div key={key} className="text-center">
                      <p className="text-section-title font-heading text-accent tabular-nums">
                        {(prob * 100).toFixed(0)}%
                      </p>
                      <p className="text-caption text-text-secondary capitalize">{key.replace("_", " ")}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            <p className="disclaimer text-center">
              Monte Carlo simulation (10,000 runs). Estimates based on statistical models. No outcome is guaranteed.
            </p>
          </div>
        )}
      </div>
    </AppShell>
  );
}