import Link from "next/link";
import { TrendingUp, Shield, Zap, BarChart3, MessageSquare, Star } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between max-w-content mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-button flex items-center justify-center">
            <span className="text-white font-heading text-body-sm">B</span>
          </div>
          <span className="text-section-title font-heading text-accent">BetLens</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="btn-ghost">
            Log in
          </Link>
          <Link href="/signup" className="btn-primary">
            Get started free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-content mx-auto px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 bg-accent-tint text-accent text-caption font-label px-3 py-1 rounded-full mb-6">
          <Star className="w-3 h-3" aria-hidden />
          Football & NBA analytics
        </div>
        <h1 className="text-hero font-heading text-text-primary mb-6 max-w-3xl mx-auto">
          Understand the real chances of sporting events
        </h1>
        <p className="text-body text-text-secondary max-w-xl mx-auto mb-8">
          Calibrated probabilities, odds comparison, and AI-powered analysis for Premier League,
          La Liga, Serie A, Bundesliga, Ligue 1, Champions League, and NBA.
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link href="/signup" className="btn-primary text-body">
            Create free account
          </Link>
          <Link href="/competitions" className="btn-secondary text-body">
            Browse competitions
          </Link>
        </div>
        <p className="mt-4 text-caption text-text-secondary">
          18+ only. Analytics tool only — no bets accepted, no money held.
        </p>
      </section>

      {/* Features */}
      <section className="bg-surface py-20">
        <div className="max-w-content mx-auto px-6">
          <h2 className="text-page-title font-heading text-text-primary text-center mb-12">
            Everything you need to understand the numbers
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {[
              {
                icon: BarChart3,
                title: "Calibrated Probabilities",
                desc: "Dixon-Coles Poisson model with LightGBM second stage. Every probability has a plain-language explanation.",
              },
              {
                icon: TrendingUp,
                title: "Value Detection",
                desc: "Compare model probabilities against bookmaker implied odds. Value flags appear when edge ≥ 3pp.",
              },
              {
                icon: MessageSquare,
                title: "AI Assistant",
                desc: "Ask questions in natural language. Every number the assistant gives comes from real platform data — no hallucinations.",
              },
              {
                icon: Zap,
                title: "Live Scores & Updates",
                desc: "Real-time match events, live win probability updates, and lineup confirmations via Server-Sent Events.",
              },
              {
                icon: Shield,
                title: "Model Transparency",
                desc: "Public Model Performance page showing accuracy, calibration curves, and number of predictions evaluated.",
              },
              {
                icon: Star,
                title: "Accumulator Analyzer",
                desc: "Combined probability, expected value, and risk label for multi-selection slips. Correlated selections trigger a warning.",
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card">
                <div className="w-10 h-10 bg-accent-tint rounded-button flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-accent" aria-hidden />
                </div>
                <h3 className="text-section-title font-heading text-text-primary mb-2">{title}</h3>
                <p className="text-body-sm text-text-secondary">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Competitions */}
      <section className="max-w-content mx-auto px-6 py-20">
        <h2 className="text-page-title font-heading text-text-primary text-center mb-4">
          Competitions covered
        </h2>
        <p className="text-body text-text-secondary text-center mb-10">
          9 competitions at launch, with more planned.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
          {[
            "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
            "Champions League", "Europa League", "Conference League", "NBA",
          ].map((comp) => (
            <div
              key={comp}
              className="card text-center text-body-sm font-label text-text-primary py-4"
            >
              {comp}
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-surface py-20">
        <div className="max-w-content mx-auto px-6">
          <h2 className="text-page-title font-heading text-text-primary text-center mb-12">
            Simple pricing
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-2xl mx-auto">
            {/* Free */}
            <div className="card">
              <h3 className="text-section-title font-heading text-text-primary mb-1">Free</h3>
              <p className="text-page-title font-heading text-accent mb-4">£0</p>
              <ul className="space-y-2 text-body-sm text-text-secondary mb-6">
                {[
                  "Standings, fixtures, results",
                  "Headline match probability",
                  "3 full predictions per day",
                  "10 assistant messages per day",
                  "Bet tracker",
                  "Accumulator analyzer (3 selections)",
                ].map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className="text-positive">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/signup" className="btn-secondary w-full text-center block">
                Get started
              </Link>
            </div>

            {/* Pro */}
            <div className="card border-accent">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-section-title font-heading text-text-primary">Pro</h3>
                <span className="badge badge-high">Popular</span>
              </div>
              <p className="text-page-title font-heading text-accent mb-4">
                £9.99<span className="text-body text-text-secondary">/mo</span>
              </p>
              <ul className="space-y-2 text-body-sm text-text-secondary mb-6">
                {[
                  "Everything in Free",
                  "All markets & player probabilities",
                  "Full value finder",
                  "Unlimited accumulator analyzer",
                  "200 assistant messages per day",
                  "Push notifications & custom triggers",
                  "Advanced bet tracker statistics",
                ].map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className="text-positive">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/signup" className="btn-primary w-full text-center block">
                Start Pro trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10">
        <div className="max-w-content mx-auto px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-accent rounded flex items-center justify-center">
                <span className="text-white text-caption font-heading">B</span>
              </div>
              <span className="font-heading text-accent">BetLens</span>
            </div>
            <div className="flex items-center gap-4 text-body-sm text-text-secondary">
              <Link href="/legal/terms" className="hover:text-accent">Terms</Link>
              <Link href="/legal/privacy" className="hover:text-accent">Privacy</Link>
              <Link href="/legal/cookies" className="hover:text-accent">Cookies</Link>
              <Link href="/model" className="hover:text-accent">Model</Link>
            </div>
          </div>
          <div className="mt-6 text-center text-caption text-text-secondary space-y-1">
            <p>
              18+ only. BetLens is an analytics tool. It never accepts bets or holds money.
            </p>
            <p>
              Estimates based on statistical models. No outcome is guaranteed.
            </p>
            <p>
              Problem gambling?{" "}
              <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer" className="underline hover:text-accent">
                BeGambleAware
              </a>{" "}
              ·{" "}
              <a href="https://www.gamcare.org.uk" target="_blank" rel="noopener noreferrer" className="underline hover:text-accent">
                GamCare
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}