"use client";

import { INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { MetricBar } from "@/components/ui/MetricBar";
import { formatDate } from "@/lib/format";
import { MOCK_HISTORY_SESSIONS, MOCK_PROGRESS_TRENDS } from "@/lib/mocks/history";

const SHOW_PREVIEW_DATA = MOCK_HISTORY_SESSIONS.length > 0 || MOCK_PROGRESS_TRENDS.length > 0;

export default function ProgressPage() {
  const hasSessions = MOCK_HISTORY_SESSIONS.length > 0;
  const hasTrends = MOCK_PROGRESS_TRENDS.length > 0;

  return (
    <>
      <PageHeader
        title="Progress and history"
        description="Track dimension trends and review past practice sessions."
      />

      {!SHOW_PREVIEW_DATA ? (
        <GlassPanel className="border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-cyan-500/5 p-8 text-center">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">No practice sessions yet</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-[var(--text-muted)]">
            Complete your first voice interview to unlock progress trends, dimension scores, and
            session history.
          </p>
          <div className="mt-6">
            <ButtonLink href="/interviews/new">Start your first interview</ButtonLink>
          </div>
        </GlassPanel>
      ) : null}

      {hasTrends ? (
        <Card className="mb-6" aria-labelledby="dimension-trends-title">
          <CardHeading id="dimension-trends-title">Dimension trends</CardHeading>
          <CardDescription>Latest session scores compared to your previous average.</CardDescription>
          <ul className="mt-4 space-y-4">
            {MOCK_PROGRESS_TRENDS.map((trend) => {
              const delta = trend.latest - trend.previous;
              const direction = delta >= 0 ? "up" : "down";
              return (
                <li
                  key={trend.dimension}
                  className="rounded-xl border border-[var(--border-glass)] bg-white/5 p-4"
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-[var(--text-primary)]">{trend.dimension}</p>
                    <p className="text-sm text-[var(--text-muted)]">
                      {trend.latest} ({direction === "up" ? "+" : ""}
                      {delta} vs previous)
                    </p>
                  </div>
                  <MetricBar
                    label={trend.dimension}
                    value={`${trend.latest}%`}
                    percent={trend.latest}
                  />
                </li>
              );
            })}
          </ul>
        </Card>
      ) : null}

      {hasSessions ? (
        <Card aria-labelledby="recent-sessions-title">
          <CardHeading id="recent-sessions-title">Recent sessions</CardHeading>
          <CardDescription>
            Session history will load from the API when available. Showing preview data for now.
          </CardDescription>
          <ul className="mt-4 divide-y divide-[var(--border-glass)]">
            {MOCK_HISTORY_SESSIONS.map((session) => (
              <li
                key={session.id}
                className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium text-[var(--text-primary)]">{session.title}</p>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">
                    {INTERVIEW_TYPE_LABELS[session.interview_type]}
                    {session.target_role ? ` · ${session.target_role}` : ""}
                  </p>
                  <p className="mt-1 text-xs text-[var(--text-dim)]">
                    {session.completed_at
                      ? `Completed ${formatDate(session.completed_at)}`
                      : "Not completed"}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <SessionStatusBadge status={session.status} />
                  {session.overall_score !== null ? (
                    <span className="text-sm font-medium text-teal-300">
                      Score {session.overall_score}
                    </span>
                  ) : null}
                  {session.status === "completed" ? (
                    <Link
                      href={`/interviews/${session.id}/results?preview=1`}
                      className="text-sm font-medium text-teal-400 underline-offset-2 hover:text-teal-300 hover:underline"
                    >
                      View results
                    </Link>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <Card aria-labelledby="recent-sessions-title">
          <CardHeading id="recent-sessions-title">Recent sessions</CardHeading>
          <CardDescription>Your completed interviews will appear here.</CardDescription>
          <p className="mt-4 text-sm text-[var(--text-muted)]">
            No sessions recorded yet.{" "}
            <Link href="/interviews/new" className="text-teal-400 hover:text-teal-300">
              Create an interview
            </Link>{" "}
            to get started.
          </p>
        </Card>
      )}
    </>
  );
}
