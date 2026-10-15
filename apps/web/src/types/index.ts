// ─── Core domain types ────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  role: "user" | "admin";
  plan: "free" | "pro";
  locale: string;
  timezone: string;
  odds_format: "decimal" | "fractional" | "american";
  onboarding_completed: boolean;
  email_verified_at: string | null;
  created_at: string;
}

export interface Competition {
  id: string;
  name: string;
  slug: string;
  country: string;
  type: "league" | "cup";
  logo_url: string | null;
  sport_code: "football" | "basketball";
}

export interface Team {
  id: string;
  name: string;
  short_name: string;
  slug: string;
  country: string;
  logo_url: string | null;
  sport_code: string;
}

export interface Player {
  id: string;
  name: string;
  position: string;
  team_id: string;
  team_name: string;
  jersey_number: number | null;
  nationality: string;
  photo_url: string | null;
  birth_date: string | null;
}

export interface Match {
  id: string;
  competition_id: string;
  round: string;
  kickoff_at: string;
  status: "scheduled" | "live" | "finished" | "postponed" | "cancelled";
  home_team_id: string;
  home_team_name: string;
  home_team_logo: string | null;
  away_team_id: string;
  away_team_name: string;
  away_team_logo: string | null;
  home_score: number | null;
  away_score: number | null;
  minute: number | null;
  venue_name: string | null;
}

export interface Standing {
  rank: number;
  team_id: string;
  team_name: string;
  team_logo: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  form: string;
}

// ─── Predictions ──────────────────────────────────────────────────────────────

export interface Factor {
  label: string;
  direction: "up" | "down";
  impact: number;
}

export interface PredictionMarkets {
  home?: number;
  draw?: number;
  away?: number;
  totals?: Array<{ line: number; over: number; under: number }>;
  btts?: { yes: number; no: number };
  correct_score?: Array<{ score: string; p: number }>;
  cards?: { any_red: number; expected_yellows: number };
}

export interface MatchPrediction {
  match_id: string;
  model_version: string;
  generated_at: string;
  confidence: "low" | "medium" | "high";
  markets: PredictionMarkets;
  expected_goals: { home: number; away: number } | null;
  factors: Factor[];
  players: PlayerPrediction[];
}

export interface PlayerPrediction {
  player_id: string;
  match_id: string;
  anytime_scorer: number;
  assist: number;
  decisive: number;
  carded: number;
  confidence: "low" | "medium" | "high";
  factors: Factor[];
}

// ─── Odds & Value ─────────────────────────────────────────────────────────────

export interface OddsEntry {
  id: string;
  bookmaker: string;
  market: string;
  selection: string;
  price_decimal: number;
  implied_probability: number;
  captured_at: string;
}

export interface ValueOpportunity {
  id: string;
  match_id: string;
  market: string;
  selection: string;
  model_probability: number;
  implied_probability: number;
  edge: number;
  expected_value: number;
  confidence: "low" | "medium" | "high";
  bookmaker: string;
  price_decimal: number | null;
  kickoff_at: string | null;
}

// ─── Bet tracker ──────────────────────────────────────────────────────────────

export interface Bet {
  id: string;
  market: string;
  selection: string;
  stake: number;
  odds_decimal: number;
  status: "pending" | "won" | "lost" | "void";
  profit: number | null;
  placed_at: string;
  notes: string;
}

export interface BetStats {
  total_bets: number;
  won: number;
  lost: number;
  total_stake: number;
  total_profit: number;
  roi: number;
  hit_rate: number;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls: unknown[];
  created_at: string;
}

// ─── Notifications ────────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  channel: string;
  read_at: string | null;
  created_at: string;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  code: string;
  message: string;
  details: unknown;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface DashboardTeamItem {
  team_id: string;
  team_name: string;
  team_logo: string | null;
  next_match: { id: string; kickoff_at: string; status: string } | null;
  last_result: { id: string; home_score: number; away_score: number } | null;
  win_probability: number | null;
}

export interface Dashboard {
  greeting: string;
  your_teams: DashboardTeamItem[];
  today_matches: Match[];
  top_probabilities: MatchPrediction[];
  value_spotlight: ValueOpportunity[];
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResult {
  type: "team" | "player" | "competition" | "match";
  id: string;
  name: string;
  subtitle: string | null;
  logo_url: string | null;
}