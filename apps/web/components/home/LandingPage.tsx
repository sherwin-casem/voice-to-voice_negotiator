"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";

import { FeatureSections, ProductFlowSection } from "@/components/home/FeatureSections";
import { LandingFooter } from "@/components/home/LandingFooter";
import { LandingHero } from "@/components/home/LandingHero";
import { SiteNav } from "@/components/navigation/SiteNav";
import { routes, type HomeSection } from "@/lib/routes";

const AudioFountainScene = dynamic(
  () =>
    import("@/components/home/AudioFountainScene").then((mod) => mod.AudioFountainScene),
  { ssr: false },
);

function scrollToHashSection() {
  const hash = window.location.hash.replace("#", "") as HomeSection;
  if (!hash) {
    return;
  }
  window.requestAnimationFrame(() => {
    document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

export function LandingPage() {
  useEffect(() => {
    scrollToHashSection();
    window.addEventListener("hashchange", scrollToHashSection);
    return () => window.removeEventListener("hashchange", scrollToHashSection);
  }, []);

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
