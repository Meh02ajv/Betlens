"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2, CheckCircle, XCircle } from "lucide-react";
import { oddsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { StatTile } from "@/components/ui/StatTile";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatDate } from "@/lib/utils";
import type { Bet, BetStats } from "@/types";

export default function TrackerPage() {
  const [bets, setBets] = useState<Bet[]>([]);
  const [stats, setStats] = useState<BetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    market: "",
    selection: "",
    stake: "",
    odds_decimal: "",
    notes: "",
  });

  const load = async () => {
    const [b, s] = await Promise.all([oddsApi.getBets(), oddsApi.getBetStats()]);
    setBets(b);
    setStats(s);
  };

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await oddsApi.createBet({
      market: form.market,
      selection: form.selection,
      stake: parseFloat(form.stake),
      odds_decimal: parseFloat(form.odds_decimal),
      notes: form.notes,
    });
    setForm({ market: "", selection: "", stake: "", odds_decimal: "", notes: "" });
    setShowForm(false);
    await load();
  };

  const handleSettle = async (bet: Bet, status: "won" | "lost") => {
    await oddsApi.updateBet(bet.id, { status });
    await load();
  };

  const handleDelete = async (id: string) => {
    await oddsApi.deleteBet(id);
    await load();
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-page-title font-heading text-text-primary">Bet Tracker</h1>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" aria-hidden />
            Log bet
          </button>
        </div>

        <p className="text-body-sm text-text-secondary">
          Personal journal only — no real money moves through BetLens.
        </p>

        {/* Stats */}
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20 rounded-card" />)}
          </div>
        ) : stats && stats.total_bets > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatTile label="Total bets" value={stats.total_bets} />
            <StatTile label="Hit rate" value={`${stats.hit_rate}%`} />
            <StatTile
              label="Total P&L"
              value={`${stats.total_profit >= 0 ? "+" : ""}${stats.total_profit.toFixed(2)}`}
              delta={stats.total_profit}
            />
            <StatTile label="ROI" value={`${stats.roi}%`} delta={stats.roi} />
          </div>
        ) : null}

        {/* Add bet form */}
        {showForm && (
          <div className="card">
            <h2 className="text-section-title font-heading text-text-primary mb-4">Log a bet</h2>
            <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-body-sm font-label text-text-primary mb-1">Market</label>
                <input
                  className="input"
                  placeholder="e.g. 1X2, Over 2.5"
                  value={form.market}
                  onChange={(e) => setForm({ ...form, market: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-body-sm font-label text-text-primary mb-1">Selection</label>
                <input
                  className="input"
                  placeholder="e.g. Home, Over"
                  value={form.selection}
                  onChange={(e) => setForm({ ...form, selection: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-body-sm font-label text-text-primary mb-1">Stake (£)</label>
                <input
                  className="input"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="10.00"
                  value={form.stake}
                  onChange={(e) => setForm({ ...form, stake: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-body-sm font-label text-text-primary mb-1">Decimal odds</label>
                <input
                  className="input"
                  type="number"
                  step="0.01"
                  min="1.01"
                  placeholder="2.10"
                  value={form.odds_decimal}
                  onChange={(e) => setForm({ ...form, odds_decimal: e.target.value })}
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-body-sm font-label text-text-primary mb-1">Notes</label>
                <input
                  className="input"
                  placeholder="Optional notes"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </div>
              <div className="sm:col-span-2 flex gap-3">
                <button type="submit" className="btn-primary">Save bet</button>
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Bets list */}
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 rounded-card" />)}
          </div>
        ) : bets.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-body-sm text-text-secondary mb-3">No bets logged yet.</p>
            <button onClick={() => setShowForm(true)} className="btn-primary">
              Log your first bet
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {bets.map((bet) => (
              <div key={bet.id} className="card flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-label text-text-primary">{bet.market}</span>
                    <span className="text-text-secondary">—</span>
                    <span className="text-text-secondary capitalize">{bet.selection}</span>
                  </div>
                  <div className="flex items-center gap-3 text-caption text-text-secondary tabular-nums">
                    <span>£{bet.stake.toFixed(2)} @ {bet.odds_decimal.toFixed(2)}</span>
                    <span>{formatDate(bet.placed_at)}</span>
                    {bet.profit !== null && (
                      <span className={bet.profit >= 0 ? "text-positive" : "text-live"}>
                        {bet.profit >= 0 ? "+" : ""}£{bet.profit.toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {bet.status === "pending" ? (
                    <>
                      <button
                        onClick={() => handleSettle(bet, "won")}
                        className="text-positive hover:opacity-80"
                        aria-label="Mark as won"
                      >
                        <CheckCircle className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleSettle(bet, "lost")}
                        className="text-live hover:opacity-80"
                        aria-label="Mark as lost"
                      >
                        <XCircle className="w-5 h-5" />
                      </button>
                    </>
                  ) : (
                    <span
                      className={`badge ${
                        bet.status === "won" ? "badge-high" : "badge-low"
                      }`}
                    >
                      {bet.status}
                    </span>
                  )}
                  <button
                    onClick={() => handleDelete(bet.id)}
                    className="text-text-secondary hover:text-live"
                    aria-label="Delete bet"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}