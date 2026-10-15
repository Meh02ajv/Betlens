"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Trophy,
  TrendingUp,
  Calculator,
  BookOpen,
  MessageSquare,
  Settings,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { isAdmin } from "@/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/competitions", label: "Competitions", icon: Trophy },
  { href: "/value", label: "Value Finder", icon: TrendingUp },
  { href: "/slip", label: "Slip Analyzer", icon: Calculator },
  { href: "/tracker", label: "Bet Tracker", icon: BookOpen },
  { href: "/assistant", label: "Assistant", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const admin = typeof window !== "undefined" ? isAdmin() : false;

  return (
    <aside className="hidden md:flex flex-col w-60 min-h-screen bg-white border-r border-border fixed left-0 top-0 z-30">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
        <div className="w-8 h-8 bg-accent rounded-button flex items-center justify-center">
          <span className="text-white font-heading text-body-sm">B</span>
        </div>
        <span className="text-section-title font-heading text-accent">BetLens</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5" aria-label="Main navigation">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-button text-body-sm font-label transition-colors duration-150",
                active
                  ? "bg-accent-tint text-accent"
                  : "text-text-secondary hover:bg-surface hover:text-text-primary"
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" aria-hidden />
              {label}
            </Link>
          );
        })}

        {admin && (
          <Link
            href="/admin"
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-button text-body-sm font-label transition-colors duration-150",
              pathname.startsWith("/admin")
                ? "bg-accent-tint text-accent"
                : "text-text-secondary hover:bg-surface hover:text-text-primary"
            )}
          >
            <Shield className="w-4 h-4 flex-shrink-0" aria-hidden />
            Admin
          </Link>
        )}
      </nav>

      {/* Settings */}
      <div className="px-3 py-4 border-t border-border">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-button text-body-sm font-label transition-colors duration-150",
            pathname === "/settings"
              ? "bg-accent-tint text-accent"
              : "text-text-secondary hover:bg-surface hover:text-text-primary"
          )}
        >
          <Settings className="w-4 h-4 flex-shrink-0" aria-hidden />
          Settings
        </Link>

        {/* Responsible gambling footer */}
        <p className="mt-3 px-3 text-caption text-text-secondary">
          18+ only.{" "}
          <a
            href="https://www.begambleaware.org"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-accent"
          >
            BeGambleAware
          </a>
        </p>
      </div>
    </aside>
  );
}