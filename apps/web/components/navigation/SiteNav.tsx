"use client";



import Link from "next/link";

import { usePathname, useRouter } from "next/navigation";

import { useState } from "react";



import { AuthEntryButtonLink } from "@/components/auth/AuthEntryLink";

import { Logo } from "@/components/brand/Logo";

import { Button } from "@/components/ui/Button";

import { ButtonLink } from "@/components/ui/ButtonLink";

import { useAppContext } from "@/context/AppProvider";

import { cn } from "@/lib/format";

import { routes, SITE_NAV_LINKS } from "@/lib/routes";



function navLinkClassName(active: boolean) {

  return cn(

    "rounded-full px-3 py-1.5 text-sm transition-colors",

    active

      ? "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/30"

      : "text-[var(--text-muted)] hover:bg-white/5 hover:text-[var(--text-primary)]",

  );

}



function truncateEmail(email: string): string {

  const atIndex = email.indexOf("@");

  if (atIndex <= 0) {

    return email;

  }

  const local = email.slice(0, atIndex);

  const domain = email.slice(atIndex);

  if (local.length <= 12) {

    return email;

  }

  return `${local.slice(0, 10)}…${domain}`;

}



export function SiteNav({

  variant = "app",

  immersiveActions,

}: {

  variant?: "floating" | "app" | "immersive";

  immersiveActions?: React.ReactNode;

}) {

  const pathname = usePathname();

  const router = useRouter();

  const { user, isAuthReady, isAuthenticated, logout } = useAppContext();

  const [mobileOpen, setMobileOpen] = useState(false);

  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const closeMobile = () => setMobileOpen(false);



  async function handleLogout() {

    setIsLoggingOut(true);

    try {

      await logout();

      closeMobile();

      router.push(routes.home);

    } finally {

      setIsLoggingOut(false);

    }

  }



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

      ? "mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full border border-[var(--border-glass)] bg-[var(--bg-deep)]/55 px-4 py-2.5 backdrop-blur-xl sm:px-5"

      : "mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6";



  const navLinks = SITE_NAV_LINKS.filter(
    (item) => isAuthenticated || item.href !== routes.evaluations,
  );

  const authActions =

    isAuthReady && isAuthenticated ? (

      <>

        <span className="hidden text-sm text-[var(--text-muted)] sm:inline" title={user?.email}>

          {user?.displayName ?? truncateEmail(user?.email ?? "")}

        </span>

        <Button variant="secondary" className="px-4 py-1.5 text-sm" onClick={handleLogout} disabled={isLoggingOut}>

          {isLoggingOut ? "Logging out…" : "Log out"}

        </Button>

        <ButtonLink href={routes.createInterview} className="px-4 py-1.5 text-sm">

          Get started

        </ButtonLink>

      </>

    ) : (

      <>

        <ButtonLink href={routes.login} variant="secondary" className="px-4 py-1.5 text-sm">

          Log in

        </ButtonLink>

        <AuthEntryButtonLink href={routes.createInterview} className="px-4 py-1.5 text-sm">

          Get started

        </AuthEntryButtonLink>

      </>

    );



  return (

    <header className={shellClass}>

      <div className={innerClass}>

        <Logo href={routes.home} showTagline={false} size="sm" />



        <nav aria-label="Primary" className="hidden items-center gap-1 lg:flex">

          {navLinks.map((item) => {

            const active = pathname === item.href;

            return (

              <Link

                key={item.href}

                href={item.href}

                className={navLinkClassName(active)}

                aria-current={active ? "page" : undefined}

                onClick={closeMobile}

              >

                {item.label}

              </Link>

            );

          })}

        </nav>



        <div className="flex items-center gap-2">

          <div className="hidden items-center gap-2 lg:flex">{authActions}</div>



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

            {navLinks.map((item) => {

              const active = pathname === item.href;

              return (

                <Link

                  key={item.href}

                  href={item.href}

                  className={navLinkClassName(active)}

                  aria-current={active ? "page" : undefined}

                  onClick={closeMobile}

                >

                  {item.label}

                </Link>

              );

            })}

          </nav>

          <div className="mt-4 flex flex-col gap-2">{authActions}</div>

        </div>

      ) : null}

    </header>

  );

}


