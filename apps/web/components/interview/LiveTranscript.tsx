"use client";

import { useState } from "react";

import type { TranscriptEntry } from "@/types/websocket";
import { Card, CardTitle } from "@/components/ui/Card";
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
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="flex flex-col" aria-labelledby="live-transcript-title">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between text-left"
        aria-expanded={expanded}
        aria-controls="live-transcript-panel"
      >
        <CardTitle id="live-transcript-title">Transcript</CardTitle>
        <span className="text-xs text-[var(--text-muted)]">{expanded ? "Hide" : "Show"}</span>
      </button>
      {expanded ? (
        <div
          id="live-transcript-panel"
          className="mt-4 max-h-48 space-y-3 overflow-y-auto rounded-xl border border-[var(--border-glass)] bg-black/20 p-3"
          aria-live="polite"
          aria-relevant="additions text"
        >
          {entries.length === 0 ? (
            <p className="text-sm text-[var(--text-dim)]">
              Transcript will appear once the interview starts.
            </p>
          ) : (
            entries.map((entry) => (
              <article key={entry.id} className="text-sm">
                <header className="mb-1 flex items-center gap-2">
                  <span className="font-medium text-teal-300/90">{speakerLabel(entry.speaker)}</span>
                  {entry.isPartial ? (
                    <span className="text-xs text-[var(--text-dim)]">(partial)</span>
                  ) : null}
                </header>
                <p
                  className={cn(
                    "leading-6 text-[var(--text-muted)]",
                    entry.isPartial && "italic",
                  )}
                >
                  {entry.text}
                </p>
              </article>
            ))
          )}
        </div>
      ) : null}
    </Card>
  );
}
