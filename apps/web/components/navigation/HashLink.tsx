"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { routes, type HomeSection } from "@/lib/routes";

function scrollToSection(section: HomeSection) {
  const target = document.getElementById(section);
  if (!target) {
    return;
  }
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  window.history.replaceState(null, "", routes.homeSection(section));
}

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

  return (
    <Link
      href={href}
      className={className}
      onClick={(event) => {
        if (pathname === routes.home) {
          event.preventDefault();
          scrollToSection(section);
          onNavigate?.();
        }
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
