"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, MessageSquare, BookOpen, User } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/competitions", label: "Matches", icon: Calendar },
  { href: "/assistant", label: "Assistant", icon: MessageSquare },
  { href: "/tracker", label: "Tracker", icon: BookOpen },
  { href: "/settings", label: "Profile", icon: User },
];

/**
 * Bottom tab bar for mobile (≤768px).
 */
export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-border"
      aria-label="Mobile navigation"
    >
      <div className="flex">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex-1 flex flex-col items-center gap-0.5 py-2 text-caption font-label transition-colors duration-150",
                active ? "text-accent" : "text-text-secondary"
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon
                className={cn("w-5 h-5", active ? "text-accent" : "text-text-secondary")}
                aria-hidden
              />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}