"use client";

import { AuthEntryButtonLink, AuthEntryLink } from "@/components/auth/AuthEntryLink";
import { cn } from "@/lib/format";
export function MarketingHero({
  eyebrow,
  title,
  description,
  primaryCta,
  secondaryCta,
  className,
}: {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
  className?: string;
}) {
  return (
    <section className={cn("mb-16 max-w-3xl", className)}>
      <p className="text-section-label">{eyebrow}</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-4xl lg:text-5xl">
        {title}
      </h1>
      <p className="mt-4 text-base leading-relaxed text-[var(--text-muted)] sm:text-lg">{description}</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <AuthEntryButtonLink href={primaryCta.href} className="px-6 py-2.5 text-sm">
          {primaryCta.label} →
        </AuthEntryButtonLink>
        {secondaryCta ? (
          <AuthEntryButtonLink href={secondaryCta.href} variant="secondary" className="px-6 py-2.5 text-sm">
            {secondaryCta.label}
          </AuthEntryButtonLink>
        ) : null}
      </div>
    </section>
  );
}

export function MarketingSection({
  eyebrow,
  title,
  description,
  children,
  className,
  id,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("mb-16", className)}>
      <div className="mb-8 max-w-2xl">
        {eyebrow ? <p className="text-section-label">{eyebrow}</p> : null}
        <h2
          className={cn(
            "text-2xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-3xl",
            eyebrow && "mt-3",
          )}
        >
          {title}
        </h2>
        {description ? (
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-muted)] sm:text-base">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export function MarketingCtaBand({
  title,
  description,
  primaryCta,
  secondaryCta,
}: {
  title: string;
  description: string;
  primaryCta: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
}) {
  return (
    <section className="glass-panel mb-4 flex flex-col items-start justify-between gap-6 p-8 sm:flex-row sm:items-center">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)] sm:text-2xl">{title}</h2>
        <p className="mt-2 max-w-xl text-sm text-[var(--text-muted)]">{description}</p>
      </div>
      <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
        <AuthEntryButtonLink href={primaryCta.href} className="justify-center px-6 py-2.5">
          {primaryCta.label} →
        </AuthEntryButtonLink>
        {secondaryCta ? (
          <AuthEntryButtonLink href={secondaryCta.href} variant="secondary" className="justify-center px-6 py-2.5">
            {secondaryCta.label}
          </AuthEntryButtonLink>
        ) : null}
      </div>
    </section>
  );
}

export function CrossLinkGrid({
  links,
}: {
  links: ReadonlyArray<{ label: string; href: string; description: string }>;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {links.map((link) => (
        <AuthEntryLink
          key={link.href}
          href={link.href}
          className="glass-panel group block p-5 transition-colors hover:bg-[var(--bg-panel-hover)]"
        >
          <p className="font-medium text-[var(--text-primary)] group-hover:text-teal-300">{link.label}</p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">{link.description}</p>
        </AuthEntryLink>
      ))}
    </div>
  );
}
