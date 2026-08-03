"use client";

import { INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { PreviewDataBanner } from "@/components/ui/Alert";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { formatDate } from "@/lib/format";
import { MOCK_HISTORY_SESSIONS } from "@/lib/mocks/history";

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Review recent practice sessions and start a new interview."
        actions={<ButtonLink href="/interviews/new">Create interview</ButtonLink>}
      />

      <GlassPanel className="mb-6 border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-cyan-500/5 p-6">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Ready to practice?
        </h2>
        <p className="mt-2 max-w-xl text-sm text-[var(--text-muted)]">
          Run a voice mock interview with AI feedback on communication, structure, and role fit.
        </p>
        <div className="mt-4">
          <ButtonLink href="/interviews/new">Start new session</ButtonLink>
        </div>
      </GlassPanel>

      <div className="mb-6">
        <PreviewDataBanner endpoint="GET /api/v1/sessions" />
      </div>

      <Card aria-labelledby="recent-sessions-title">
        <CardHeading id="recent-sessions-title">Recent sessions</CardHeading>
        <CardDescription>Preview list until session history API is available.</CardDescription>
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
                  Completed {formatDate(session.completed_at)}
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
    </>
  );
}
