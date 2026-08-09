"use client";

import type { InterviewType } from "@voice/shared";
import { getInterviewerRole, INTERVIEW_TYPE_LABELS } from "@voice/shared";
import { motion, useReducedMotion } from "framer-motion";

import type { InterviewerState } from "@/types/websocket";
import { cn } from "@/lib/format";

import { InterviewerCharacterPortrait } from "./InterviewerCharacterPortrait";
import { WaveformVisualizer } from "./WaveformVisualizer";

function stateLabel(state: InterviewerState, isRecording: boolean): string {
  if (isRecording) return "Listening to you";
  if (state === "speaking") return "Speaking";
  if (state === "listening") return "Listening";
  if (state === "processing" || state === "thinking") return "Thinking";
  return "Ready";
}

export function InterviewerAvatar({
  state,
  audioLevel,
  isRecording,
  questionSequence,
  interviewType,
  className,
  footer,
}: {
  state: InterviewerState;
  audioLevel: number;
  isRecording: boolean;
  questionSequence: number | null;
  interviewType?: InterviewType;
  className?: string;
  /** Optional controls rendered inside the stage chrome (e.g. mic bar). */
  footer?: React.ReactNode;
}) {
  const reduceMotion = useReducedMotion();
  const isSpeaking = state === "speaking";
  const isListening = state === "listening" || isRecording;
  const isProcessing = state === "processing" || state === "thinking";
  const waveformActive = isSpeaking || isListening || isProcessing;

  const interviewerRole = getInterviewerRole(interviewType);
  const interviewTypeLabel = interviewType ? INTERVIEW_TYPE_LABELS[interviewType] : null;
  const status = stateLabel(state, isRecording);

  return (
    <motion.div
      className={cn("relative flex flex-col", className)}
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl border border-white/10 bg-[#060d18]",
          "shadow-[0_0_0_1px_rgba(20,184,166,0.08),0_24px_64px_rgba(0,0,0,0.45)]",
          isSpeaking && "ring-2 ring-teal-400/35",
          isListening && "ring-2 ring-cyan-400/30",
          isProcessing && "ring-2 ring-teal-500/20",
        )}
      >
        {/* Cinematic stage — landscape frame so the portrait fills without letterboxing */}
        <div className="relative aspect-[16/11] w-full sm:aspect-[16/10] lg:aspect-[16/10.5]">
          <InterviewerCharacterPortrait
            state={state}
            audioLevel={audioLevel}
            isRecording={isRecording}
            className="absolute inset-0"
            fillFrame
          />

          {/* Top gradient for overlay legibility */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-black/55 to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-black/70 to-transparent" />

          <div className="absolute left-3 top-3 z-10 flex max-w-[70%] flex-col gap-2 sm:left-4 sm:top-4">
            <div className="rounded-xl border border-white/10 bg-black/45 px-3 py-2 backdrop-blur-md">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-teal-300/80">
                Interviewer
              </p>
              <p className="text-sm font-semibold text-white">{interviewerRole}</p>
              {interviewTypeLabel ? (
                <p className="text-xs text-slate-300/85">{interviewTypeLabel}</p>
              ) : null}
            </div>

            <div
              className={cn(
                "inline-flex w-fit items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium backdrop-blur-md",
                isSpeaking && "border-teal-400/40 bg-teal-500/15 text-teal-200",
                isListening && "border-cyan-400/40 bg-cyan-500/15 text-cyan-200",
                isProcessing && "border-teal-400/30 bg-teal-500/10 text-teal-200/90",
                !isSpeaking &&
                  !isListening &&
                  !isProcessing &&
                  "border-white/10 bg-black/40 text-slate-300",
              )}
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  isSpeaking && "bg-teal-400 shadow-[0_0_8px_#14b8a6]",
                  isListening && "animate-pulse bg-cyan-400 shadow-[0_0_8px_#22d3ee]",
                  isProcessing && "animate-pulse bg-teal-300",
                  !isSpeaking && !isListening && !isProcessing && "bg-slate-400",
                )}
                aria-hidden
              />
              {status}
            </div>
          </div>

          <div className="absolute bottom-3 left-3 z-10 flex items-end gap-3 sm:bottom-4 sm:left-4">
            {questionSequence !== null && questionSequence > 0 ? (
              <div className="rounded-lg border border-white/10 bg-black/45 px-2.5 py-1.5 text-xs font-medium text-white/90 backdrop-blur-md">
                Q{questionSequence}
              </div>
            ) : null}
          </div>

          <div className="absolute bottom-3 right-3 z-10 rounded-xl border border-white/10 bg-black/45 px-2.5 py-2 backdrop-blur-md sm:bottom-4 sm:right-4">
            <WaveformVisualizer level={audioLevel} isActive={waveformActive} />
          </div>

          {isRecording ? (
            <div className="absolute right-3 top-3 z-10 flex items-center gap-2 rounded-full border border-red-400/30 bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-200 backdrop-blur-md sm:right-4 sm:top-4">
              <span className="h-2 w-2 animate-pulse rounded-full bg-red-400" aria-hidden="true" />
              Recording
            </div>
          ) : null}
        </div>

        {footer ? (
          <div className="border-t border-white/10 bg-black/35 px-3 py-3 backdrop-blur-md sm:px-4">
            {footer}
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
