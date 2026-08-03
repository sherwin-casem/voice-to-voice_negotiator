"use client";

import type { InterviewSessionStatus, SessionResponse } from "@voice/shared";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CountdownTimer } from "@/components/interview/CountdownTimer";
import { ConnectionStatus } from "@/components/interview/ConnectionStatus";
import { CurrentQuestion } from "@/components/interview/CurrentQuestion";
import { InterviewerAvatar } from "@/components/interview/InterviewerAvatar";
import { LiveTranscript } from "@/components/interview/LiveTranscript";
import { MicControls } from "@/components/interview/MicControls";
import { StageStepper } from "@/components/interview/StageStepper";
import { PracticeModeBadge } from "@/components/ui/Badge";
import { Alert, PreviewMetricsBanner, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { MetricBar } from "@/components/ui/MetricBar";
import { useAppContext } from "@/context/AppProvider";
import { useInterviewTimer } from "@/hooks/useInterviewTimer";
import { useLiveMetricsPreview } from "@/hooks/useLiveMetricsPreview";
import { useSession } from "@/hooks/useSession";
import { useVoiceInterview } from "@/hooks/useVoiceInterview";
import { ApiClientError } from "@/lib/api-client";
import { getSession } from "@/lib/interview-api";

export default function LiveInterviewPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const router = useRouter();
  const { userId } = useAppContext();
  const {
    session: loadedSession,
    error: sessionLoadError,
    isLoading,
  } = useSession(userId, sessionId);

  const [sessionPatch, setSessionPatch] = useState<{
    sessionId: string;
    patch: Partial<SessionResponse>;
  } | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isEnding, setIsEnding] = useState(false);

  const session = useMemo(() => {
    if (!loadedSession) {
      return null;
    }
    if (sessionPatch?.sessionId === loadedSession.id) {
      return { ...loadedSession, ...sessionPatch.patch };
    }
    return loadedSession;
  }, [loadedSession, sessionPatch]);

  const loadError = refreshError ?? sessionLoadError;

  const applySessionPatch = useCallback(
    (patch: Partial<SessionResponse>) => {
      if (!loadedSession) {
        return;
      }
      setSessionPatch({ sessionId: loadedSession.id, patch });
    },
    [loadedSession],
  );

  const { metrics } = useLiveMetricsPreview();

  const refreshSession = useCallback(async () => {
    if (!userId || !sessionId) {
      return;
    }
    try {
      const loaded = await getSession(userId, sessionId);
      applySessionPatch({
        status: loaded.status,
        question_count: loaded.question_count,
      });
    } catch (caught) {
      setRefreshError(
        caught instanceof ApiClientError ? caught.message : "Unable to refresh session.",
      );
    }
  }, [applySessionPatch, sessionId, userId]);

  const voice = useVoiceInterview(sessionId, userId, {
    onSessionStatusChange: (status, questionCount) => {
      applySessionPatch({
        status: status as InterviewSessionStatus,
        question_count: questionCount,
      });
    },
    onSessionEnded: () => {
      void refreshSession();
    },
    onTurnComplete: () => {
      void refreshSession();
    },
  });

  const elapsedSeconds = useInterviewTimer(session?.status === "active");
  const targetMinutes =
    session?.config && typeof session.config.target_duration_minutes === "number"
      ? session.config.target_duration_minutes
      : null;

  const notes = useMemo(() => {
    const items: string[] = [];
    const config = session?.config;
    if (config?.target_role) {
      items.push(`Target role: ${config.target_role}`);
    }
    if (config?.difficulty) {
      items.push(`Difficulty: ${config.difficulty}`);
    }
    if (config?.company_context) {
      items.push(`Company: ${config.company_context}`);
    }
    if (items.length === 0) {
      items.push("Review your resume highlights before answering.");
      items.push("Use the STAR method for behavioral questions.");
      items.push("Speak clearly and pause before follow-ups.");
    }
    return items;
  }, [session?.config]);

  useEffect(() => {
    if (userId && sessionId) {
      voice.connect();
    }
  }, [sessionId, userId, voice.connect]);

  async function handleStartInterview() {
    setIsStarting(true);
    setRefreshError(null);
    try {
      await voice.startInterview();
      await refreshSession();
    } catch (caught) {
      setRefreshError(
        caught instanceof Error ? caught.message : "Unable to start voice interview.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function handleEndInterview() {
    setIsEnding(true);
    setRefreshError(null);
    try {
      await voice.endInterview();
      voice.disconnect();
      await refreshSession();
      router.push(`/interviews/${sessionId}/results`);
    } catch (caught) {
      setRefreshError(
        caught instanceof Error ? caught.message : "Unable to end interview gracefully.",
      );
    } finally {
      setIsEnding(false);
    }
  }

  async function handleToggleMic() {
    if (voice.isRecording) {
      voice.pauseAnswer();
      return;
    }
    await voice.beginAnswer();
  }

  const canStartInterview =
    voice.isSessionReady &&
    !voice.isInterviewStarted &&
    (session?.status === "configured" || session?.status === "active");

  const canAnswer =
    voice.isInterviewStarted &&
    voice.connectionState === "connected" &&
    (voice.isAwaitingAnswer || voice.interviewerState === "listening");

  const isEnded =
    session?.status === "completed" ||
    session?.status === "abandoned" ||
    session?.status === "evaluation_failed";

  if (isLoading) {
    return <Spinner label="Loading live interview" />;
  }

  if (loadError && !session) {
    return (
      <Alert variant="error" title="Unable to open interview">
        {loadError}
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header row */}
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
          <h1 className="text-xl font-bold tracking-widest text-[var(--text-primary)] sm:text-2xl">
            MOCK INTERVIEW
          </h1>
          <ConnectionStatus state={voice.connectionState} />
        </div>
        <StageStepper
          interviewType={session?.interview_type}
          isStarted={voice.isInterviewStarted}
          isEnded={isEnded}
          className="order-3 lg:order-none"
        />
        <div className="flex flex-wrap items-center gap-2 lg:justify-end">
          <PracticeModeBadge />
          {canStartInterview ? (
            <Button onClick={handleStartInterview} disabled={isStarting}>
              {isStarting ? "Starting…" : "Start"}
            </Button>
          ) : null}
          {voice.isInterviewStarted ? (
            <Button variant="secondary" onClick={handleEndInterview} disabled={isEnding}>
              {isEnding ? "Ending…" : "End interview"}
            </Button>
          ) : null}
        </div>
      </header>

      {(loadError || voice.errorMessage || voice.permissionDenied) && (
        <div className="space-y-2">
          {loadError ? <Alert variant="error">{loadError}</Alert> : null}
          {voice.errorMessage ? (
            <Alert variant="warning" title="Connection issue">
              {voice.errorMessage}
            </Alert>
          ) : null}
          {voice.permissionDenied ? (
            <Alert variant="warning" title="Microphone blocked">
              Allow microphone access in your browser settings to answer by voice.
            </Alert>
          ) : null}
        </div>
      )}

      {/* 3-column layout */}
      <div className="grid gap-4 lg:grid-cols-12 lg:gap-6">
        {/* Notes */}
        <aside className="lg:col-span-3">
          <GlassPanel className="h-full p-5">
            <h2 className="text-section-label mb-4">Notes</h2>
            <ul className="space-y-2 text-sm text-[var(--text-muted)]">
              {notes.map((note) => (
                <li key={note} className="flex gap-2">
                  <span className="text-teal-500" aria-hidden="true">
                    •
                  </span>
                  {note}
                </li>
              ))}
            </ul>
          </GlassPanel>
        </aside>

        {/* Center: avatar + question + controls */}
        <section className="space-y-4 lg:col-span-6">
          <InterviewerAvatar
            state={voice.interviewerState}
            audioLevel={voice.audioLevel}
            isRecording={voice.isRecording}
            questionSequence={voice.currentQuestionSequence}
          />
          <CurrentQuestion
            question={voice.currentQuestion}
            sequenceNum={voice.currentQuestionSequence}
          />
          <MicControls
            isEnabled={voice.isMicEnabled}
            isRecording={voice.isRecording}
            permissionDenied={voice.permissionDenied}
            canAnswer={canAnswer}
            onToggleMic={handleToggleMic}
            onFinishAnswer={voice.finishAnswer}
            disabled={!voice.isInterviewStarted}
            compact
          />
        </section>

        {/* Metrics + timer */}
        <aside className="space-y-4 lg:col-span-3">
          <GlassPanel className="p-5">
            <h2 className="text-section-label mb-4">Real-Time Metrics</h2>
            <div className="space-y-4">
              <MetricBar
                label={metrics.confidence.label}
                value={metrics.confidence.value}
                percent={metrics.confidence.percent}
              />
              <MetricBar
                label={metrics.speakingPace.label}
                value={metrics.speakingPace.value}
                percent={metrics.speakingPace.percent}
                variant="success"
              />
              <MetricBar
                label={metrics.fillerWords.label}
                value={metrics.fillerWords.value}
                percent={metrics.fillerWords.percent}
                variant="success"
              />
              <MetricBar
                label={metrics.clarity.label}
                value={metrics.clarity.value}
                percent={metrics.clarity.percent}
              />
            </div>
            <div className="mt-4">
              <PreviewMetricsBanner />
            </div>
          </GlassPanel>

          <GlassPanel className="p-5">
            <CountdownTimer elapsedSeconds={elapsedSeconds} targetMinutes={targetMinutes} />
          </GlassPanel>
        </aside>
      </div>

      <LiveTranscript entries={voice.transcript} />
    </div>
  );
}
