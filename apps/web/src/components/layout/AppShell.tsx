"use client";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { MobileNav } from "./MobileNav";

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * Authenticated app shell: sidebar (desktop) + top bar + mobile nav.
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <TopBar />
      <main
        className="md:ml-60 pt-14 pb-16 md:pb-0 min-h-screen"
        id="main-content"
      >
        <div className="max-w-content mx-auto px-4 py-6">{children}</div>
      </main>
      <MobileNav />
    </div>
  );
}