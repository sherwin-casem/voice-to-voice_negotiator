"use client";

import { MarketingHero } from "@/components/marketing/MarketingSections";
import { ResourcesHeroArt } from "@/components/marketing/ResourcesHeroArt";
import { RESOURCES_HERO } from "@/lib/marketing/resources-content";

export function ResourcesHero() {
  return <MarketingHero {...RESOURCES_HERO} visual={<ResourcesHeroArt />} />;
}
