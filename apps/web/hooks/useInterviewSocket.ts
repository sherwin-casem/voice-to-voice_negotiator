"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { InterviewWebSocket } from "@/lib/ws-client";
import type {
  InterviewerState,
  ServerWsEnvelope,
  TranscriptEntry,
  WsConnectionState,
} from "@/types/websocket";

function nextEntryId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function mapInterviewerState(payload: Record<string, unknown>): InterviewerState {
  const raw = String(payload.state ?? payload.phase ?? "idle");
  if (raw === "listening" || raw === "processing" || raw === "speaking" || raw === "thinking") {
    return raw;
  }
  return "idle";
}

export interface LiveInterviewState {
  connectionState: WsConnectionState;
  interviewerState: InterviewerState;
  transcript: TranscriptEntry[];
  currentQuestion: string | null;
  currentQuestionSequence: number | null;
  errorMessage: string | null;
  connect: () => void;
  disconnect: () => void;
  startInterview: () => void;
  finishAnswer: () => void;
}

export function useInterviewSocket(sessionId: string, userId: string): LiveInterviewState {
  const [connectionState, setConnectionState] = useState<WsConnectionState>("idle");
  const [interviewerState, setInterviewerState] = useState<InterviewerState>("idle");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [currentQuestionSequence, setCurrentQuestionSequence] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clientRef = useRef<InterviewWebSocket | null>(null);

  const appendTranscript = useCallback(
    (speaker: TranscriptEntry["speaker"], text: string, isPartial = false) => {
      if (!text.trim()) {
        return;
      }
      setTranscript((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.speaker === speaker && last.isPartial && isPartial) {
          return [...prev.slice(0, -1), { ...last, text, timestamp: Date.now() }];
        }
        return [
          ...prev,
          {
            id: nextEntryId(speaker),
            speaker,
            text,
            isPartial,
            timestamp: Date.now(),
          },
        ];
      });
    },
    [],
  );

  const handleEnvelope = useCallback(
    (envelope: ServerWsEnvelope) => {
      const { type, payload } = envelope;

      switch (type) {
        case "session.ready":
          setConnectionState("connected");
          appendTranscript("system", "Session connected. Ready to start.");
          break;
        case "session.started":
          appendTranscript("system", "Interview started.");
          break;
        case "interviewer.state":
          setInterviewerState(mapInterviewerState(payload));
          break;
        case "interviewer.question":
          setCurrentQuestion(String(payload.question_text ?? payload.text ?? ""));
          setCurrentQuestionSequence(
            typeof payload.sequence_num === "number" ? payload.sequence_num : null,
          );
          appendTranscript("interviewer", String(payload.question_text ?? payload.text ?? ""));
          setInterviewerState("speaking");
          break;
        case "transcript.partial":
          appendTranscript(
            payload.speaker === "interviewer" ? "interviewer" : "candidate",
            String(payload.text ?? ""),
            true,
          );
          break;
        case "transcript.final":
          appendTranscript(
            payload.speaker === "interviewer" ? "interviewer" : "candidate",
            String(payload.text ?? ""),
            false,
          );
          break;
        case "session.error":
          setErrorMessage(String(payload.message ?? "Unknown session error"));
          setConnectionState("error");
          break;
        default:
          break;
      }
    },
    [appendTranscript],
  );

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    setConnectionState("disconnected");
  }, []);

  const connect = useCallback(() => {
    if (!sessionId || !userId) {
      return;
    }
    disconnect();
    setConnectionState("connecting");
    setErrorMessage(null);

    const client = new InterviewWebSocket(sessionId, userId);
    clientRef.current = client;
    client.connect(handleEnvelope, (open) => {
      setConnectionState(open ? "connected" : "disconnected");
    });
  }, [disconnect, handleEnvelope, sessionId, userId]);

  const startInterview = useCallback(() => {
    clientRef.current?.send("session.start", {});
  }, []);

  const finishAnswer = useCallback(() => {
    clientRef.current?.send("speech.end", {});
    setInterviewerState("processing");
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionState,
    interviewerState,
    transcript,
    currentQuestion,
    currentQuestionSequence,
    errorMessage,
    connect,
    disconnect,
    startInterview,
    finishAnswer,
  };
}
