"use client";

import { Suspense, useMemo } from "react";
import { useParams, useSearchParams } from "next/navigation";

import {
  AnswerEvaluationList,
  BetterAnswersList,
  PracticeRecommendations,
} from "@/components/evaluation/AnswerEvaluation";
import { DimensionScores } from "@/components/evaluation/DimensionScores";
import { FeedbackList, PriorityImprovements } from "@/components/evaluation/FeedbackSections";
import { OverallScoreCard } from "@/components/evaluation/OverallScoreCard";
import { InterviewFunnelStepper } from "@/components/interview/InterviewFunnelStepper";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Spinner } from "@/components/ui/Alert";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { CollapsibleSection } from "@/components/ui/CollapsibleSection";
import { useAppContext } from "@/context/AppProvider";
import { useSession } from "@/hooks/useSession";
import { formatDate } from "@/lib/format";
import { buildPreviewEvaluation } from "@/lib/mocks/evaluation";

function ResultsContent() {
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const sessionId = params.sessionId;
  const isPreviewMode = searchParams.get("preview") === "1";
  const { userId } = useAppContext();
  const { session, error: loadError, isLoading: sessionLoading } = useSession(
    isPreviewMode ? "" : userId,
    isPreviewMode ? "" : sessionId,
  );
  const isLoading = isPreviewMode ? false : sessionLoading;

  const evaluation = useMemo(
    () => buildPreviewEvaluation(session?.title ?? "Interview session"),
    [session?.title],
  );

  if (isLoading) {
    return <Spinner label="Loading results" />;
  }

  return (
    <>
      <InterviewFunnelStepper current="results" sessionId={sessionId} className="mb-6" />

      <PageHeader
        title="Interview results"
        description="Multi-agent evaluation, scoring, and coaching recommendations."
        actions={
          <>
            <ButtonLink href="/progress" variant="secondary">
              View progress
            </ButtonLink>
            <ButtonLink href="/interviews/new">New interview</ButtonLink>
          </>
        }
      />

      {loadError ? (
        <div className="mb-6">
          <Alert variant="warning">{loadError}</Alert>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,280px)_1fr] lg:items-start">
        <aside className="space-y-4 lg:sticky lg:top-24">
          <OverallScoreCard score={evaluation.overall_score} />
          <Card>
            <CardHeading>Top priorities</CardHeading>
            <CardDescription>Focus on these improvements first.</CardDescription>
            <ul className="mt-4 space-y-2 text-sm text-[var(--text-muted)]">
              {evaluation.priority_improvements.slice(0, 3).map((item) => (
                <li key={`${item.area}-${item.priority}`} className="flex gap-2">
                  <span className="text-teal-500" aria-hidden="true">
                    •
                  </span>
                  {item.recommendation}
                </li>
              ))}
            </ul>
          </Card>
        </aside>

        <div className="space-y-6">
          {session ? (
            <Card>
              <CardHeading>Session summary</CardHeading>
              <CardDescription>Loaded from the interview session API.</CardDescription>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-[var(--text-muted)]">Title</dt>
                  <dd className="font-medium text-[var(--text-primary)]">
                    {session.title ?? "Untitled session"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Status</dt>
                  <dd className="mt-1">
                    <SessionStatusBadge status={session.status} />
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Questions asked</dt>
                  <dd className="font-medium text-[var(--text-primary)]">
                    {session.question_count}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Ended</dt>
                  <dd className="font-medium text-[var(--text-primary)]">
                    {formatDate(session.ended_at)}
                  </dd>
                </div>
              </dl>
            </Card>
          ) : null}

          <CollapsibleSection
            title="Dimension scores"
            description="Breakdown across evaluation dimensions."
            defaultOpen
          >
            <DimensionScores scores={evaluation.dimension_scores} bare />
          </CollapsibleSection>

          <div className="grid gap-6 lg:grid-cols-2">
            <CollapsibleSection
              title="Strengths"
              description="Evidence-backed positives from evaluators."
              defaultOpen
            >
              <FeedbackList
                title="Strengths"
                description="Evidence-backed positives from evaluators."
                items={evaluation.strengths}
                emptyMessage="No strengths recorded."
                bare
              />
            </CollapsibleSection>

            <CollapsibleSection
              title="Weaknesses"
              description="Specific gaps identified during evaluation."
              defaultOpen
            >
              <FeedbackList
                title="Weaknesses"
                description="Specific gaps identified during evaluation."
                items={evaluation.weaknesses}
                emptyMessage="No weaknesses recorded."
                bare
              />
            </CollapsibleSection>
          </div>

          <CollapsibleSection
            title="All improvements"
            description="Full list of priority improvements."
            defaultOpen={false}
          >
            <PriorityImprovements items={evaluation.priority_improvements} bare />
          </CollapsibleSection>

          <CollapsibleSection
            title="Answer evaluations"
            description="Per-answer feedback from evaluators."
            defaultOpen={false}
          >
            <AnswerEvaluationList items={evaluation.answer_evaluations} bare />
          </CollapsibleSection>

          <CollapsibleSection
            title="Better answer examples"
            description="Suggested rewrites for stronger responses."
            defaultOpen={false}
          >
            <BetterAnswersList items={evaluation.better_answers} bare />
          </CollapsibleSection>

          <CollapsibleSection
            title="Practice recommendations"
            description="What to rehearse before your next session."
            defaultOpen={false}
          >
            <PracticeRecommendations items={evaluation.practice_recommendations} bare />
          </CollapsibleSection>
        </div>
      </div>
    </>
  );
}

export default function InterviewResultsPage() {
  return (
    <Suspense fallback={<Spinner label="Loading results" />}>
      <ResultsContent />
    </Suspense>
  );
}
