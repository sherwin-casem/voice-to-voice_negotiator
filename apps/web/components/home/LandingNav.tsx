import Link from "next/link";

import { Logo } from "@/components/brand/Logo";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { cn } from "@/lib/format";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#evaluation", label: "Evaluation" },
  { href: "#practice", label: "Voice Practice" },
] as const;

export function LandingNav({ className }: { className?: string }) {
  return (
    <header className={cn("fixed inset-x-0 top-0 z-50 px-4 pt-4 sm:px-6", className)}>
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full border border-[var(--border-glass)] bg-[var(--bg-deep)]/55 px-4 py-2.5 backdrop-blur-xl sm:px-5">
        <Logo href="/" showTagline={false} size="sm" />

        <nav aria-label="Landing" className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-3 py-1.5 text-sm text-[var(--text-muted)] transition-colors hover:bg-white/5 hover:text-[var(--text-primary)]"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ButtonLink href="/interviews/new" variant="secondary" className="hidden px-4 py-1.5 sm:inline-flex">
            Log in
          </ButtonLink>
          <ButtonLink href="/interviews/new" className="px-4 py-1.5 text-sm">
            Start practicing
          </ButtonLink>
        </div>
      </div>
    </header>
  );
}
