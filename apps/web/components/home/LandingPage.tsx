"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { FeatureSectionsTeaser, ProductFlowSection } from "@/components/home/FeatureSections";
import { LandingFooter } from "@/components/home/LandingFooter";
import { LandingHero } from "@/components/home/LandingHero";
import { SiteNav } from "@/components/navigation/SiteNav";
import { scrollToHashFromLocation } from "@/lib/home-navigation";
import { routes } from "@/lib/routes";

export function LandingPage() {
  const pathname = usePathname();

  useEffect(() => {
    if (pathname !== routes.home) {
      return;
    }

    scrollToHashFromLocation();

    const handleHashChange = () => scrollToHashFromLocation();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [pathname]);

  return (
    <div className="relative min-h-screen overflow-x-hidden text-[var(--text-primary)]">
      <SiteNav variant="floating" />
      <main className="relative">
        <LandingHero />
        <ProductFlowSection />
        <FeatureSectionsTeaser />
        <LandingFooter />
      </main>
    </div>
  );
}
