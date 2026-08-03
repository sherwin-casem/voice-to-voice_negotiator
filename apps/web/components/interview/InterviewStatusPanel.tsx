import type { InterviewSessionStatus } from "@voice/shared";

import { SessionStatusBadge } from "@/components/ui/Badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function InterviewStatusPanel({
  status,
  questionCount,
}: {
  status: InterviewSessionStatus;
  questionCount: number;
}) {
  return (
    <Card aria-labelledby="interview-status-title">
      <CardTitle id="interview-status-title">Interview status</CardTitle>
      <CardDescription>Current session lifecycle state.</CardDescription>
      <dl className="mt-4 grid gap-3 text-sm">
        <div className="flex items-center justify-between gap-3">
          <dt className="text-zinc-600">Status</dt>
          <dd>
            <SessionStatusBadge status={status} />
          </dd>
        </div>
        <div className="flex items-center justify-between gap-3">
          <dt className="text-zinc-600">Questions asked</dt>
          <dd className="font-medium text-zinc-900">{questionCount}</dd>
        </div>
      </dl>
    </Card>
  );
}
