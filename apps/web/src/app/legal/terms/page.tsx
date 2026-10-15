import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";

export default function TermsPage() {
  return (
    <AppShell>
      <div className="max-w-2xl space-y-6">
        <h1 className="text-page-title font-heading text-text-primary">Terms of Service</h1>
        <div className="prose prose-sm text-text-secondary space-y-4">
          <p>
            BetLens is an analytics and decision-support tool. It never accepts bets, never holds
            user money, and never promises profit.
          </p>
          <h2 className="text-section-title font-heading text-text-primary">Eligibility</h2>
          <p>
            You must be 18 years of age or older to use BetLens. By creating an account you confirm
            that you meet this requirement.
          </p>
          <h2 className="text-section-title font-heading text-text-primary">No betting services</h2>
          <p>
            BetLens does not facilitate, accept, or process bets. All probabilities and odds
            comparisons are for informational purposes only.
          </p>
          <h2 className="text-section-title font-heading text-text-primary">Accuracy disclaimer</h2>
          <p>
            All probabilities are estimates based on statistical models. No outcome is guaranteed.
            Past model performance does not guarantee future accuracy.
          </p>
          <h2 className="text-section-title font-heading text-text-primary">Responsible gambling</h2>
          <p>
            If you or someone you know has a gambling problem, please seek help from{" "}
            <a href="https://www.begambleaware.org" className="text-accent underline" target="_blank" rel="noopener noreferrer">
              BeGambleAware
            </a>{" "}
            or{" "}
            <a href="https://www.gamcare.org.uk" className="text-accent underline" target="_blank" rel="noopener noreferrer">
              GamCare
            </a>.
          </p>
        </div>
      </div>
    </AppShell>
  );
}