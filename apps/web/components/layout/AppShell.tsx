"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/brand/Logo";
import { PreviewNoticeBanner } from "@/components/ui/PreviewNotice";
import { cn } from "@/lib/format";

const NAV_ITEMS = [
  { href: "/interviews/new", label: "Create Interview" },
  { href: "/progress", label: "Progress" },
];

export function AppShell({
  children,
  immersiveActions,
}: {
  children: React.ReactNode;
  immersiveActions?: React.ReactNode;
}) {
  const pathname = usePathname();
  const isImmersive = pathname.includes("/live");

  return (
    <div className="min-h-screen text-[var(--text-primary)]">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-teal-600 focus:px-3 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>

      {isImmersive ? (
        <header className="border-b border-[var(--border-glass)] bg-black/20 backdrop-blur-md">
          <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
            <Link href="/interviews/new" className="text-xs font-medium uppercase tracking-widest text-[var(--text-muted)] hover:text-teal-300">
              ← Exit
            </Link>
            {immersiveActions ? (
              <div className="flex flex-wrap items-center gap-2">{immersiveActions}</div>
            ) : null}
          </div>
        </header>
      ) : (
        <header className="sticky top-0 z-40 border-b border-[var(--border-glass)] bg-[var(--bg-deep)]/80 backdrop-blur-xl">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <Logo />
            <nav aria-label="Primary" className="flex flex-wrap gap-1">
              {NAV_ITEMS.map((item) => {
                const active =
                  pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/30"
                        : "text-[var(--text-muted)] hover:bg-white/5 hover:text-[var(--text-primary)]",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>
      )}

      <main
        id="main-content"
        className={cn(
          "mx-auto",
          isImmersive ? "max-w-[1400px] px-4 py-4 sm:px-6 sm:py-6" : "max-w-6xl px-4 py-8 sm:px-6",
        )}
      >
        {!isImmersive ? <PreviewNoticeBanner /> : null}
        {children}
      </main>
    </div>
  );
}
