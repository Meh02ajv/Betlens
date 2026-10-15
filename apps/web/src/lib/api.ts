/**
 * BetLens API client.
 * All requests go through this module — never call fetch() directly in components.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// ─── Token storage ────────────────────────────────────────────────────────────

const TOKEN_KEY = "betlens_access_token";
const REFRESH_KEY = "betlens_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

interface RequestOptions extends RequestInit {
  auth?: boolean;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { auth = true, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (auth) {
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (response.status === 401 && auth) {
    // Try to refresh
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      const retryResponse = await fetch(`${API_BASE}${path}`, {
        ...fetchOptions,
        headers,
      });
      if (!retryResponse.ok) {
        clearTokens();
        throw new ApiError(retryResponse.status, "Session expired");
      }
      return retryResponse.json() as Promise<T>;
    } else {
      clearTokens();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.replace("/login");
      }
      throw new ApiError(401, "Session expired");
    }
  }

  if (!response.ok) {
    let errorData: { message?: string; detail?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore
    }
    throw new ApiError(
      response.status,
      errorData.message ?? errorData.detail ?? "Request failed"
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem(REFRESH_KEY);
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  signup: (data: {
    email: string;
    password: string;
    name: string;
    is_adult_confirmed: boolean;
  }) =>
    apiFetch<{ message: string }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
      auth: false,
    }),

  login: (email: string, password: string) =>
    apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    }),

  logout: () =>
    apiFetch<{ message: string }>("/auth/logout", { method: "POST" }),

  forgotPassword: (email: string) =>
    apiFetch<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
      auth: false,
    }),

  resetPassword: (token: string, new_password: string) =>
    apiFetch<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
      auth: false,
    }),
};

// ─── Users ────────────────────────────────────────────────────────────────────

export const usersApi = {
  getProfile: () => apiFetch<import("@/types").User>("/me"),
  updateProfile: (data: Partial<import("@/types").User>) =>
    apiFetch<import("@/types").User>("/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getDashboard: (date?: string) =>
    apiFetch<import("@/types").Dashboard>(`/me/dashboard${date ? `?date=${date}` : ""}`),
  getFavorites: () => apiFetch<{ favorites: import("@/types").SearchResult[] }>("/me/favorites"),
  setFavorites: (favorites: Array<{ entity_type: string; entity_id: string }>) =>
    apiFetch("/me/favorites", {
      method: "PUT",
      body: JSON.stringify({ favorites }),
    }),
  deleteAccount: () => apiFetch("/me", { method: "DELETE" }),
  exportData: () => apiFetch("/me/export"),
};

// ─── Sports data ──────────────────────────────────────────────────────────────

export const sportsApi = {
  getCompetitions: () =>
    apiFetch<import("@/types").Competition[]>("/competitions", { auth: false }),
  getCompetition: (slug: string) =>
    apiFetch<import("@/types").Competition>(`/competitions/${slug}`, { auth: false }),
  getStandings: (slug: string) =>
    apiFetch<import("@/types").Standing[]>(`/live/competitions/${slug}/standings`, { auth: false }),
  getFixtures: (slug: string, status?: string, matchday?: number) =>
    apiFetch<import("@/types").Match[]>(
      `/live/competitions/${slug}/fixtures?${new URLSearchParams({
        ...(status ? { status } : {}),
        ...(matchday ? { matchday: String(matchday) } : {}),
      }).toString()}`,
      { auth: false }
    ),
  getLiveNbaGames: (date?: string) =>
    apiFetch<import("@/types").Match[]>(
      `/live/nba/games${date ? `?date=${date}` : ""}`,
      { auth: false }
    ),
  getLiveNbaTeams: () =>
    apiFetch<Array<import("@/types").Team & { conference?: string; division?: string }>>(
      "/live/nba/teams",
      { auth: false }
    ),
  getOutlook: (slug: string) =>
    apiFetch<unknown[]>(`/competitions/${slug}/outlook`, { auth: false }),
  getTeam: (id: string) =>
    apiFetch<import("@/types").Team>(`/teams/${id}`, { auth: false }),
  getTeamFixtures: (id: string) =>
    apiFetch<import("@/types").Match[]>(`/teams/${id}/fixtures`, { auth: false }),
  getSquad: (id: string) =>
    apiFetch<import("@/types").Player[]>(`/teams/${id}/squad`, { auth: false }),
  getMatches: (params?: { date?: string; competition?: string; team?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return apiFetch<import("@/types").Match[]>(`/matches${qs ? `?${qs}` : ""}`, { auth: false });
  },
  getMatch: (id: string) =>
    apiFetch<import("@/types").Match>(`/matches/${id}`, { auth: false }),
  getMatchLineups: (id: string) =>
    apiFetch<unknown[]>(`/matches/${id}/lineups`, { auth: false }),
  getMatchEvents: (id: string) =>
    apiFetch<unknown[]>(`/matches/${id}/events`, { auth: false }),
  getPlayer: (id: string) =>
    apiFetch<import("@/types").Player>(`/players/${id}`, { auth: false }),
  search: (q: string) =>
    apiFetch<import("@/types").SearchResult[]>(`/search?q=${encodeURIComponent(q)}`, { auth: false }),
};

// ─── Predictions ──────────────────────────────────────────────────────────────

export const predictionsApi = {
  getMatchPredictions: (matchId: string) =>
    apiFetch<import("@/types").MatchPrediction>(`/matches/${matchId}/predictions`),
  getPlayerPredictions: (playerId: string, matchId?: string) =>
    apiFetch<import("@/types").PlayerPrediction>(
      `/players/${playerId}/predictions${matchId ? `?match_id=${matchId}` : ""}`
    ),
  getModelPerformance: () =>
    apiFetch<unknown>("/model/performance", { auth: false }),
};

// ─── Odds & Value ─────────────────────────────────────────────────────────────

export const oddsApi = {
  getMatchOdds: (matchId: string) =>
    apiFetch<import("@/types").OddsEntry[]>(`/matches/${matchId}/odds`),
  getValueOpportunities: (params?: { competition?: string; min_edge?: number }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return apiFetch<import("@/types").ValueOpportunity[]>(`/value${qs ? `?${qs}` : ""}`);
  },
  analyzeSlip: (selections: unknown[]) =>
    apiFetch<{
      combined_probability: number;
      combined_odds: number;
      expected_value: number;
      risk_label: string;
      correlated_warning: boolean;
    }>("/slips/analyze", {
      method: "POST",
      body: JSON.stringify(selections),
    }),
  getBets: () => apiFetch<import("@/types").Bet[]>("/bets"),
  createBet: (data: Partial<import("@/types").Bet>) =>
    apiFetch<{ id: string }>("/bets", { method: "POST", body: JSON.stringify(data) }),
  updateBet: (id: string, data: Partial<import("@/types").Bet>) =>
    apiFetch<import("@/types").Bet>(`/bets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteBet: (id: string) => apiFetch(`/bets/${id}`, { method: "DELETE" }),
  getBetStats: () => apiFetch<import("@/types").BetStats>("/bets/stats"),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const chatApi = {
  getSessions: () => apiFetch<import("@/types").ChatSession[]>("/chat/sessions"),
  createSession: () =>
    apiFetch<{ id: string; title: string; suggested_prompts: string[] }>("/chat/sessions", {
      method: "POST",
    }),
  renameSession: (id: string, title: string) =>
    apiFetch(`/chat/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  deleteSession: (id: string) =>
    apiFetch(`/chat/sessions/${id}`, { method: "DELETE" }),
  getMessages: (sessionId: string) =>
    apiFetch<import("@/types").ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),
};

// ─── Notifications ────────────────────────────────────────────────────────────

export const notificationsApi = {
  getNotifications: () =>
    apiFetch<import("@/types").Notification[]>("/notifications"),
  markRead: (id: string) =>
    apiFetch(`/notifications/${id}/read`, { method: "PATCH" }),
  getSettings: () => apiFetch("/notifications/settings"),
  updateSettings: (data: unknown) =>
    apiFetch("/notifications/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// ─── Billing ─────────────────────────────────────────────────────────────────

export const billingApi = {
  createCheckout: () => apiFetch<{ url: string | null }>("/billing/checkout", { method: "POST" }),
  createPortal: () => apiFetch<{ url: string | null }>("/billing/portal", { method: "POST" }),
};