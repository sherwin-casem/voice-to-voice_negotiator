"use client";

import Link from "next/link";

import { NavLink } from "@/components/navigation/HashLink";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { routes, SITE_NAV_LINKS } from "@/lib/routes";

export function LandingFooter() {
  return (
    <footer className="relative border-t border-[var(--border-glass)] bg-[var(--bg-deep)]">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="glass-panel flex flex-col items-start justify-between gap-8 p-8 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
              Ready to practice out loud?
            </h2>
            <p className="mt-2 max-w-md text-sm text-[var(--text-muted)]">
              Jump into a live voice interview or review sample evaluation scores before you begin.
            </p>
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <ButtonLink href={routes.previewResults} variant="secondary" className="justify-center px-6 py-2.5">
              View sample results
            </ButtonLink>
            <ButtonLink href={routes.createInterview} className="justify-center px-6 py-2.5">
              Start practicing →
            </ButtonLink>
          </div>
        </div>

        <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-section-label">Product</p>
            <ul className="mt-3 space-y-2">
              {SITE_NAV_LINKS.map((item) => (
                <li key={item.href}>
                  <NavLink
                    href={item.href}
                    isHash={item.isHash}
                    section={item.section}
                    className="text-sm text-[var(--text-muted)] hover:text-teal-300"
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-section-label">Interview flow</p>
            <ul className="mt-3 space-y-2">
              <li>
                <Link href={routes.createInterview} className="text-sm text-[var(--text-muted)] hover:text-teal-300">
                  Create session
                </Link>
              </li>
              <li>
                <Link href={routes.createInterview} className="text-sm text-[var(--text-muted)] hover:text-teal-300">
                  Configure &amp; go live
                </Link>
              </li>
              <li>
                <Link href={routes.previewResults} className="text-sm text-[var(--text-muted)] hover:text-teal-300">
                  Evaluation report
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-section-label">VoxForge</p>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)]">
              AI voice interview practice with multi-agent evaluation and progress tracking.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
