"use client";

import Link from "next/link";

import { ButtonLink } from "@/components/ui/ButtonLink";
import { useAppContext } from "@/context/AppProvider";
import { resolveAuthEntryHref } from "@/lib/routes";

export function useAuthEntryHref(targetHref: string): string {
  const { isAuthenticated } = useAppContext();
  return resolveAuthEntryHref(targetHref, isAuthenticated);
}

export function AuthEntryButtonLink({
  href,
  children,
  className,
  variant,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
  variant?: "primary" | "secondary";
}) {
  const resolvedHref = useAuthEntryHref(href);
  return (
    <ButtonLink href={resolvedHref} className={className} variant={variant}>
      {children}
    </ButtonLink>
  );
}

export function AuthEntryLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  const resolvedHref = useAuthEntryHref(href);
  return (
    <Link href={resolvedHref} className={className}>
      {children}
    </Link>
  );
}
