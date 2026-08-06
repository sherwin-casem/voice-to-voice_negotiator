"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { InterviewWebSocket } from "@/lib/ws-client";
import { PcmCapture } from "@/lib/voice/pcm-capture";
import { PcmStreamPlayer } from "@/lib/voice/pcm-player";
import {
  VOICE_CHANNELS,
  VOICE_ENCODING,
  VOICE_SAMPLE_RATE,
  WS_EVENTS,
} from "@/lib/voice/constants";
import type {
  InterviewerState,
  ServerWsEnvelope,
  TranscriptEntry,
  WsConnectionState,
} from "@/types/websocket";

function nextEntryId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export interface VoiceInterviewOptions {
  onSessionStatusChange?: (status: string, questionCount: number) => void;
  onSessionEnded?: (status: string, reason: string) => void;
  onTurnComplete?: () => void;
}

export interface VoiceInterviewState {
  connectionState: WsConnectionState;
  interviewerState: InterviewerState;
  transcript: TranscriptEntry[];
  currentQuestion: string | null;
  currentQuestionSequence: number | null;
  errorMessage: string | null;
  isSessionReady: boolean;
  isInterviewStarted: boolean;
  isRecording: boolean;
  isMicEnabled: boolean;
  permissionDenied: boolean;
  audioLevel: number;
  isAwaitingAnswer: boolean;
  connect: () => void;
  disconnect: () => void;
  startInterview: () => Promise<void>;
  beginAnswer: () => Promise<void>;
  pauseAnswer: () => void;
  finishAnswer: () => void;
  endInterview: () => Promise<void>;
}

export function useVoiceInterview(
  sessionId: string,
  accessToken: string,
  options: VoiceInterviewOptions = {},
): VoiceInterviewState {
  const [connectionState, setConnectionState] = useState<WsConnectionState>("idle");
  const [interviewerState, setInterviewerState] = useState<InterviewerState>("idle");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [currentQuestionSequence, setCurrentQuestionSequence] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSessionReady, setIsSessionReady] = useState(false);
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isMicEnabled, setIsMicEnabled] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isAwaitingAnswer, setIsAwaitingAnswer] = useState(false);

  const clientRef = useRef<InterviewWebSocket | null>(null);
  const captureRef = useRef<PcmCapture | null>(null);
  const playerRef = useRef<PcmStreamPlayer | null>(null);
  const audioSeqRef = useRef(0);
  const questionCountRef = useRef(0);
  const partialCandidateIdRef = useRef<string | null>(null);
  const endInterviewResolveRef = useRef<(() => void) | null>(null);
  const endInterviewRejectRef = useRef<((reason: Error) => void) | null>(null);
  const allowReconnectRef = useRef(true);
  const isInterviewStartedRef = useRef(false);
  const optionsRef = useRef(options);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const appendSystemMessage = useCallback((text: string) => {
    setTranscript((previous) => [
      ...previous,
      {
        id: nextEntryId("system"),
        speaker: "system",
        text,
        timestamp: Date.now(),
      },
    ]);
  }, []);

  const setCandidatePartial = useCallback((text: string) => {
    if (!text.trim()) {
      return;
    }
    setTranscript((previous) => {
      if (partialCandidateIdRef.current) {
        return previous.map((entry) =>
          entry.id === partialCandidateIdRef.current
            ? { ...entry, text, isPartial: true, timestamp: Date.now() }
            : entry,
        );
      }
      const id = nextEntryId("candidate");
      partialCandidateIdRef.current = id;
      return [
        ...previous,
        {
          id,
          speaker: "candidate",
          text,
          isPartial: true,
          timestamp: Date.now(),
        },
      ];
    });
  }, []);

  const setCandidateFinal = useCallback((text: string) => {
    if (!text.trim()) {
      return;
    }
    setTranscript((previous) => {
      const partialId = partialCandidateIdRef.current;
      if (partialId) {
        partialCandidateIdRef.current = null;
        return previous.map((entry) =>
          entry.id === partialId
            ? { ...entry, text, isPartial: false, timestamp: Date.now() }
            : entry,
        );
      }
      return [
        ...previous,
        {
          id: nextEntryId("candidate"),
          speaker: "candidate",
          text,
          isPartial: false,
          timestamp: Date.now(),
        },
      ];
    });
  }, []);

  const appendInterviewerMessage = useCallback((text: string) => {
    if (!text.trim()) {
      return;
    }
    setTranscript((previous) => [
      ...previous,
      {
        id: nextEntryId("interviewer"),
        speaker: "interviewer",
        text,
        isPartial: false,
        timestamp: Date.now(),
      },
    ]);
  }, []);

  const handleEnvelope = useCallback(
    (envelope: ServerWsEnvelope) => {
      const { type, payload } = envelope;

      switch (type) {
        case WS_EVENTS.server.sessionReady: {
          setConnectionState("connected");
          setIsSessionReady(true);
          questionCountRef.current = Number(payload.question_count ?? 0);
          optionsRef.current.onSessionStatusChange?.(
            String(payload.status ?? "unknown"),
            questionCountRef.current,
          );
          appendSystemMessage("Voice session connected.");
          break;
        }
        case WS_EVENTS.server.interviewerResponse: {
          const text = String(payload.text ?? "");
          questionCountRef.current += 1;
          setCurrentQuestion(text);
          setCurrentQuestionSequence(questionCountRef.current);
          appendInterviewerMessage(text);
          setInterviewerState("speaking");
          setIsInterviewStarted(true);
          isInterviewStartedRef.current = true;
          setIsAwaitingAnswer(false);
          break;
        }
        case WS_EVENTS.server.audioOutput: {
          const player = playerRef.current ?? new PcmStreamPlayer();
          playerRef.current = player;
          void player.resume().then(() => {
            player.enqueueBase64Chunk(
              String(payload.data ?? ""),
              Number(payload.sample_rate ?? VOICE_SAMPLE_RATE),
            );
            if (payload.is_final === true) {
              setInterviewerState("idle");
              setIsAwaitingAnswer(true);
            } else {
              setInterviewerState("speaking");
            }
          });
          break;
        }
        case WS_EVENTS.server.transcriptPartial:
          setInterviewerState("processing");
          setCandidatePartial(String(payload.text ?? ""));
          break;
        case WS_EVENTS.server.transcriptFinal:
          setCandidateFinal(String(payload.text ?? ""));
          setInterviewerState("thinking");
          setIsAwaitingAnswer(false);
          optionsRef.current.onTurnComplete?.();
          break;
        case WS_EVENTS.server.interviewerThinking:
          setInterviewerState("thinking");
          break;
        case WS_EVENTS.server.sessionError: {
          const recoverable = payload.recoverable !== false;
          setErrorMessage(String(payload.message ?? "Unknown session error"));
          setConnectionState(recoverable ? "connected" : "error");
          if (!recoverable) {
            allowReconnectRef.current = false;
          }
          break;
        }
        case WS_EVENTS.server.sessionEnd: {
          allowReconnectRef.current = false;
          appendSystemMessage(`Session ended (${String(payload.reason ?? "ended")}).`);
          optionsRef.current.onSessionEnded?.(
            String(payload.status ?? "completed"),
            String(payload.reason ?? "ended"),
          );
          endInterviewResolveRef.current?.();
          endInterviewResolveRef.current = null;
          endInterviewRejectRef.current = null;
          setInterviewerState("idle");
          setIsAwaitingAnswer(false);
          setIsInterviewStarted(false);
          isInterviewStartedRef.current = false;
          clientRef.current?.disconnect();
          break;
        }
        default:
          break;
      }
    },
    [appendInterviewerMessage, appendSystemMessage, setCandidateFinal, setCandidatePartial],
  );

  const stopCapture = useCallback(() => {
    captureRef.current?.stopStreaming();
    captureRef.current?.stop();
    captureRef.current = null;
    setIsRecording(false);
    setIsMicEnabled(false);
    setAudioLevel(0);
  }, []);

  const disconnect = useCallback(() => {
    allowReconnectRef.current = false;
    clientRef.current?.disconnect();
    clientRef.current = null;
    stopCapture();
    playerRef.current?.dispose();
    playerRef.current = null;
    setConnectionState("disconnected");
  }, [stopCapture]);

  const connect = useCallback(() => {
    if (!sessionId || !accessToken) {
      return;
    }

    allowReconnectRef.current = true;
    clientRef.current?.disconnect();
    setConnectionState("connecting");
    setErrorMessage(null);
    setIsSessionReady(false);

    const client = new InterviewWebSocket(sessionId, accessToken);
    clientRef.current = client;
    client.connect(
      handleEnvelope,
      (connected, reconnecting) => {
        if (connected) {
          setConnectionState("connected");
          return;
        }
        if (reconnecting && allowReconnectRef.current) {
          setConnectionState("reconnecting");
          return;
        }
        if (!connected && !reconnecting && isInterviewStartedRef.current) {
          allowReconnectRef.current = false;
          setErrorMessage(
            "Connection lost. The backend may have marked this session as abandoned.",
          );
        }
        if (!allowReconnectRef.current) {
          setConnectionState("disconnected");
          return;
        }
        setConnectionState("disconnected");
      },
    );
  }, [handleEnvelope, sessionId, accessToken]);

  const startInterview = useCallback(async () => {
    if (!clientRef.current?.isOpen) {
      throw new Error("Voice connection is not ready.");
    }

    playerRef.current?.resume();
    const sent = clientRef.current.send(WS_EVENTS.client.sessionStart, {
      session_id: sessionId,
      audio_format: {
        sample_rate: VOICE_SAMPLE_RATE,
        encoding: VOICE_ENCODING,
        channels: VOICE_CHANNELS,
      },
    });

    if (!sent) {
      throw new Error("Unable to send session.start.");
    }

    setIsInterviewStarted(true);
    isInterviewStartedRef.current = true;
    optionsRef.current.onSessionStatusChange?.("active", questionCountRef.current);
    appendSystemMessage("Interview started.");
  }, [appendSystemMessage, sessionId]);

  const beginAnswer = useCallback(async () => {
    if (
      !isAwaitingAnswer &&
      (interviewerState === "speaking" ||
        interviewerState === "thinking" ||
        interviewerState === "processing")
    ) {
      setErrorMessage("Wait for the interviewer to finish before answering.");
      return;
    }

    try {
      const capture = captureRef.current ?? new PcmCapture();
      captureRef.current = capture;
      capture.onLevel(setAudioLevel);
      capture.onChunk(({ dataBase64, timestampMs }) => {
        clientRef.current?.send(WS_EVENTS.client.audioInput, {
          seq: audioSeqRef.current,
          data: dataBase64,
          timestamp_ms: timestampMs,
          is_final_chunk: false,
        });
        audioSeqRef.current += 1;
      });

      await capture.start();
      audioSeqRef.current = 0;
      capture.beginStreaming();
      setPermissionDenied(false);
      setIsMicEnabled(true);
      setIsRecording(true);
      setInterviewerState("listening");
      setErrorMessage(null);
    } catch {
      setPermissionDenied(true);
      setIsMicEnabled(false);
      setIsRecording(false);
      setErrorMessage("Microphone permission is required to answer by voice.");
    }
  }, [interviewerState, isAwaitingAnswer]);

  const finishAnswer = useCallback(() => {
    captureRef.current?.stopStreaming();
    setIsRecording(false);
    setInterviewerState("processing");

    clientRef.current?.send(WS_EVENTS.client.speechEnd, {
      timestamp_ms: Date.now(),
    });
  }, []);

  const pauseAnswer = useCallback(() => {
    captureRef.current?.stopStreaming();
    setIsRecording(false);
    if (isAwaitingAnswer) {
      setInterviewerState("idle");
    }
  }, [isAwaitingAnswer]);

  const endInterview = useCallback(async () => {
    return new Promise<void>((resolve, reject) => {
      endInterviewResolveRef.current = resolve;
      endInterviewRejectRef.current = reject;

      const sent = clientRef.current?.send(WS_EVENTS.client.sessionEnd, {
        reason: "user_ended",
      });

      if (!sent) {
        endInterviewResolveRef.current = null;
        endInterviewRejectRef.current = null;
        reject(new Error("Voice connection is not open."));
        return;
      }

      window.setTimeout(() => {
        if (endInterviewRejectRef.current) {
          endInterviewRejectRef.current(new Error("Timed out waiting for session.end"));
          endInterviewResolveRef.current = null;
          endInterviewRejectRef.current = null;
        }
      }, 10000);
    });
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
    isSessionReady,
    isInterviewStarted,
    isRecording,
    isMicEnabled,
    permissionDenied,
    audioLevel,
    isAwaitingAnswer,
    connect,
    disconnect,
    startInterview,
    beginAnswer,
    pauseAnswer,
    finishAnswer,
    endInterview,
  };
}
