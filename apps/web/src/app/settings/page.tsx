"use client";

import { useEffect, useState } from "react";
import { usersApi, billingApi } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/Skeleton";
import type { User } from "@/types";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<Pick<User, "name" | "timezone" | "odds_format" | "locale">>({
    name: "",
    timezone: "",
    odds_format: "decimal",
    locale: "en",
  });

  useEffect(() => {
    usersApi.getProfile().then((u) => {
      setUser(u);
      setForm({ name: u.name, timezone: u.timezone, odds_format: u.odds_format, locale: u.locale });
    }).finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const updated = await usersApi.updateProfile(form);
    setUser(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    setSaving(false);
  };

  const handleUpgrade = async () => {
    const { url } = await billingApi.createCheckout();
    if (url) window.location.href = url;
    else alert("Stripe not configured. Set STRIPE_SECRET_KEY to enable billing.");
  };

  return (
    <AppShell>
      <div className="max-w-xl space-y-8">
        <h1 className="text-page-title font-heading text-text-primary">Settings</h1>

        {loading ? (
          <Skeleton className="h-64 rounded-card" />
        ) : (
          <>
            {/* Profile */}
            <div className="card">
              <h2 className="text-section-title font-heading text-text-primary mb-4">Profile</h2>
              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-body-sm font-label text-text-primary mb-1">Name</label>
                  <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div>
                  <label className="block text-body-sm font-label text-text-primary mb-1">Email</label>
                  <input className="input bg-surface" value={user?.email ?? ""} disabled />
                  <p className="mt-1 text-caption text-text-secondary">Email cannot be changed.</p>
                </div>
                <div>
                  <label className="block text-body-sm font-label text-text-primary mb-1">Odds format</label>
                  <select className="input" value={form.odds_format} onChange={(e) => setForm({ ...form, odds_format: e.target.value as User["odds_format"] })}>
                    <option value="decimal">Decimal (2.50)</option>
                    <option value="fractional">Fractional (3/2)</option>
                    <option value="american">American (+150)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-body-sm font-label text-text-primary mb-1">Time zone</label>
                  <input className="input" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} placeholder="Europe/London" />
                </div>
                <button type="submit" disabled={saving} className="btn-primary">
                  {saving ? "Saving…" : saved ? "Saved ✓" : "Save changes"}
                </button>
              </form>
            </div>

            {/* Plan */}
            <div className="card">
              <h2 className="text-section-title font-heading text-text-primary mb-2">Plan</h2>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-label text-text-primary capitalize">{user?.plan} plan</p>
                  <p className="text-caption text-text-secondary">
                    {user?.plan === "free" ? "Upgrade to Pro for full access." : "You have full Pro access."}
                  </p>
                </div>
                {user?.plan === "free" && (
                  <button onClick={handleUpgrade} className="btn-primary">Upgrade to Pro</button>
                )}
                {user?.plan === "pro" && (
                  <button onClick={async () => {
                    const { url } = await billingApi.createPortal();
                    if (url) window.location.href = url;
                  }} className="btn-secondary">Manage billing</button>
                )}
              </div>
            </div>

            {/* Privacy */}
            <div className="card">
              <h2 className="text-section-title font-heading text-text-primary mb-2">Privacy</h2>
              <div className="space-y-3">
                <button onClick={() => usersApi.exportData()} className="btn-secondary w-full text-left">
                  Export my data
                </button>
                <button
                  onClick={async () => {
                    if (confirm("Are you sure? This will permanently delete your account.")) {
                      await usersApi.deleteAccount();
                      window.location.href = "/";
                    }
                  }}
                  className="w-full text-left px-4 py-2 text-body-sm text-live border border-live rounded-button hover:bg-red-50 transition-colors"
                >
                  Delete account
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}