"use client";

import { AuthEntryButtonLink, AuthEntryLink } from "@/components/auth/AuthEntryLink";
import { GlowArt } from "@/components/ui/GlowArt";
import { Reveal } from "@/components/visuals/Reveal";
import { TiltCard } from "@/components/visuals/TiltCard";
import { cn } from "@/lib/format";

export function MarketingHero({
  eyebrow,
  title,
  description,
  primaryCta,
  secondaryCta,
  art,
  className,
}: {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
  art?: { src: string; width: number; height: number };
  className?: string;
}) {
  return (
    <section className={cn("mb-16", className)}>
      <div className="flex items-center gap-12">
        <Reveal className="max-w-3xl flex-1">
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
        </Reveal>
        {art ? (
          <Reveal delayMs={120} className="hidden shrink-0 lg:block">
            <TiltCard>
              <GlowArt
                src={art.src}
                width={art.width}
                height={art.height}
                sizes="(min-width: 1280px) 18rem, 16rem"
                className="w-64 animate-float-slow xl:w-72"
              />
            </TiltCard>
          </Reveal>
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
      <Reveal className="mb-8 max-w-2xl">
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
      </Reveal>
      <Reveal delayMs={90}>{children}</Reveal>
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
    <Reveal
      as="section"
      className="glass-panel relative mb-4 flex flex-col items-start justify-between gap-6 overflow-hidden p-8 sm:flex-row sm:items-center"
    >
      <GlowArt
        src="/backgrounds/holo-stage.png"
        width={512}
        height={512}
        sizes="28rem"
        className="absolute -right-16 -top-24 hidden w-[28rem] opacity-25 sm:block"
      />
      <div className="relative">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] sm:text-2xl">{title}</h2>
        <p className="mt-2 max-w-xl text-sm text-[var(--text-muted)]">{description}</p>
      </div>
      <div className="relative flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
        <AuthEntryButtonLink href={primaryCta.href} className="justify-center px-6 py-2.5">
          {primaryCta.label} →
        </AuthEntryButtonLink>
        {secondaryCta ? (
          <AuthEntryButtonLink href={secondaryCta.href} variant="secondary" className="justify-center px-6 py-2.5">
            {secondaryCta.label}
          </AuthEntryButtonLink>
        ) : null}
      </div>
    </Reveal>
  );
}

export function CrossLinkGrid({
  links,
}: {
  links: ReadonlyArray<{ label: string; href: string; description: string }>;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {links.map((link, index) => (
        <Reveal key={link.href} delayMs={index * 90}>
          <AuthEntryLink
            href={link.href}
            className="glass-panel group block h-full p-5 transition-all duration-300 hover:-translate-y-1 hover:bg-[var(--bg-panel-hover)] hover:shadow-[0_12px_32px_rgba(20,184,166,0.1)]"
          >
            <p className="font-medium text-[var(--text-primary)] group-hover:text-teal-300">{link.label}</p>
            <p className="mt-2 text-sm text-[var(--text-muted)]">{link.description}</p>
          </AuthEntryLink>
        </Reveal>
      ))}
    </div>
  );
}
