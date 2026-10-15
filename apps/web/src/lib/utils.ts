import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// ─── Odds formatting ──────────────────────────────────────────────────────────

export function formatOdds(
  decimal: number,
  format: "decimal" | "fractional" | "american" = "decimal"
): string {
  if (format === "decimal") {
    return decimal.toFixed(2);
  }

  if (format === "fractional") {
    const numerator = Math.round((decimal - 1) * 100);
    const denominator = 100;
    const gcd = greatestCommonDivisor(numerator, denominator);
    return `${numerator / gcd}/${denominator / gcd}`;
  }

  if (format === "american") {
    if (decimal >= 2) {
      return `+${Math.round((decimal - 1) * 100)}`;
    } else {
      return `${Math.round(-100 / (decimal - 1))}`;
    }
  }

  return decimal.toFixed(2);
}

function greatestCommonDivisor(a: number, b: number): number {
  return b === 0 ? a : greatestCommonDivisor(b, a % b);
}

// ─── Probability formatting ───────────────────────────────────────────────────

export function formatProbability(p: number, decimals = 0): string {
  return `${(p * 100).toFixed(decimals)}%`;
}

// ─── Date/time formatting ─────────────────────────────────────────────────────

export function formatKickoff(isoString: string, timezone = "UTC"): string {
  const date = new Date(isoString);
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone,
  }).format(date);
}

export function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(isoString));
}

export function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function isToday(isoString: string): boolean {
  const date = new Date(isoString);
  const today = new Date();
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}

// ─── Confidence helpers ───────────────────────────────────────────────────────

export function confidenceColor(confidence: "low" | "medium" | "high"): string {
  return {
    low: "text-text-secondary border-text-secondary",
    medium: "text-accent border-accent",
    high: "text-positive border-positive",
  }[confidence];
}

export function confidenceLabel(confidence: "low" | "medium" | "high"): string {
  return {
    low: "Low confidence — sparse data or major unknowns",
    medium: "Medium confidence — reasonable data, some uncertainty",
    high: "High confidence — sufficient data, lineup confirmed",
  }[confidence];
}

// ─── Form chip helpers ────────────────────────────────────────────────────────

export function parseForm(form: string): Array<"W" | "D" | "L"> {
  return form.split("").filter((c): c is "W" | "D" | "L" =>
    ["W", "D", "L"].includes(c)
  );
}

// ─── Value helpers ────────────────────────────────────────────────────────────

export function hasValue(
  modelProb: number,
  impliedProb: number,
  confidence: string
): boolean {
  const edge = modelProb - impliedProb;
  return edge >= 0.03 && ["medium", "high"].includes(confidence);
}

export function formatEdge(edge: number): string {
  const sign = edge >= 0 ? "+" : "";
  return `${sign}${(edge * 100).toFixed(1)}pp`;
}

// ─── Score helpers ────────────────────────────────────────────────────────────

export function matchResult(
  homeScore: number,
  awayScore: number,
  teamId: string,
  homeTeamId: string
): "W" | "D" | "L" {
  if (homeScore === awayScore) return "D";
  const homeWon = homeScore > awayScore;
  const isHome = teamId === homeTeamId;
  return (homeWon && isHome) || (!homeWon && !isHome) ? "W" : "L";
}