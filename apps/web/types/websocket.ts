export type WsConnectionState = "idle" | "connecting" | "connected" | "disconnected" | "error";

export type InterviewerState =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "thinking";

export interface TranscriptEntry {
  id: string;
  speaker: "candidate" | "interviewer" | "system";
  text: string;
  isPartial?: boolean;
  timestamp: number;
}

export interface ServerWsEnvelope {
  type: string;
  payload: Record<string, unknown>;
  request_id?: string;
  timestamp_ms?: number;
}
