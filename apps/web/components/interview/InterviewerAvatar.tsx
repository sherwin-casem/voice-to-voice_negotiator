import Image from "next/image";

import type { InterviewerState } from "@/types/websocket";
import { cn } from "@/lib/format";

import { WaveformVisualizer } from "./WaveformVisualizer";

export function InterviewerAvatar({
  state,
  audioLevel,
  isRecording,
  questionSequence,
  className,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  questionSequence: number | null;
  className?: string;
}) {
  const isSpeaking = state === "speaking";
  const isListening = state === "listening" || isRecording;
  const waveformActive = isSpeaking || isListening || state === "processing";

  return (
    <div className={cn("relative flex flex-col", className)}>
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl gradient-border-glow",
          isSpeaking && "ring-2 ring-teal-500/40",
          isListening && "ring-2 ring-cyan-500/30",
        )}
      >
        <div className="absolute left-4 top-4 z-10">
          <WaveformVisualizer level={audioLevel} isActive={waveformActive} />
        </div>

        {isRecording ? (
          <div className="absolute right-4 top-4 z-10 flex items-center gap-2 rounded-full bg-black/40 px-3 py-1.5 text-xs text-red-300 backdrop-blur-sm">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" aria-hidden="true" />
            <span>Recording</span>
            <span className="sr-only">Recording active</span>
          </div>
        ) : null}

        <div className="relative flex aspect-[4/5] items-center justify-center bg-gradient-to-b from-slate-800/50 to-slate-900/80 p-6">
          <Image
            src="/interviewer-avatar.svg"
            alt="AI interviewer"
            width={280}
            height={340}
            className="h-auto w-full max-w-[280px] object-contain"
            priority
          />
        </div>
      </div>

      {questionSequence !== null && questionSequence > 0 ? (
        <div className="mt-3 rounded-xl bg-black/30 px-4 py-2 text-center backdrop-blur-sm">
          <p className="text-sm font-medium text-[var(--text-primary)]">
            Question {questionSequence}
          </p>
        </div>
      ) : null}
    </div>
  );
}
