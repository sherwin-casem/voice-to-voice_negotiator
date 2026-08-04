"use client";

import type { InterviewType } from "@voice/shared";
import { getInterviewerRole, INTERVIEW_TYPE_LABELS } from "@voice/shared";

import type { InterviewerState } from "@/types/websocket";
import { cn } from "@/lib/format";

import { InterviewerCharacterPortrait } from "./InterviewerCharacterPortrait";
import { WaveformVisualizer } from "./WaveformVisualizer";

export function InterviewerAvatar({
  state,
  audioLevel,
  isRecording,
  questionSequence,
  interviewType,
  className,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  questionSequence: number | null;
  interviewType?: InterviewType;
  className?: string;
}) {
  const isSpeaking = state === "speaking";
  const isListening = state === "listening" || isRecording;
  const isProcessing = state === "processing" || state === "thinking";
  const waveformActive = isSpeaking || isListening || isProcessing;

  const interviewerRole = getInterviewerRole(interviewType);
  const interviewTypeLabel = interviewType ? INTERVIEW_TYPE_LABELS[interviewType] : null;

  return (
    <div className={cn("relative flex flex-col", className)}>
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl gradient-border-glow",
          isSpeaking && "ring-2 ring-teal-500/40",
          isListening && "ring-2 ring-cyan-500/30",
        )}
      >
        <div className="absolute left-3 top-3 z-10 rounded-xl bg-black/50 px-3 py-2 backdrop-blur-sm sm:left-4 sm:top-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-teal-300/75">
            Interviewer
          </p>
          <p className="text-sm font-semibold text-[var(--text-primary)]">{interviewerRole}</p>
          {interviewTypeLabel ? (
            <p className="text-xs text-[var(--text-muted)]">{interviewTypeLabel} interview</p>
          ) : null}
        </div>

        <div className="absolute bottom-3 right-3 z-10 rounded-lg bg-black/45 px-2.5 py-2 backdrop-blur-sm sm:bottom-4 sm:right-4">
          <WaveformVisualizer level={audioLevel} isActive={waveformActive} />
        </div>

        {isRecording ? (
          <div className="absolute right-3 top-3 z-10 flex items-center gap-2 rounded-full bg-black/40 px-3 py-1.5 text-xs text-red-300 backdrop-blur-sm sm:right-4 sm:top-4">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" aria-hidden="true" />
            <span>Recording</span>
            <span className="sr-only">Recording active</span>
          </div>
        ) : null}

        <div className="relative h-[clamp(280px,48vh,520px)] w-full bg-gradient-to-b from-slate-800/50 to-slate-900/80 sm:h-[clamp(320px,52vh,580px)] lg:h-[clamp(360px,58vh,640px)]">
          <InterviewerCharacterPortrait
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
