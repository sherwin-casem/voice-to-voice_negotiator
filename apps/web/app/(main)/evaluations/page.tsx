"use client";

import type { InterviewSessionStatus, SessionSummaryResponse } from "@voice/shared";
import { INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Spinner } from "@/components/ui/Alert";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GlowArt } from "@/components/ui/GlowArt";
import { MetricBar } from "@/components/ui/MetricBar";
import { Reveal } from "@/components/visuals/Reveal";
import { useProgressAnalysis } from "@/hooks/useProgressAnalysis";
import { useSessionHistory } from "@/hooks/useSessionHistory";
import { cn, formatDate } from "@/lib/format";
import { routes } from "@/lib/routes";

function canViewSessionResults(session: SessionSummaryResponse): boolean {
  return session.status === "completed";
}

function RecentSessionRow({ session }: { session: SessionSummaryResponse }) {
  const isClickable = canViewSessionResults(session);
  const rowClassName = cn(
    "flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between",
    isClickable &&
      "-mx-3 rounded-xl px-3 transition-colors hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500",
  );

  const title = session.title ?? "Untitled session";

  const content = (
    <>
      <div>
        <p
          className={cn(
            "font-medium text-[var(--text-primary)]",
            isClickable && "group-hover:text-teal-300",
          )}
        >
          {title}
        </p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          {INTERVIEW_TYPE_LABELS[session.interview_type]}
          {session.target_role ? ` · ${session.target_role}` : ""}
        </p>
        <p className="mt-1 text-xs text-[var(--text-dim)]">
          {session.ended_at
            ? `Completed ${formatDate(session.ended_at)}`
            : "Not completed"}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <SessionStatusBadge status={session.status as InterviewSessionStatus} />
        {session.overall_score !== null ? (
          <span className="text-sm font-medium text-teal-300">
            Score {Math.round(session.overall_score)}
          </span>
        ) : null}
        {isClickable ? (
          <span className="text-sm font-medium text-teal-400 group-hover:text-teal-300">
            View results →
          </span>
        ) : null}
      </div>
    </>
  );

  if (!isClickable) {
    return <li className={rowClassName}>{content}</li>;
  }

  return (
    <li>
      <Link href={routes.sessionResults(session.id)} className={cn("group block", rowClassName)}>
        {content}
      </Link>
    </li>
  );
}

export default function EvaluationsPage() {
  const {
    data: progress,
    error: progressError,
    isLoading: progressLoading,
  } = useProgressAnalysis();
  const {
    sessions,
    error: sessionsError,
    isLoading: sessionsLoading,
  } = useSessionHistory();

  const isLoading = progressLoading || sessionsLoading;
  const error = progressError ?? sessionsError;

  const hasTrends = (progress?.dimension_trends.length ?? 0) > 0;
  const hasSessions = sessions.length > 0;
  const isEmpty =
    !isLoading &&
    !error &&
    (progress?.sessions_analyzed ?? 0) === 0 &&
    !hasSessions;

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Loading evaluations" />
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title="Evaluations"
        description="Track dimension trends and review past practice sessions."
        actions={
          <>
            <ButtonLink href={routes.home} variant="secondary">
              Home
            </ButtonLink>
            <ButtonLink href={routes.createInterview}>New interview</ButtonLink>
          </>
        }
      />

      {error ? (
        <Alert variant="error" title="Unable to load evaluations">
          {error}
        </Alert>
      ) : null}

      {isEmpty ? (
        <Reveal>
          <GlassPanel className="relative overflow-hidden border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-cyan-500/5 p-8 text-center">
            <GlowArt
              src="/backgrounds/insight-sphere.png"
              width={512}
              height={512}
              sizes="14rem"
              className="mx-auto mb-4 w-56 animate-float-slow"
            />
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">No practice sessions yet</h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-[var(--text-muted)]">
              Complete your first voice interview to unlock evaluation trends, dimension scores, and
              session history.
            </p>
            <div className="mt-6">
              <ButtonLink href={routes.createInterview}>Start your first interview</ButtonLink>
            </div>
          </GlassPanel>
        </Reveal>
      ) : null}

      {hasTrends ? (
        <Reveal>
          <Card className="relative mb-6 overflow-hidden" aria-labelledby="dimension-trends-title">
            <GlowArt
              src="/backgrounds/score-ring.png"
              width={512}
              height={512}
              sizes="20rem"
              className="pointer-events-none absolute -right-20 -top-24 hidden w-80 opacity-25 lg:block"
            />
            <div className="relative">
              <CardHeading id="dimension-trends-title">Dimension trends</CardHeading>
          <CardDescription>
            Latest session scores compared to your previous average
            {progress?.sessions_analyzed
              ? ` (${progress.sessions_analyzed} sessions analyzed)`
              : ""}
            .
          </CardDescription>
          <ul className="mt-4 space-y-4">
            {progress?.dimension_trends.map((trend) => {
              const latest = Math.round(trend.recent_average);
              const delta = Math.round(trend.delta);
              const direction = delta >= 0 ? "up" : "down";
              return (
                <li
                  key={trend.dimension}
                  className="rounded-xl border border-[var(--border-glass)] bg-white/5 p-4"
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-[var(--text-primary)]">{trend.label}</p>
                    <p className="text-sm text-[var(--text-muted)]">
                      {latest} ({direction === "up" ? "+" : ""}
                      {delta} vs previous)
                    </p>
                  </div>
                  <MetricBar label={trend.label} value={`${latest}%`} percent={latest} />
                </li>
              );
            })}
          </ul>
            </div>
          </Card>
        </Reveal>
      ) : null}

      {hasSessions ? (
        <Reveal delayMs={90}>
          <Card aria-labelledby="recent-sessions-title">
          <CardHeading id="recent-sessions-title">Recent sessions</CardHeading>
          <CardDescription>Your interview practice history, newest first.</CardDescription>
          <ul className="mt-4 divide-y divide-[var(--border-glass)]">
            {sessions.map((session) => (
              <RecentSessionRow key={session.id} session={session} />
            ))}
          </ul>
        </Card>
        </Reveal>
      ) : !isEmpty ? (
        <Reveal delayMs={90}>
          <Card aria-labelledby="recent-sessions-title">
          <CardHeading id="recent-sessions-title">Recent sessions</CardHeading>
          <CardDescription>Your completed interviews will appear here.</CardDescription>
          <p className="mt-4 text-sm text-[var(--text-muted)]">
            No sessions recorded yet.{" "}
            <Link href={routes.createInterview} className="text-teal-400 hover:text-teal-300">
              Create an interview
            </Link>{" "}
            to get started.
          </p>
        </Card>
        </Reveal>
      ) : null}
    </>
  );
}
