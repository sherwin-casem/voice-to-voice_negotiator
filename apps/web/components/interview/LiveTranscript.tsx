import type { TranscriptEntry } from "@/types/websocket";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/format";

function speakerLabel(speaker: TranscriptEntry["speaker"]): string {
  if (speaker === "candidate") {
    return "You";
  }
  if (speaker === "interviewer") {
    return "Interviewer";
  }
  return "System";
}

export function LiveTranscript({ entries }: { entries: TranscriptEntry[] }) {
  return (
    <Card className="flex min-h-72 flex-col" aria-labelledby="live-transcript-title">
      <CardTitle id="live-transcript-title">Live transcript</CardTitle>
      <CardDescription>Partial and final transcript segments appear here.</CardDescription>
      <div
        className="mt-4 flex-1 space-y-3 overflow-y-auto rounded-xl border border-zinc-100 bg-zinc-50 p-3"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {entries.length === 0 ? (
          <p className="text-sm text-zinc-500">Transcript will appear once the interview starts.</p>
        ) : (
          entries.map((entry) => (
            <article key={entry.id} className="text-sm">
              <header className="mb-1 flex items-center gap-2">
                <span className="font-medium text-zinc-800">{speakerLabel(entry.speaker)}</span>
                {entry.isPartial ? (
                  <span className="text-xs text-zinc-500">(partial)</span>
                ) : null}
              </header>
              <p className={cn("leading-6 text-zinc-700", entry.isPartial && "italic")}>
                {entry.text}
              </p>
            </article>
          ))
        )}
      </div>
    </Card>
  );
}
