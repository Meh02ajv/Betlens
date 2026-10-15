"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Bell, User, LogOut, Settings, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { authApi } from "@/lib/api";
import { logout } from "@/lib/auth";

export function TopBar() {
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } finally {
      logout();
      router.push("/login");
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      setSearchOpen(false);
      setQuery("");
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 md:left-60 z-20 bg-white border-b border-border h-14 flex items-center px-4 gap-3">
      {/* Mobile logo */}
      <Link href="/dashboard" className="md:hidden flex items-center gap-2">
        <div className="w-7 h-7 bg-accent rounded-button flex items-center justify-center">
          <span className="text-white font-heading text-caption">B</span>
        </div>
        <span className="font-heading text-accent">BetLens</span>
      </Link>

      <div className="flex-1" />

      {/* Global search */}
      <div className="relative">
        {searchOpen ? (
          <form onSubmit={handleSearch} className="flex items-center">
            <input
              autoFocus
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search teams, players, competitions…"
              className="input w-64 text-body-sm py-1.5"
              onBlur={() => !query && setSearchOpen(false)}
            />
          </form>
        ) : (
          <button
            onClick={() => setSearchOpen(true)}
            className="btn-ghost flex items-center gap-1.5"
            aria-label="Open search (Ctrl+K)"
          >
            <Search className="w-4 h-4" aria-hidden />
            <span className="hidden sm:inline text-body-sm">Search</span>
            <kbd className="hidden sm:inline text-caption bg-surface border border-border rounded px-1">
              ⌘K
            </kbd>
          </button>
        )}
      </div>

      {/* Notifications */}
      <Link
        href="/notifications"
        className="btn-ghost relative"
        aria-label="Notifications"
      >
        <Bell className="w-4 h-4" aria-hidden />
      </Link>

      {/* Avatar menu */}
      <div className="relative">
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="flex items-center gap-1.5 btn-ghost"
          aria-expanded={menuOpen}
          aria-haspopup="menu"
        >
          <div className="w-7 h-7 rounded-full bg-accent-tint flex items-center justify-center">
            <User className="w-4 h-4 text-accent" aria-hidden />
          </div>
          <ChevronDown className="w-3 h-3 text-text-secondary" aria-hidden />
        </button>

        {menuOpen && (
          <div
            className="absolute right-0 top-full mt-1 w-48 bg-white border border-border rounded-card shadow-popover py-1 z-50"
            role="menu"
          >
            <Link
              href="/settings"
              className="flex items-center gap-2 px-3 py-2 text-body-sm text-text-primary hover:bg-surface"
              role="menuitem"
              onClick={() => setMenuOpen(false)}
            >
              <Settings className="w-4 h-4" aria-hidden />
              Settings
            </Link>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-body-sm text-text-primary hover:bg-surface"
              role="menuitem"
            >
              <LogOut className="w-4 h-4" aria-hidden />
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}