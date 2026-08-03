import { PREVIEW_LIVE_METRICS } from "@/lib/mocks/live-metrics";

export function useLiveMetricsPreview() {
  return {
    isPreview: true as const,
    metrics: PREVIEW_LIVE_METRICS,
  };
}
