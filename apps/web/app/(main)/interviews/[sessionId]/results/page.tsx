"use client";

import { INTERVIEW_TYPE_LABELS, type InterviewSessionStatus } from "@voice/shared";
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
import { useSession } from "@/hooks/useSession";
import { useSessionEvaluation } from "@/hooks/useSessionEvaluation";
import type { SessionEvaluationData } from "@/lib/evaluation-api";
import { formatDate } from "@/lib/format";
import { buildPreviewEvaluation } from "@/lib/mocks/evaluation";
import { getHistorySessionById } from "@/lib/mocks/history";
import { routes } from "@/lib/routes";

interface ResultsView {
  overall_score: number;
  dimension_scores: Record<string, number | null>;
  strengths: string[];
  weaknesses: string[];
  priority_improvements: Array<{
    area: string;
    priority: number;
    recommendation: string;
    rationale: string;
  }>;
  answer_evaluations: Array<{
    question: string;
    answer_excerpt: string;
    feedback: string;
    score: number;
  }>;
  better_answers: Array<{ question: string; example: string }>;
  practice_recommendations: Array<{
    title: string;
    instructions: string;
    success_criteria: string;
  }>;
  judge_summary: string | null;
  coach_summary: string | null;
}

function toResultsView(data: SessionEvaluationData): ResultsView {
  return {
    overall_score: data.overall_score,
    dimension_scores: { ...data.dimension_scores } as Record<string, number | null>,
    strengths: data.strengths,
    weaknesses: data.weaknesses,
    priority_improvements: data.priority_improvements.map((item) => ({
      area: item.area,
      priority: item.priority,
      recommendation: item.recommendation,
      rationale: item.rationale ?? "",
    })),
    answer_evaluations: [],
    better_answers: data.better_answers.map((item) => ({
      question: item.question ?? "Suggested stronger answer",
      example: item.example,
    })),
    practice_recommendations: data.practice_recommendations,
    judge_summary: data.judge_summary,
    coach_summary: data.coach_summary,
  };
}

function ResultsContent() {
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const sessionId = params.sessionId;
  const isPreviewMode = searchParams.get("preview") === "1";
  const { session, error: loadError, isLoading: sessionLoading } = useSession(
    isPreviewMode ? "" : sessionId,
  );
  const {
    data: evaluationData,
    error: evaluationError,
    isEvaluating,
  } = useSessionEvaluation(isPreviewMode ? "" : sessionId, !isPreviewMode);

  const previewSession = useMemo(
    () => (isPreviewMode ? getHistorySessionById(sessionId) : undefined),
    [isPreviewMode, sessionId],
  );

  const evaluation = useMemo<ResultsView | null>(() => {
    if (isPreviewMode) {
      return {
        ...buildPreviewEvaluation(previewSession?.title ?? "Interview session", {
          overallScore: previewSession?.overall_score,
        }),
        judge_summary: null,
        coach_summary: null,
      };
    }
    if (evaluationData?.evaluation_status === "completed" && evaluationData.evaluation) {
      return toResultsView(evaluationData.evaluation);
    }
    return null;
  }, [isPreviewMode, previewSession, evaluationData]);

  const isLoading = isPreviewMode ? false : sessionLoading;

  if (isLoading) {
    return <Spinner label="Loading results" />;
  }

  const sessionStatus =
    (evaluationData?.session_status as InterviewSessionStatus | undefined) ??
    session?.status ??
    previewSession?.status ??
    "completed";

  return (
    <>
      <InterviewFunnelStepper current="results" sessionId={sessionId} className="mb-6" />

      <PageHeader
        title="Interview results"
        description="Multi-agent evaluation, scoring, and coaching recommendations."
        actions={
          <>
            <ButtonLink href={routes.home} variant="secondary">
              Home
            </ButtonLink>
            <ButtonLink href={routes.evaluations} variant="secondary">
              View evaluations
            </ButtonLink>
            <ButtonLink href={routes.createInterview}>New interview</ButtonLink>
          </>
        }
      />

      {loadError ? (
        <div className="mb-6">
          <Alert variant="warning">{loadError}</Alert>
        </div>
      ) : null}

      {!isPreviewMode && evaluationError ? (
        <div className="mb-6">
          <Alert variant="warning">{evaluationError}</Alert>
        </div>
      ) : null}

      {!isPreviewMode && evaluationData?.evaluation_status === "failed" ? (
        <div className="mb-6">
          <Alert variant="warning">
            Evaluation failed
            {evaluationData.error_message ? `: ${evaluationData.error_message}` : "."} Your
            interview transcript is saved; please contact support if this persists.
          </Alert>
        </div>
      ) : null}

      {!isPreviewMode && evaluationData?.evaluation_status === "unavailable" ? (
        <div className="mb-6">
          <Alert variant="info">
            No evaluation is available for this session yet. Finish an interview to receive
            multi-agent feedback.
          </Alert>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,280px)_1fr] lg:items-start">
        <aside className="space-y-4 lg:sticky lg:top-24">
          {evaluation ? (
            <>
              <OverallScoreCard score={evaluation.overall_score} />
              {evaluation.priority_improvements.length > 0 ? (
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
              ) : null}
            </>
          ) : !isPreviewMode && isEvaluating ? (
            <Card>
              <CardHeading>Evaluation in progress</CardHeading>
              <CardDescription>
                Our evaluation agents are reviewing your interview. This usually takes under a
                minute.
              </CardDescription>
              <div className="mt-4">
                <Spinner label="Evaluating your interview" />
              </div>
            </Card>
          ) : null}
        </aside>

        <div className="space-y-6">
          {(session ?? previewSession) ? (
            <Card>
              <CardHeading>Session summary</CardHeading>
              <CardDescription>
                {session
                  ? "Loaded from the interview session API."
                  : "Loaded from your evaluations history."}
              </CardDescription>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-[var(--text-muted)]">Title</dt>
                  <dd className="font-medium text-[var(--text-primary)]">
                    {session?.title ?? previewSession?.title ?? "Untitled session"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--text-muted)]">Status</dt>
                  <dd className="mt-1">
                    <SessionStatusBadge status={sessionStatus} />
                  </dd>
                </div>
                {session ? (
                  <>
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
                  </>
                ) : previewSession ? (
                  <>
                    <div>
                      <dt className="text-[var(--text-muted)]">Interview type</dt>
                      <dd className="font-medium text-[var(--text-primary)]">
                        {INTERVIEW_TYPE_LABELS[previewSession.interview_type]}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--text-muted)]">Completed</dt>
                      <dd className="font-medium text-[var(--text-primary)]">
                        {formatDate(previewSession.completed_at)}
                      </dd>
                    </div>
                    {previewSession.target_role ? (
                      <div className="sm:col-span-2">
                        <dt className="text-[var(--text-muted)]">Target role</dt>
                        <dd className="font-medium text-[var(--text-primary)]">
                          {previewSession.target_role}
                        </dd>
                      </div>
                    ) : null}
                  </>
                ) : null}
              </dl>
            </Card>
          ) : null}

          {evaluation ? (
            <>
              {evaluation.judge_summary || evaluation.coach_summary ? (
                <Card>
                  <CardHeading>Evaluator summary</CardHeading>
                  <CardDescription>Overall assessment from the evaluation panel.</CardDescription>
                  {evaluation.judge_summary ? (
                    <p className="mt-4 text-sm leading-6 text-[var(--text-muted)]">
                      {evaluation.judge_summary}
                    </p>
                  ) : null}
                  {evaluation.coach_summary ? (
                    <p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">
                      {evaluation.coach_summary}
                    </p>
                  ) : null}
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

              {evaluation.priority_improvements.length > 0 ? (
                <CollapsibleSection
                  title="All improvements"
                  description="Full list of priority improvements."
                  defaultOpen={false}
                >
                  <PriorityImprovements items={evaluation.priority_improvements} bare />
                </CollapsibleSection>
              ) : null}

              {evaluation.answer_evaluations.length > 0 ? (
                <CollapsibleSection
                  title="Answer evaluations"
                  description="Per-answer feedback from evaluators."
                  defaultOpen={false}
                >
                  <AnswerEvaluationList items={evaluation.answer_evaluations} bare />
                </CollapsibleSection>
              ) : null}

              {evaluation.better_answers.length > 0 ? (
                <CollapsibleSection
                  title="Better answer examples"
                  description="Suggested rewrites for stronger responses."
                  defaultOpen={false}
                >
                  <BetterAnswersList items={evaluation.better_answers} bare />
                </CollapsibleSection>
              ) : null}

              {evaluation.practice_recommendations.length > 0 ? (
                <CollapsibleSection
                  title="Practice recommendations"
                  description="What to rehearse before your next session."
                  defaultOpen={false}
                >
                  <PracticeRecommendations items={evaluation.practice_recommendations} bare />
                </CollapsibleSection>
              ) : null}
            </>
          ) : !isPreviewMode && isEvaluating ? (
            <Card>
              <CardHeading>Results will appear here</CardHeading>
              <CardDescription>
                Dimension scores, strengths, weaknesses, and coaching recommendations are being
                generated. This page refreshes automatically.
              </CardDescription>
            </Card>
          ) : null}
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
