import { GlassPanel } from "@/components/ui/GlassPanel";

export function CurrentQuestion({
  question,
  sequenceNum,
}: {
  question: string | null;
  sequenceNum: number | null;
}) {
  if (!question) {
    return null;
  }

  return (
    <GlassPanel className="p-4" aria-live="polite">
      {sequenceNum ? (
        <p className="text-section-label mb-2">Question {sequenceNum}</p>
      ) : null}
      <p className="text-base leading-relaxed text-[var(--text-primary)]">{question}</p>
    </GlassPanel>
  );
}
