"use client";

import { LandingFooter } from "@/components/home/LandingFooter";
import { SiteNav } from "@/components/navigation/SiteNav";

export function MarketingShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-[var(--text-primary)]">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-teal-600 focus:px-3 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>

      <SiteNav variant="app" />

      <main id="main-content" className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
        {children}
      </main>

      <LandingFooter />
    </div>
  );
}
