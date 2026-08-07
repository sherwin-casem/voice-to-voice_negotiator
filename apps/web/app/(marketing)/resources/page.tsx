import type { Metadata } from "next";

import {
  CrossLinkGrid,
  MarketingHero,
  MarketingSection,
} from "@/components/marketing/MarketingSections";
import {
  GettingStartedChecklist,
  ResourceGuideGrid,
  ResourceTipList,
} from "@/components/marketing/ResourcesBlocks";
import {
  GETTING_STARTED,
  RESOURCE_CROSS_LINKS,
  RESOURCES_HERO,
  RESOURCE_GUIDES,
  VOICE_TIPS,
} from "@/lib/marketing/resources-content";

export const metadata: Metadata = {
  title: "Resources",
  description: "Interview prep guides, voice practice tips, and a getting-started checklist for VoxForge.",
};

export default function ResourcesPage() {
  return (
    <>
      <MarketingHero
        {...RESOURCES_HERO}
        art={{ src: "/backgrounds/data-cubes.png", width: 307, height: 512 }}
      />

      <MarketingSection
        eyebrow="Guides"
        title="Prep guides by interview type"
        description="Tactical advice for the formats VoxForge supports — use these before your next voice session."
      >
        <ResourceGuideGrid guides={RESOURCE_GUIDES} />
      </MarketingSection>

      <MarketingSection
        eyebrow="Voice tips"
        title="Perform better in live voice interviews"
        description="Small habits that make a big difference when you are speaking, not typing."
      >
        <ResourceTipList tips={VOICE_TIPS} />
      </MarketingSection>

      <MarketingSection
        eyebrow="Getting started"
        title="Your first session in four steps"
        description="Follow this checklist from setup through evaluation review."
      >
        <GettingStartedChecklist steps={GETTING_STARTED} />
      </MarketingSection>

      <MarketingSection eyebrow="Explore" title="More from VoxForge">
        <CrossLinkGrid links={RESOURCE_CROSS_LINKS} />
      </MarketingSection>
    </>
  );
}
