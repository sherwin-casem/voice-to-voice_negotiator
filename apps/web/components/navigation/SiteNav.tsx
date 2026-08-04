"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/brand/Logo";
import { NavLink } from "@/components/navigation/HashLink";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { cn } from "@/lib/format";
import { routes, SITE_NAV_LINKS } from "@/lib/routes";

function navLinkClassName(isActive: boolean) {
  return cn(
    "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
    isActive
      ? "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/30"
      : "text-[var(--text-muted)] hover:bg-white/5 hover:text-[var(--text-primary)]",
  );
}

function isNavActive(pathname: string, href: string) {
  if (href.startsWith("/#")) {
    return false;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteNav({
  variant = "app",
  immersiveActions,
}: {
  variant?: "floating" | "app" | "immersive";
  immersiveActions?: React.ReactNode;
}) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isHome = pathname === routes.home;
  const closeMobile = () => setMobileOpen(false);

  if (variant === "immersive") {
    return (
      <header className="border-b border-[var(--border-glass)] bg-black/20 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            href={routes.createInterview}
            className="text-xs font-medium uppercase tracking-widest text-[var(--text-muted)] hover:text-teal-300"
          >
            ← Exit interview
          </Link>
          {immersiveActions ? (
            <div className="flex flex-wrap items-center gap-2">{immersiveActions}</div>
          ) : null}
        </div>
      </header>
    );
  }

  const shellClass =
    variant === "floating"
      ? "fixed inset-x-0 top-0 z-50 px-4 pt-4 sm:px-6"
      : "sticky top-0 z-40 border-b border-[var(--border-glass)] bg-[var(--bg-deep)]/80 backdrop-blur-xl";

  const innerClass =
    variant === "floating"
      ? "mx-auto flex max-w-6xl items-center justify-between gap-3 rounded-full border border-[var(--border-glass)] bg-[var(--bg-deep)]/55 px-4 py-2.5 backdrop-blur-xl sm:px-5"
      : "mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4 sm:px-6";

  return (
    <header className={shellClass}>
      <div className={innerClass}>
        <Logo href={routes.home} showTagline={!isHome && variant === "app"} size="sm" />

        <nav aria-label="Primary" className="hidden items-center gap-1 lg:flex">
          {!isHome ? (
            <NavLink
              href={routes.home}
              isHash={false}
              className={navLinkClassName(false)}
              onNavigate={closeMobile}
            >
              Home
            </NavLink>
          ) : null}
          {SITE_NAV_LINKS.map((item) => {
            const section = item.href.replace("/#", "") as "features" | "evaluation" | "practice" | "flow";
            return (
              <NavLink
                key={item.href}
                href={item.href}
                isHash={item.isHash}
                section={item.isHash ? section : undefined}
                className={navLinkClassName(isNavActive(pathname, item.href))}
                active={isNavActive(pathname, item.href)}
                onNavigate={closeMobile}
              >
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ButtonLink
            href={routes.progress}
            variant="secondary"
            className="hidden px-4 py-1.5 sm:inline-flex"
          >
            Progress
          </ButtonLink>
          <ButtonLink href={routes.createInterview} className="hidden px-4 py-1.5 sm:inline-flex">
            Start practicing
          </ButtonLink>

          <button
            type="button"
            className="inline-flex rounded-full border border-[var(--border-glass-strong)] p-2 text-[var(--text-muted)] hover:bg-white/5 hover:text-[var(--text-primary)] lg:hidden"
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav-panel"
            onClick={() => setMobileOpen((open) => !open)}
          >
            <span className="sr-only">{mobileOpen ? "Close menu" : "Open menu"}</span>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
              {mobileOpen ? (
                <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              ) : (
                <path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen ? (
        <div
          id="mobile-nav-panel"
          className={cn(
            "border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/95 px-4 py-4 backdrop-blur-xl lg:hidden",
            variant === "floating" ? "mx-4 mt-2 rounded-2xl border sm:mx-6" : "",
          )}
        >
          <nav aria-label="Mobile" className="flex flex-col gap-1">
            {!isHome ? (
              <NavLink
                href={routes.home}
                isHash={false}
                className={navLinkClassName(false)}
                onNavigate={closeMobile}
              >
                Home
              </NavLink>
            ) : null}
            {SITE_NAV_LINKS.map((item) => {
              const section = item.href.replace("/#", "") as "features" | "evaluation" | "practice" | "flow";
              return (
                <NavLink
                  key={item.href}
                  href={item.href}
                  isHash={item.isHash}
                  section={item.isHash ? section : undefined}
                  className={navLinkClassName(isNavActive(pathname, item.href))}
                  onNavigate={closeMobile}
                >
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <ButtonLink href={routes.progress} variant="secondary" className="w-full justify-center py-2">
              Progress
            </ButtonLink>
            <ButtonLink href={routes.createInterview} className="w-full justify-center py-2">
              Start practicing
            </ButtonLink>
          </div>
        </div>
      ) : null}
    </header>
  );
}
