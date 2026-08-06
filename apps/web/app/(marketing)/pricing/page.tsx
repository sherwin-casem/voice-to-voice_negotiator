import type { Metadata } from "next";

import {
  FaqAccordion,
  PricingComparisonTable,
  PricingTierCards,
} from "@/components/marketing/PricingBlocks";
import {
  MarketingCtaBand,
  MarketingHero,
  MarketingSection,
} from "@/components/marketing/MarketingSections";
import {
  PRICING_COMPARISON,
  PRICING_CTA,
  PRICING_FAQ,
  PRICING_HERO,
  PRICING_TIERS,
} from "@/lib/marketing/pricing-content";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Simple plans for voice interview practice — Free, Pro, and Team tiers for serious prep.",
};

export default function PricingPage() {
  return (
    <>
      <MarketingHero
        {...PRICING_HERO}
        primaryCta={{ label: "Get started free", href: PRICING_TIERS[0].cta.href }}
        secondaryCta={{ label: "Compare features", href: "#comparison" }}
      />

      <MarketingSection
        eyebrow="Plans"
        title="Choose the level of prep you need"
        description="All plans currently start with the same onboarding flow during early access."
      >
        <PricingTierCards tiers={PRICING_TIERS} />
      </MarketingSection>

      <MarketingSection
        id="comparison"
        eyebrow="Compare"
        title="Feature comparison"
        description="See what is included in each tier."
      >
        <PricingComparisonTable categories={PRICING_COMPARISON.categories} />
      </MarketingSection>

      <MarketingSection eyebrow="FAQ" title="Common questions">
        <FaqAccordion items={PRICING_FAQ} />
      </MarketingSection>

      <MarketingCtaBand {...PRICING_CTA} />
    </>
  );
}
