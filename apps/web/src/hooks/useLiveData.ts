"use client";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useLiveStandings(slug: string) {
  return useQuery({
    queryKey: ["live-standings", slug],
    queryFn: () => apiFetch<any[]>(`/live/competitions/${slug}/standings`, { auth: false }),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLiveFixtures(slug: string, status?: string) {
  return useQuery({
    queryKey: ["live-fixtures", slug, status],
    queryFn: () => apiFetch<any[]>(`/live/competitions/${slug}/fixtures${status ? `?status=${status}` : ""}`, { auth: false }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useLiveNBAGames(season: number = 2024) {
  return useQuery({
    queryKey: ["live-nba-games", season],
    queryFn: () => apiFetch<any[]>(`/live/nba/games?season=${season}`, { auth: false }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useLiveOdds(slug: string) {
  return useQuery({
    queryKey: ["live-odds", slug],
    queryFn: () => apiFetch<any[]>(`/live/odds/${slug}`, { auth: false }),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProviderStatus() {
  return useQuery({
    queryKey: ["provider-status"],
    queryFn: () => apiFetch<{ football_provider: string; nba_provider: string; odds_provider: string; status: string }>("/live/status", { auth: false }),
    staleTime: 60 * 1000,
  });
}