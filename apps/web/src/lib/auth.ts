/**
 * Auth state management — simple localStorage-based approach.
 * In production, consider using next-auth or a dedicated auth library.
 */
"use client";

import { setTokens, clearTokens, getAccessToken } from "./api";

export interface AuthState {
  isAuthenticated: boolean;
  userId: string | null;
  plan: "free" | "pro" | null;
  role: "user" | "admin" | null;
}

function parseJwt(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split(".")[1];
    const decoded = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function getAuthState(): AuthState {
  const token = getAccessToken();
  if (!token) {
    return { isAuthenticated: false, userId: null, plan: null, role: null };
  }

  const payload = parseJwt(token);
  if (!payload) {
    return { isAuthenticated: false, userId: null, plan: null, role: null };
  }

  // Check expiry
  const exp = payload.exp as number | undefined;
  if (exp && Date.now() / 1000 > exp) {
    clearTokens();
    return { isAuthenticated: false, userId: null, plan: null, role: null };
  }

  return {
    isAuthenticated: true,
    userId: payload.sub as string,
    plan: (payload.plan as "free" | "pro") ?? "free",
    role: (payload.role as "user" | "admin") ?? "user",
  };
}

export function login(accessToken: string, refreshToken: string): void {
  setTokens(accessToken, refreshToken);
}

export function logout(): void {
  clearTokens();
}

export function isAuthenticated(): boolean {
  return getAuthState().isAuthenticated;
}

export function isPro(): boolean {
  return getAuthState().plan === "pro";
}

export function isAdmin(): boolean {
  return getAuthState().role === "admin";
}