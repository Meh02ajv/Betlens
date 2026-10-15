"use client";

import { useEffect, useState } from "react";
import { oddsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { ConfidenceBadge } from "@/components/ui/ConfidenceBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatProbability, formatKickoff } from "@/lib/utils";
import type { ValueOpportunity } from "@/types";

export default function ValuePage() {
  const [opportunities, setOpportunities] = useState<ValueOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [minEdge, setMinEdge] = useState(0.03);

  const load = async () => {
    setLoading(true);
    const data = await oddsApi.getValueOpportunities({ min_edge: minEdge });
    setOpportunities(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [minEdge]);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-page-title font-heading text-text-primary mb-1">Value Finder</h1>
          <p className="text-body-sm text-text-secondary">
            Matches where model probability exceeds bookmaker implied probability by at least{" "}
            {(minEdge * 100).toFixed(0)} percentage points.
          </p>
        </div>

        {/* Filter */}
        <div className="card flex items-center gap-4">
          <label className="text-body-sm font-label text-text-primary">Min edge:</label>
          <select
            value={minEdge}
            onChange={(e) => setMinEdge(parseFloat(e.target.value))}
            className="input w-32"
          >
            <option value={0.03}>3pp</option>
            <option value={0.05}>5pp</option>
            <option value={0.08}>8pp</option>
            <option value={0.10}>10pp</option>
          </select>
        </div>

        {/* Results */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24 rounded-card" />)}
          </div>
        ) : opportunities.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-body-sm text-text-secondary">
              No value opportunities found with the current filters.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {opportunities.map((vo) => (
              <div key={vo.id} className="card border-l-4 border-l-positive">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-label text-text-primary capitalize">
                        {vo.market} — {vo.selection}
                      </span>
                      <ConfidenceBadge confidence={vo.confidence} />
                    </div>
                    {vo.kickoff_at && (
                      <p className="text-caption text-text-secondary">
                        {formatKickoff(vo.kickoff_at)}
                      </p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-section-title font-heading text-positive tabular-nums">
                      +{(vo.edge * 100).toFixed(1)}pp
                    </p>
                    <p className="text-caption text-text-secondary">edge</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-body-sm font-label text-accent tabular-nums">
                      {formatProbability(vo.model_probability)}
                    </p>
                    <p className="text-caption text-text-secondary">Model</p>
                  </div>
                  <div>
                    <p className="text-body-sm font-label text-text-primary tabular-nums">
                      {formatProbability(vo.implied_probability)}
                    </p>
                    <p className="text-caption text-text-secondary">Market</p>
                  </div>
                  <div>
                    <p className="text-body-sm font-label text-text-primary tabular-nums">
                      {vo.price_decimal?.toFixed(2) ?? "—"}
                    </p>
                    <p className="text-caption text-text-secondary">{vo.bookmaker}</p>
                  </div>
                </div>

                <p className="mt-3 disclaimer">
                  Estimates based on statistical models. No outcome is guaranteed.
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}