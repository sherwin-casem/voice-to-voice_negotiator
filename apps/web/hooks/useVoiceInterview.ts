"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchWsTicket } from "@/lib/auth-api";
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

/**
 * Explicit answer lifecycle so the mic can never be armed while a previous
 * answer is still being processed or the interviewer is still audible.
 *
 * locked -> ready (interviewer audio finished playing)
 * ready -> recording (user starts mic)
 * recording <-> paused (user pauses/resumes within one answer)
 * recording | paused -> submitted (user finishes the answer)
 * submitted -> locked (next question arrives)
 */
export type AnswerPhase = "locked" | "ready" | "recording" | "paused" | "submitted";

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
  answerPhase: AnswerPhase;
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
  const [answerPhase, setAnswerPhase] = useState<AnswerPhase>("locked");

  const clientRef = useRef<InterviewWebSocket | null>(null);
  const captureRef = useRef<PcmCapture | null>(null);
  const playerRef = useRef<PcmStreamPlayer | null>(null);
  const playbackChainRef = useRef<Promise<void>>(Promise.resolve());
  const isPlaybackActiveRef = useRef(false);
  // After a barge-in, drop the remaining audio chunks of the cancelled
  // utterance until the next interviewer response begins.
  const dropAudioOutputRef = useRef(false);
  const answerPhaseRef = useRef<AnswerPhase>("locked");
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

  const transitionAnswerPhase = useCallback((phase: AnswerPhase) => {
    answerPhaseRef.current = phase;
    setAnswerPhase(phase);
  }, []);

  const handlePlaybackDrained = useCallback(() => {
    isPlaybackActiveRef.current = false;
    setInterviewerState("idle");
    setIsAwaitingAnswer(true);
    transitionAnswerPhase("ready");
  }, [transitionAnswerPhase]);

  const ensurePlayer = useCallback(() => {
    if (!playerRef.current) {
      const player = new PcmStreamPlayer();
      player.onDrained(handlePlaybackDrained);
      playerRef.current = player;
    }
    return playerRef.current;
  }, [handlePlaybackDrained]);

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
          if (isInterviewStartedRef.current) {
            // Reconnected mid-interview: re-send session.start so the server
            // resumes by re-delivering the open question.
            clientRef.current?.send(WS_EVENTS.client.sessionStart, {
              session_id: sessionId,
              audio_format: {
                sample_rate: VOICE_SAMPLE_RATE,
                encoding: VOICE_ENCODING,
                channels: VOICE_CHANNELS,
              },
            });
          }
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
          transitionAnswerPhase("locked");
          dropAudioOutputRef.current = false;
          // New question, new turn: audio seq restarts on the server side too.
          audioSeqRef.current = 0;
          break;
        }
        case WS_EVENTS.server.audioOutput: {
          if (dropAudioOutputRef.current) {
            break;
          }
          const player = ensurePlayer();
          const data = String(payload.data ?? "");
          const sampleRate = Number(payload.sample_rate ?? VOICE_SAMPLE_RATE);
          const isFinal = payload.is_final === true;
          isPlaybackActiveRef.current = true;
          // Chain chunk handling so out-of-order resume() resolutions cannot
          // reorder playback or flip the speaking state after the final chunk.
          playbackChainRef.current = playbackChainRef.current
            .then(async () => {
              await player.resume();
              if (data.length > 0) {
                player.enqueueBase64Chunk(data, sampleRate);
              }
              if (isFinal) {
                // The answer unlocks when playback drains, not on receipt.
                player.markFinalChunkReceived();
              } else {
                setInterviewerState("speaking");
              }
            })
            .catch(() => {
              // Playback failures should not break the message loop.
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
        case WS_EVENTS.server.sessionEnded: {
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
          transitionAnswerPhase("locked");
          setIsInterviewStarted(false);
          isInterviewStartedRef.current = false;
          clientRef.current?.disconnect();
          break;
        }
        default:
          break;
      }
    },
    [
      appendInterviewerMessage,
      appendSystemMessage,
      ensurePlayer,
      sessionId,
      setCandidateFinal,
      setCandidatePartial,
      transitionAnswerPhase,
    ],
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
    playbackChainRef.current = Promise.resolve();
    isPlaybackActiveRef.current = false;
    dropAudioOutputRef.current = false;
    transitionAnswerPhase("locked");
    setConnectionState("disconnected");
  }, [stopCapture, transitionAnswerPhase]);

  const connect = useCallback(() => {
    if (!sessionId || !accessToken) {
      return;
    }

    allowReconnectRef.current = true;
    clientRef.current?.disconnect();
    setConnectionState("connecting");
    setErrorMessage(null);
    setIsSessionReady(false);

    const client = new InterviewWebSocket(sessionId, () => fetchWsTicket(sessionId));
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
    const phase = answerPhaseRef.current;
    const canBargeIn = phase === "locked" && isPlaybackActiveRef.current;
    if (phase !== "ready" && phase !== "paused" && !canBargeIn) {
      setErrorMessage(
        phase === "submitted"
          ? "Your answer is being processed. Wait for the next question."
          : "Wait for the interviewer to finish before answering.",
      );
      return;
    }

    if (canBargeIn) {
      // Barge-in: stop interviewer playback locally and tell the server to
      // cancel the rest of the TTS stream for this turn.
      dropAudioOutputRef.current = true;
      isPlaybackActiveRef.current = false;
      playerRef.current?.stop();
      playbackChainRef.current = Promise.resolve();
      clientRef.current?.send(WS_EVENTS.client.outputCancel, {});
      setInterviewerState("listening");
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
        });
        audioSeqRef.current += 1;
      });

      // Note: audio seq is NOT reset here. Pausing and resuming stays within
      // one server-side turn buffer, which requires a monotonic sequence.
      await capture.start();
      capture.beginStreaming();
      setPermissionDenied(false);
      setIsMicEnabled(true);
      setIsRecording(true);
      setInterviewerState("listening");
      setErrorMessage(null);
      transitionAnswerPhase("recording");
    } catch {
      setPermissionDenied(true);
      setIsMicEnabled(false);
      setIsRecording(false);
      setErrorMessage("Microphone permission is required to answer by voice.");
    }
  }, [transitionAnswerPhase]);

  const finishAnswer = useCallback(() => {
    const phase = answerPhaseRef.current;
    if (phase !== "recording" && phase !== "paused") {
      return;
    }

    captureRef.current?.stopStreaming();
    setIsRecording(false);
    setInterviewerState("processing");
    // Lock the mic until the next question's audio has finished playing.
    setIsAwaitingAnswer(false);
    transitionAnswerPhase("submitted");

    clientRef.current?.send(WS_EVENTS.client.speechEnd, {
      timestamp_ms: Date.now(),
    });
  }, [transitionAnswerPhase]);

  const pauseAnswer = useCallback(() => {
    if (answerPhaseRef.current !== "recording") {
      return;
    }
    captureRef.current?.stopStreaming();
    setIsRecording(false);
    setInterviewerState("idle");
    transitionAnswerPhase("paused");
  }, [transitionAnswerPhase]);

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
          const reject = endInterviewRejectRef.current;
          endInterviewResolveRef.current = null;
          endInterviewRejectRef.current = null;
          // Don't leave a half-open connection behind on timeout; the caller
          // can still end the session over REST.
          disconnect();
          reject(new Error("Timed out waiting for the session to end."));
        }
      }, 10000);
    });
  }, [disconnect]);

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
    answerPhase,
    connect,
    disconnect,
    startInterview,
    beginAnswer,
    pauseAnswer,
    finishAnswer,
    endInterview,
  };
}
