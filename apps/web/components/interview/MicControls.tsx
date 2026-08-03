import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function MicControls({
  isEnabled,
  isRecording,
  permissionDenied,
  canAnswer,
  onToggleMic,
  onFinishAnswer,
  disabled,
}: {
  isEnabled: boolean;
  isRecording: boolean;
  permissionDenied: boolean;
  canAnswer: boolean;
  onToggleMic: () => void;
  onFinishAnswer: () => void;
  disabled?: boolean;
}) {
  return (
    <Card aria-labelledby="mic-controls-title">
      <CardTitle id="mic-controls-title">Microphone</CardTitle>
      <CardDescription>
        Enable your microphone to practice voice answers. Finish answer when you are done speaking.
      </CardDescription>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          variant={isRecording ? "danger" : "secondary"}
          onClick={onToggleMic}
          disabled={disabled || permissionDenied || !canAnswer}
          aria-pressed={isRecording}
        >
          {permissionDenied
            ? "Microphone blocked"
            : isRecording
              ? "Stop microphone"
              : isEnabled
                ? "Start microphone"
                : "Enable microphone"}
        </Button>
        <Button onClick={onFinishAnswer} disabled={disabled || !isEnabled || !canAnswer}>
          Finish answer
        </Button>
      </div>
      {permissionDenied ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          Microphone access was denied. Check browser permissions and try again.
        </p>
      ) : null}
    </Card>
  );
}
