"use client";

import { SiteNav } from "@/components/navigation/SiteNav";
import { PreviewNoticeBanner } from "@/components/ui/PreviewNotice";
import { cn } from "@/lib/format";
import { usePathname } from "next/navigation";

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

      <SiteNav variant={isImmersive ? "immersive" : "app"} immersiveActions={immersiveActions} />

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
