export const PREVIEW_LIVE_METRICS = {
  confidence: { label: "Confidence Score", value: "85%", percent: 85 },
  speakingPace: { label: "Speaking Pace", value: "Optimal", percent: 75 },
  fillerWords: { label: "Filler Words", value: "Low", percent: 25 },
  clarity: { label: "Clarity", value: "High", percent: 88 },
} as const;

export type PreviewLiveMetricKey = keyof typeof PREVIEW_LIVE_METRICS;
