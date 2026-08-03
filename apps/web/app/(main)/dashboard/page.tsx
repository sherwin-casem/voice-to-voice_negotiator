"use client";

import { INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { PreviewDataBanner } from "@/components/ui/Alert";
import { SessionStatusBadge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
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

      <div className="mb-6">
        <PreviewDataBanner endpoint="GET /api/v1/sessions" />
      </div>

      <Card aria-labelledby="recent-sessions-title">
        <CardTitle id="recent-sessions-title">Recent sessions</CardTitle>
        <CardDescription>Preview list until session history API is available.</CardDescription>
        <ul className="mt-4 divide-y divide-zinc-100">
          {MOCK_HISTORY_SESSIONS.map((session) => (
            <li key={session.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-medium text-zinc-900">{session.title}</p>
                <p className="mt-1 text-sm text-zinc-600">
                  {INTERVIEW_TYPE_LABELS[session.interview_type]}
                  {session.target_role ? ` · ${session.target_role}` : ""}
                </p>
                <p className="mt-1 text-xs text-zinc-500">Completed {formatDate(session.completed_at)}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <SessionStatusBadge status={session.status} />
                {session.overall_score !== null ? (
                  <span className="text-sm font-medium text-zinc-700">Score {session.overall_score}</span>
                ) : null}
                {session.status === "completed" ? (
                  <Link
                    href={`/interviews/${session.id}/results?preview=1`}
                    className="text-sm font-medium text-zinc-900 underline-offset-2 hover:underline"
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
