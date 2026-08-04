"use client";

import dynamic from "next/dynamic";

import { FeatureSections } from "@/components/home/FeatureSections";
import { LandingHero } from "@/components/home/LandingHero";
import { LandingNav } from "@/components/home/LandingNav";

const AudioFountainScene = dynamic(
  () =>
    import("@/components/home/AudioFountainScene").then((mod) => mod.AudioFountainScene),
  { ssr: false },
);

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden text-[var(--text-primary)]">
      <AudioFountainScene />
      <LandingNav />
      <main>
        <LandingHero />
        <FeatureSections />
      </main>
    </div>
  );
}
