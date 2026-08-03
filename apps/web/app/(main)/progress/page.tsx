"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PreviewDataBanner } from "@/components/ui/Alert";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { MOCK_PROGRESS_TRENDS } from "@/lib/mocks/history";

export default function ProgressPage() {
  return (
    <>
      <PageHeader
        title="Progress and history"
        description="Track dimension trends across practice sessions over time."
        actions={<ButtonLink href="/interviews/new">Create interview</ButtonLink>}
      />

      <div className="mb-6">
        <PreviewDataBanner endpoint="GET /api/v1/progress" />
      </div>

      <Card aria-labelledby="dimension-trends-title">
        <CardTitle id="dimension-trends-title">Dimension trends</CardTitle>
        <CardDescription>Latest session scores compared to your previous average.</CardDescription>
        <ul className="mt-4 space-y-4">
          {MOCK_PROGRESS_TRENDS.map((trend) => {
            const delta = trend.latest - trend.previous;
            const direction = delta >= 0 ? "up" : "down";
            return (
              <li key={trend.dimension} className="rounded-xl border border-zinc-100 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-zinc-900">{trend.dimension}</p>
                  <p className="text-sm text-zinc-600">
                    {trend.latest} ({direction === "up" ? "+" : ""}
                    {delta} vs previous)
                  </p>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-100">
                  <div
                    className="h-full rounded-full bg-zinc-900"
                    style={{ width: `${trend.latest}%` }}
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={trend.latest}
                    aria-label={`${trend.dimension} progress`}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      </Card>
    </>
  );
}
