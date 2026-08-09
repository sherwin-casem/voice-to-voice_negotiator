"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useState } from "react";

import type { TranscriptEntry } from "@/types/websocket";
import { cn } from "@/lib/format";

function speakerLabel(speaker: TranscriptEntry["speaker"]): string {
  if (speaker === "candidate") return "You";
  if (speaker === "interviewer") return "Interviewer";
  return "System";
}

export function LiveTranscript({ entries }: { entries: TranscriptEntry[] }) {
  const [expanded, setExpanded] = useState(false);
  const reduceMotion = useReducedMotion();

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/[0.03]"
        aria-expanded={expanded}
        aria-controls="live-transcript-panel"
      >
        <div className="flex items-center gap-3">
          <p id="live-transcript-title" className="text-sm font-semibold text-[var(--text-primary)]">
            Transcript
          </p>
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-[11px] text-slate-400">
            {entries.length} {entries.length === 1 ? "line" : "lines"}
          </span>
        </div>
        <span className="text-xs text-[var(--text-muted)]">{expanded ? "Hide" : "Show"}</span>
      </button>

      <AnimatePresence initial={false}>
        {expanded ? (
          <motion.div
            id="live-transcript-panel"
            key="panel"
            initial={reduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div
              className="max-h-52 space-y-3 overflow-y-auto border-t border-white/10 px-4 py-3"
              aria-live="polite"
              aria-relevant="additions text"
            >
              {entries.length === 0 ? (
                <p className="text-sm text-[var(--text-dim)]">
                  Transcript appears once the interview starts.
                </p>
              ) : (
                entries.map((entry) => (
                  <article key={entry.id} className="text-sm">
                    <header className="mb-1 flex items-center gap-2">
                      <span className="font-medium text-teal-300/90">
                        {speakerLabel(entry.speaker)}
                      </span>
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
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
