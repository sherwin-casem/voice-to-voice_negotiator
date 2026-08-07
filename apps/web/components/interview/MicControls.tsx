import { Button } from "@/components/ui/Button";
import { GlassPanel } from "@/components/ui/GlassPanel";

export function MicControls({
  isEnabled,
  isRecording,
  permissionDenied,
  canAnswer,
  onToggleMic,
  onFinishAnswer,
  disabled,
  compact = false,
}: {
  isEnabled: boolean;
  isRecording: boolean;
  permissionDenied: boolean;
  canAnswer: boolean;
  onToggleMic: () => void;
  onFinishAnswer: () => void;
  disabled?: boolean;
  compact?: boolean;
}) {
  return (
    <GlassPanel className={compact ? "p-3" : "p-4"}>
      {!compact ? (
        <p className="text-section-label mb-3">Microphone</p>
      ) : null}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button
          variant={isRecording ? "danger" : "secondary"}
          onClick={onToggleMic}
          disabled={disabled || permissionDenied || !canAnswer}
          aria-pressed={isRecording}
          className={compact ? "text-xs px-4 py-1.5" : undefined}
        >
          {permissionDenied
            ? "Mic blocked"
            : isRecording
              ? "Pause"
              : isEnabled
                ? "Resume mic"
                : "Start answer"}
        </Button>
        <Button
          onClick={onFinishAnswer}
          disabled={disabled || !isEnabled || !canAnswer}
          className={compact ? "text-xs px-4 py-1.5" : undefined}
        >
          Finish answer
        </Button>
      </div>
      {isRecording ? (
        <p className="mt-2 text-center text-xs text-[var(--text-dim)]">
          Pause keeps your answer open. Finish answer sends it to the interviewer.
        </p>
      ) : null}
      {permissionDenied ? (
        <p className="mt-2 text-center text-xs text-red-400" role="alert">
          Microphone access denied. Check browser permissions.
        </p>
      ) : null}
    </GlassPanel>
  );
}
