"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  AnswerEvaluationList,
  BetterAnswersList,
  PracticeRecommendations,
} from "@/components/evaluation/AnswerEvaluation";
import { DimensionScores } from "@/components/evaluation/DimensionScores";
import { FeedbackList, PriorityImprovements } from "@/components/evaluation/FeedbackSections";
import { OverallScoreCard } from "@/components/evaluation/OverallScoreCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, PreviewDataBanner, Spinner } from "@/components/ui/Alert";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { useAppContext } from "@/context/AppProvider";
import { ApiClientError } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import { buildPreviewEvaluation } from "@/lib/mocks/evaluation";
import { getSession } from "@/lib/interview-api";
import type { SessionResponse } from "@voice/shared";

export default function InterviewResultsPage() {
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const sessionId = params.sessionId;
  const isPreviewMode = searchParams.get("preview") === "1";
  const { userId } = useAppContext();

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(!isPreviewMode);

  useEffect(() => {
    if (isPreviewMode || !userId || !sessionId) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    getSession(userId, sessionId)
      .then((loaded) => {
        if (!cancelled) {
          setSession(loaded);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setLoadError(
            caught instanceof ApiClientError ? caught.message : "Unable to load session.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isPreviewMode, sessionId, userId]);

  const evaluation = useMemo(
    () => buildPreviewEvaluation(session?.title ?? "Interview session"),
    [session?.title],
  );

  if (isLoading) {
    return <Spinner label="Loading results" />;
  }

  return (
    <>
      <PageHeader
        title="Interview results"
        description="Multi-agent evaluation, scoring, and coaching recommendations."
        actions={
          <>
            <ButtonLink href="/dashboard" variant="secondary">
              Dashboard
            </ButtonLink>
            <ButtonLink href="/interviews/new">New interview</ButtonLink>
          </>
        }
      />

      <div className="mb-6 space-y-4">
        <PreviewDataBanner endpoint="GET /api/v1/sessions/{id}/evaluation" />
        {loadError ? <Alert variant="warning">{loadError}</Alert> : null}
      </div>

      {session ? (
        <Card className="mb-6">
          <CardTitle>Session summary</CardTitle>
          <CardDescription>Loaded from the interview session API.</CardDescription>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-zinc-600">Title</dt>
              <dd className="font-medium text-zinc-900">{session.title ?? "Untitled session"}</dd>
            </div>
            <div>
              <dt className="text-zinc-600">Status</dt>
              <dd className="mt-1">
                <SessionStatusBadge status={session.status} />
              </dd>
            </div>
            <div>
              <dt className="text-zinc-600">Questions asked</dt>
              <dd className="font-medium text-zinc-900">{session.question_count}</dd>
            </div>
            <div>
              <dt className="text-zinc-600">Ended</dt>
              <dd className="font-medium text-zinc-900">{formatDate(session.ended_at)}</dd>
            </div>
          </dl>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <OverallScoreCard score={evaluation.overall_score} />
        <div className="lg:col-span-2">
          <DimensionScores scores={evaluation.dimension_scores} />
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <FeedbackList
          title="Strengths"
          description="Evidence-backed positives from evaluators."
          items={evaluation.strengths}
          emptyMessage="No strengths recorded."
        />
        <FeedbackList
          title="Weaknesses"
          description="Specific gaps identified during evaluation."
          items={evaluation.weaknesses}
          emptyMessage="No weaknesses recorded."
        />
      </div>

      <div className="mt-6 space-y-6">
        <PriorityImprovements items={evaluation.priority_improvements} />
        <AnswerEvaluationList items={evaluation.answer_evaluations} />
        <BetterAnswersList items={evaluation.better_answers} />
        <PracticeRecommendations items={evaluation.practice_recommendations} />
      </div>
    </>
  );
}
