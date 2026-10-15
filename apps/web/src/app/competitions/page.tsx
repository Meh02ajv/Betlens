"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { sportsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/Skeleton";
import { Logo } from "@/components/ui/Logo";
import type { Competition } from "@/types";

export default function CompetitionsPage() {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sportsApi.getCompetitions().then(setCompetitions).finally(() => setLoading(false));
  }, []);

  const football = competitions.filter((c) => c.sport_code === "football");
  const basketball = competitions.filter((c) => c.sport_code === "basketball");

  return (
    <AppShell>
      <div className="space-y-8">
        <h1 className="text-page-title font-heading text-text-primary">Competitions</h1>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-20 rounded-card" />
            ))}
          </div>
        ) : (
          <>
            <section>
              <h2 className="text-section-title font-heading text-text-primary mb-4">Football</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {football.map((comp) => (
                  <CompetitionCard key={comp.id} competition={comp} />
                ))}
              </div>
            </section>

            {basketball.length > 0 && (
              <section>
                <h2 className="text-section-title font-heading text-text-primary mb-4">Basketball</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {basketball.map((comp) => (
                    <CompetitionCard key={comp.id} competition={comp} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}

function CompetitionCard({ competition }: { competition: Competition }) {
  return (
    <Link
      href={`/competitions/${competition.slug}`}
      className="card flex items-center gap-4 hover:border-accent-hover transition-colors"
    >
      <Logo src={competition.logo_url} alt={competition.name} className="w-10 h-10 flex-shrink-0" />
      <div className="min-w-0">
        <p className="font-label text-text-primary truncate">{competition.name}</p>
        <p className="text-caption text-text-secondary">{competition.country}</p>
      </div>
    </Link>
  );
}