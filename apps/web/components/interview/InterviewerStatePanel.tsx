import type { InterviewerState } from "@/types/websocket";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/format";

const STATE_LABELS: Record<InterviewerState, string> = {
  idle: "Idle",
  listening: "Listening",
  processing: "Processing",
  speaking: "Speaking",
  thinking: "Thinking",
};

const STATE_COLORS: Record<InterviewerState, string> = {
  idle: "bg-zinc-200",
  listening: "bg-emerald-500",
  processing: "bg-amber-500",
  speaking: "bg-blue-500",
  thinking: "bg-violet-500",
};

export function InterviewerStatePanel({ state }: { state: InterviewerState }) {
  return (
    <Card aria-labelledby="interviewer-state-title">
      <CardTitle id="interviewer-state-title">AI interviewer</CardTitle>
      <CardDescription>Current interviewer activity.</CardDescription>
      <div className="mt-4 flex items-center gap-3">
        <span
          className={cn("h-3 w-3 rounded-full", STATE_COLORS[state])}
          aria-hidden="true"
        />
        <p className="text-sm font-medium text-zinc-900" aria-live="polite">
          {STATE_LABELS[state]}
        </p>
      </div>
    </Card>
  );
}
