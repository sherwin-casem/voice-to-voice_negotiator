import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function AudioActivityIndicator({
  level,
  isActive,
}: {
  level: number;
  isActive: boolean;
}) {
  const bars = Array.from({ length: 12 }, (_, index) => {
    const threshold = (index + 1) / 12;
    const active = isActive && level >= threshold;
    return active;
  });

  return (
    <Card aria-labelledby="audio-activity-title">
      <CardTitle id="audio-activity-title">Audio activity</CardTitle>
      <CardDescription>Input level from your microphone.</CardDescription>
      <div
        className="mt-4 flex h-12 items-end gap-1"
        role="meter"
        aria-label="Microphone input level"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(level * 100)}
      >
        {bars.map((active, index) => (
          <span
            key={index}
            className={`w-2 rounded-sm transition-colors ${
              active ? "bg-emerald-500" : "bg-zinc-200"
            }`}
            style={{ height: `${((index + 1) / 12) * 100}%` }}
            aria-hidden="true"
          />
        ))}
      </div>
    </Card>
  );
}
