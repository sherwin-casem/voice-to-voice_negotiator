"use client";

import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { FeatureSections, ProductFlowSection } from "@/components/home/FeatureSections";
import { LandingFooter } from "@/components/home/LandingFooter";
import { LandingHero } from "@/components/home/LandingHero";
import { SiteNav } from "@/components/navigation/SiteNav";
import { scrollToHashFromLocation } from "@/lib/home-navigation";
import { routes } from "@/lib/routes";

const AudioFountainScene = dynamic(
  () =>
    import("@/components/home/AudioFountainScene").then((mod) => mod.AudioFountainScene),
  { ssr: false },
);

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
      <AudioFountainScene />
      <SiteNav variant="floating" />
      <main className="relative z-10">
        <LandingHero />
        <ProductFlowSection />
        <FeatureSections />
        <LandingFooter />
      </main>
    </div>
  );
}
