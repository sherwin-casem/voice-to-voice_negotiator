"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PreviewDataBanner } from "@/components/ui/Alert";
import { MetricBar } from "@/components/ui/MetricBar";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
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
        <CardHeading id="dimension-trends-title">Dimension trends</CardHeading>
        <CardDescription>Latest session scores compared to your previous average.</CardDescription>
        <ul className="mt-4 space-y-4">
          {MOCK_PROGRESS_TRENDS.map((trend) => {
            const delta = trend.latest - trend.previous;
            const direction = delta >= 0 ? "up" : "down";
            return (
              <li key={trend.dimension} className="rounded-xl border border-[var(--border-glass)] bg-white/5 p-4">
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
    </>
  );
}
