"use client";

import dynamic from "next/dynamic";
import Image from "next/image";

import type { InterviewerState } from "@/types/websocket";
import { cn } from "@/lib/format";

import { WaveformVisualizer } from "./WaveformVisualizer";

const InterviewerCharacter3D = dynamic(
  () =>
    import("@/components/interview/InterviewerCharacter3D").then((mod) => mod.InterviewerCharacter3D),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center">
        <Image
          src="/interviewer-avatar.svg"
          alt=""
          width={200}
          height={240}
          aria-hidden
          className="h-auto w-2/3 max-w-[200px] opacity-60"
        />
      </div>
    ),
  },
);

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
        <div className="absolute left-3 top-3 z-10 sm:left-4 sm:top-4">
          <WaveformVisualizer level={audioLevel} isActive={waveformActive} />
        </div>

        {isRecording ? (
          <div className="absolute right-3 top-3 z-10 flex items-center gap-2 rounded-full bg-black/40 px-3 py-1.5 text-xs text-red-300 backdrop-blur-sm sm:right-4 sm:top-4">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" aria-hidden="true" />
            <span>Recording</span>
            <span className="sr-only">Recording active</span>
          </div>
        ) : null}

        <div className="relative h-[min(36vh,320px)] min-h-[220px] bg-gradient-to-b from-slate-800/50 to-slate-900/80 sm:h-[min(42vh,380px)]">
          <InterviewerCharacter3D
            state={state}
            audioLevel={audioLevel}
            isRecording={isRecording}
            className="absolute inset-0"
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
