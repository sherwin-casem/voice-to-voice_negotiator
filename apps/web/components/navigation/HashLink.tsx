"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { cn } from "@/lib/format";
import { navigateToHomeSection } from "@/lib/home-navigation";
import { routes, type HomeSection } from "@/lib/routes";

export function HashLink({
  section,
  href,
  children,
  className,
  onNavigate,
}: {
  section: HomeSection;
  href: string;
  children: React.ReactNode;
  className?: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <Link
      href={href}
      className={className}
      onClick={(event) => {
        event.preventDefault();
        navigateToHomeSection(section, router, pathname);
        onNavigate?.();
      }}
    >
      {children}
    </Link>
  );
}

export function NavLink({
  href,
  isHash,
  section,
  children,
  className,
  active,
  onNavigate,
}: {
  href: string;
  isHash: boolean;
  section?: HomeSection;
  children: React.ReactNode;
  className?: string;
  active?: boolean;
  onNavigate?: () => void;
}) {
  const linkClass = cn(className, active && "bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/30");

  if (isHash && section) {
    return (
      <HashLink section={section} href={href} className={linkClass} onNavigate={onNavigate}>
        {children}
      </HashLink>
    );
  }

  return (
    <Link href={href} className={linkClass} aria-current={active ? "page" : undefined} onClick={onNavigate}>
      {children}
    </Link>
  );
}
