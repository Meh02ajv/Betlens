"use client";

import { useEffect, useState } from "react";
import { predictionsApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/Skeleton";

export default function ModelPage() {
  const [data, setData] = useState<{
    models: Array<{
      name: string;
      sport: string;
      trained_at: string;
      metrics: Record<string, unknown>;
      is_active: boolean;
    }>;
    methodology: Record<string, string>;
    disclaimer: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    predictionsApi
      .getModelPerformance()
      .then((d) => setData(d as typeof data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="space-y-8 max-w-3xl">
        <div>
          <h1 className="text-page-title font-heading text-text-primary mb-2">
            Model Performance
          </h1>
          <p className="text-body text-text-secondary">
            BetLens uses calibrated statistical models. This page shows accuracy metrics,
            methodology, and how predictions are evaluated.
          </p>
        </div>

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 rounded-card" />
            <Skeleton className="h-32 rounded-card" />
          </div>
        ) : data ? (
          <>
            {/* Active models */}
            <section>
              <h2 className="text-section-title font-heading text-text-primary mb-4">
                Active models
              </h2>
              <div className="space-y-4">
                {data.models.map((model) => (
                  <div key={model.name} className="card">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-label text-text-primary">{model.name}</h3>
                        <p className="text-caption text-text-secondary capitalize">{model.sport}</p>
                      </div>
                      {model.is_active && (
                        <span className="badge badge-high">Active</span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      {Object.entries(model.metrics).map(([key, value]) => (
                        <div key={key}>
                          <p className="text-caption text-text-secondary capitalize">
                            {key.replace(/_/g, " ")}
                          </p>
                          <p className="font-label text-text-primary tabular-nums">
                            {typeof value === "number" ? value.toFixed(3) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Methodology */}
            <section>
              <h2 className="text-section-title font-heading text-text-primary mb-4">
                Methodology
              </h2>
              <div className="space-y-4">
                {Object.entries(data.methodology).map(([key, value]) => (
                  <div key={key} className="card">
                    <h3 className="font-label text-text-primary capitalize mb-1">
                      {key.replace(/_/g, " ")}
                    </h3>
                    <p className="text-body-sm text-text-secondary">{value}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* How we evaluate */}
            <section className="card">
              <h2 className="text-section-title font-heading text-text-primary mb-3">
                How we evaluate
              </h2>
              <ul className="space-y-2 text-body-sm text-text-secondary">
                <li>
                  <strong className="text-text-primary">Log loss</strong> — measures how well
                  calibrated the probabilities are. Lower is better.
                </li>
                <li>
                  <strong className="text-text-primary">Brier score</strong> — mean squared error
                  of probability forecasts. Lower is better.
                </li>
                <li>
                  <strong className="text-text-primary">Calibration</strong> — events given 70%
                  should happen roughly 70% of the time.
                </li>
                <li>
                  <strong className="text-text-primary">Walk-forward backtest</strong> — trained on
                  past seasons, tested on future blocks. No data leakage.
                </li>
                <li>
                  <strong className="text-text-primary">Market baseline</strong> — compared against
                  bookmaker implied probabilities after margin removal.
                </li>
              </ul>
            </section>

            <p className="disclaimer text-center">{data.disclaimer}</p>
          </>
        ) : (
          <p className="text-body-sm text-text-secondary">Failed to load model data.</p>
        )}
      </div>
    </AppShell>
  );
}