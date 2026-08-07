import type { Metadata } from "next";

import {
  DimensionGrid,
  FeaturePillarGrid,
  FlowSteps,
  InterviewFormatGrid,
  ProblemSolutionBlock,
  StatsBand,
} from "@/components/marketing/FeaturesBlocks";
import {
  MarketingHero,
  MarketingSection,
} from "@/components/marketing/MarketingSections";
import {
  EVALUATION_DIMENSIONS,
  EXPANDED_PILLARS,
  FEATURES_HERO,
  FEATURES_STATS,
  INTERVIEW_FORMATS,
  PROBLEM_SOLUTION,
} from "@/lib/marketing/features-content";
import { PRODUCT_FLOW } from "@/lib/routes";

export const metadata: Metadata = {
  title: "Features",
  description:
    "Voice-first AI interview practice with multi-agent evaluation, seven scoring dimensions, and progress tracking.",
};

export default function FeaturesPage() {
  return (
    <>
      <MarketingHero
        {...FEATURES_HERO}
        art={{ src: "/backgrounds/ai-head.png", width: 307, height: 512 }}
      />

      <MarketingSection eyebrow={PROBLEM_SOLUTION.eyebrow} title={PROBLEM_SOLUTION.title}>
        <ProblemSolutionBlock problem={PROBLEM_SOLUTION.problem} solution={PROBLEM_SOLUTION.solution} />
      </MarketingSection>

      <MarketingSection
        eyebrow="Core capabilities"
        title="Everything you need to prepare out loud"
        description="Three pillars that mirror how real interview prep should work — practice, evaluate, and improve."
      >
        <FeaturePillarGrid pillars={EXPANDED_PILLARS} />
      </MarketingSection>

      <MarketingSection
        eyebrow="End-to-end flow"
        title="From session creation to scored feedback in four steps"
        description="Each stage builds on the last so you always know what to do next."
      >
        <FlowSteps steps={PRODUCT_FLOW} />
      </MarketingSection>

      <MarketingSection
        eyebrow="Evaluation"
        title="Seven dimensions, one unified report"
        description="Separate agents score distinct skills, then synthesis highlights what to fix first."
      >
        <DimensionGrid dimensions={EVALUATION_DIMENSIONS} />
      </MarketingSection>

      <MarketingSection
        eyebrow="Interview formats"
        title="Practice for the rounds you will actually face"
        description="Configure sessions for the interview type and difficulty level that matches your target role."
      >
        <InterviewFormatGrid formats={INTERVIEW_FORMATS} />
      </MarketingSection>

      <MarketingSection title="Built for voice-first preparation">
        <StatsBand stats={FEATURES_STATS} />
      </MarketingSection>
    </>
  );
}
