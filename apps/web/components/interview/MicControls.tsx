"use client";

import { motion, useReducedMotion } from "framer-motion";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/format";

export function MicControls({
  isEnabled,
  isRecording,
  permissionDenied,
  canAnswer,
  onToggleMic,
  onFinishAnswer,
  disabled,
  compact = false,
  embedded = false,
}: {
  isEnabled: boolean;
  isRecording: boolean;
  permissionDenied: boolean;
  canAnswer: boolean;
  onToggleMic: () => void;
  onFinishAnswer: () => void;
  disabled?: boolean;
  compact?: boolean;
  /** Render without outer glass chrome (for stage footer). */
  embedded?: boolean;
}) {
  const reduceMotion = useReducedMotion();
  const toggleDisabled = disabled || permissionDenied || !canAnswer;
  const finishDisabled = disabled || !isEnabled || !canAnswer;

  const toggleLabel = permissionDenied
    ? "Mic blocked"
    : isRecording
      ? "Pause answer"
      : isEnabled
        ? "Resume answer"
        : "Start answer";

  return (
    <div className={cn(!embedded && "glass-panel p-3 sm:p-4")}>
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
        <motion.div
          whileHover={reduceMotion || toggleDisabled ? undefined : { scale: 1.02 }}
          whileTap={reduceMotion || toggleDisabled ? undefined : { scale: 0.98 }}
        >
          <Button
            variant={isRecording ? "danger" : "primary"}
            onClick={onToggleMic}
            disabled={toggleDisabled}
            aria-pressed={isRecording}
            className={cn(
              "min-w-[9.5rem]",
              compact ? "px-5 py-2 text-sm" : "px-6 py-2.5 text-sm",
              !isRecording &&
                !toggleDisabled &&
                "shadow-[0_0_28px_rgba(20,184,166,0.35)]",
            )}
          >
            {isRecording ? (
              <span className="mr-2 inline-flex h-2 w-2 animate-pulse rounded-full bg-white" aria-hidden />
            ) : null}
            {toggleLabel}
          </Button>
        </motion.div>

        <Button
          variant="secondary"
          onClick={onFinishAnswer}
          disabled={finishDisabled}
          className={cn(
            "min-w-[9.5rem] border-white/20 bg-white/10 text-white hover:bg-white/15",
            compact ? "px-5 py-2 text-sm" : "px-6 py-2.5 text-sm",
          )}
        >
          Finish answer
        </Button>
      </div>

      {isRecording ? (
        <p className="mt-2 text-center text-xs text-slate-400">
          Pause keeps your answer open. Finish sends it to the interviewer.
        </p>
      ) : null}
      {permissionDenied ? (
        <p className="mt-2 text-center text-xs text-red-400" role="alert">
          Microphone access denied. Check browser permissions.
        </p>
      ) : null}
      {disabled && !permissionDenied ? (
        <p className="mt-2 text-center text-xs text-slate-500">
          Press Start to begin the interview, then answer by voice.
        </p>
      ) : null}
    </div>
  );
}
