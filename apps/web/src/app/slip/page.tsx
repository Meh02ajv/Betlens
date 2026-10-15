"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { oddsApi, sportsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import type { Match } from "@/types";

interface Selection {
  id: string;
  match_id: string;
  label: string;
  probability: string;
  odds_decimal: string;
}

const emptySelection = (): Selection => ({
  id: crypto.randomUUID(),
  match_id: "",
  label: "",
  probability: "50",
  odds_decimal: "2.00",
});

export default function SlipPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [selections, setSelections] = useState<Selection[]>([emptySelection()]);
  const [result, setResult] = useState<Awaited<ReturnType<typeof oddsApi.analyzeSlip>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    sportsApi
      .getMatches()
      .then(setMatches)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const updateSelection = (id: string, patch: Partial<Selection>) => {
    setSelections((current) =>
      current.map((selection) =>
        selection.id === id ? { ...selection, ...patch } : selection
      )
    );
    setResult(null);
  };

  const selectMatch = (id: string, matchId: string) => {
    const match = matches.find((item) => item.id === matchId);
    updateSelection(id, {
      match_id: matchId,
      label: match ? `${match.home_team_name} vs ${match.away_team_name}` : "",
    });
  };

  const analyze = async () => {
    setError(null);
    setAnalyzing(true);
    try {
      const payload = selections.map((selection) => ({
        match_id: selection.match_id || undefined,
        market: "custom",
        selection: selection.label || "Selection",
        probability: Number(selection.probability) / 100,
        odds_decimal: Number(selection.odds_decimal),
      }));
      setResult(await oddsApi.analyzeSlip(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not analyze slip");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-page-title font-heading text-text-primary">Slip analyzer</h1>
          <p className="text-body-sm text-text-secondary mt-1">
            Combine selections and review the estimated probability and risk.
          </p>
        </div>

        {error && <div className="card border-live text-live text-body-sm">{error}</div>}

        <div className="space-y-3">
          {selections.map((selection, index) => (
            <div key={selection.id} className="card space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-label text-text-primary">Selection {index + 1}</h2>
                {selections.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setSelections((current) => current.filter((item) => item.id !== selection.id))}
                    className="text-text-secondary hover:text-live"
                    aria-label={`Remove selection ${index + 1}`}
                  >
                    <Trash2 className="w-4 h-4" aria-hidden />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="md:col-span-3 text-body-sm text-text-secondary">
                  Match
                  <select
                    className="input mt-1"
                    value={selection.match_id}
                    disabled={loading}
                    onChange={(event) => selectMatch(selection.id, event.target.value)}
                  >
                    <option value="">Choose a match</option>
                    {matches.map((match) => (
                      <option key={match.id} value={match.id}>
                        {match.home_team_name} vs {match.away_team_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-body-sm text-text-secondary">
                  Selection
                  <input
                    className="input mt-1"
                    value={selection.label}
                    onChange={(event) => updateSelection(selection.id, { label: event.target.value })}
                    placeholder="Home win"
                  />
                </label>
                <label className="text-body-sm text-text-secondary">
                  Probability (%)
                  <input
                    className="input mt-1"
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={selection.probability}
                    onChange={(event) => updateSelection(selection.id, { probability: event.target.value })}
                  />
                </label>
                <label className="text-body-sm text-text-secondary">
                  Decimal odds
                  <input
                    className="input mt-1"
                    type="number"
                    min="1"
                    step="0.01"
                    value={selection.odds_decimal}
                    onChange={(event) => updateSelection(selection.id, { odds_decimal: event.target.value })}
                  />
                </label>
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="btn-secondary flex items-center gap-2"
            onClick={() => setSelections((current) => [...current, emptySelection()])}
          >
            <Plus className="w-4 h-4" aria-hidden />
            Add selection
          </button>
          <button type="button" className="btn-primary" onClick={analyze} disabled={analyzing}>
            {analyzing ? "Analyzing..." : "Analyze slip"}
          </button>
        </div>

        {result && (
          <div className="card border-accent grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Combined probability" value={`${(result.combined_probability * 100).toFixed(1)}%`} />
            <Metric label="Combined odds" value={result.combined_odds.toFixed(2)} />
            <Metric label="Expected value" value={`${(result.expected_value * 100).toFixed(1)}%`} />
            <Metric label="Risk" value={result.risk_label} />
            {result.correlated_warning && (
              <p className="col-span-full text-body-sm text-live">
                Multiple selections use the same match and may be correlated.
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-caption text-text-secondary">{label}</p>
      <p className="text-section-title font-heading text-accent mt-1">{value}</p>
    </div>
  );
}