"use client";

import type { InterviewSessionStatus, SessionResponse } from "@voice/shared";
import { getInterviewerRole, INTERVIEW_TYPE_LABELS } from "@voice/shared";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CountdownTimer } from "@/components/interview/CountdownTimer";
import { ConnectionStatus } from "@/components/interview/ConnectionStatus";
import { CurrentQuestion } from "@/components/interview/CurrentQuestion";
import { InterviewFunnelStepper } from "@/components/interview/InterviewFunnelStepper";
import { InterviewerAvatar } from "@/components/interview/InterviewerAvatar";
import { LiveTranscript } from "@/components/interview/LiveTranscript";
import { MicControls } from "@/components/interview/MicControls";
import { PracticeModeBadge } from "@/components/ui/Badge";
import { Alert, Spinner } from "@/components/ui/Alert";
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

function ConnectionTipsPanel() {
  return (
    <GlassPanel className="p-5 lg:hidden">
      <h2 className="text-section-label mb-4">Before you start</h2>
      <ul className="space-y-2 text-sm text-[var(--text-muted)]">
        <li>Use headphones to reduce echo.</li>
        <li>Allow microphone access when prompted.</li>
        <li>Find a quiet space with stable internet.</li>
        <li>Tap the mic button to record your answer.</li>
      </ul>
    </GlassPanel>
  );
}

function DemoMetricsPanel({
  metrics,
}: {
  metrics: ReturnType<typeof useLiveMetricsPreview>["metrics"];
}) {
  return (
    <GlassPanel className="hidden p-5 lg:block">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h2 className="text-section-label">Demo metrics</h2>
        <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-200">
          Preview
        </span>
      </div>
      <p className="mb-4 text-xs text-[var(--text-dim)]">
        Live evaluation metrics update during your session as you speak.
      </p>
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
    </GlassPanel>
  );
}

export default function LiveInterviewPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const router = useRouter();
  const { accessToken } = useAppContext();
  const {
    session: loadedSession,
    error: sessionLoadError,
    isLoading,
  } = useSession(sessionId);

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
    if (!sessionId) {
      return;
    }
    try {
      const loaded = await getSession(sessionId);
      applySessionPatch({
        status: loaded.status,
        question_count: loaded.question_count,
      });
      return loaded.status;
    } catch (caught) {
      setRefreshError(
        caught instanceof ApiClientError ? caught.message : "Unable to refresh session.",
      );
      return null;
    }
  }, [applySessionPatch, sessionId]);

  const refreshSessionUntilActive = useCallback(async () => {
    for (let attempt = 0; attempt < 8; attempt += 1) {
      const status = await refreshSession();
      if (status === "active" || status === "completing") {
        return;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    }
  }, [refreshSession]);

  const voice = useVoiceInterview(sessionId, accessToken ?? "", {
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

  const isSessionTerminal =
    session?.status === "completed" ||
    session?.status === "abandoned" ||
    session?.status === "evaluation_failed";

  const isTimerRunning =
    !isSessionTerminal &&
    (voice.isInterviewStarted ||
      session?.status === "active" ||
      session?.status === "completing");

  const elapsedSeconds = useInterviewTimer(isTimerRunning);
  const targetMinutes =
    session?.config && typeof session.config.target_duration_minutes === "number"
      ? session.config.target_duration_minutes
      : null;

  const notes = useMemo(() => {
    const items: string[] = [];
    const config = session?.config;
    if (session?.interview_type) {
      items.push(
        `Interviewer: ${getInterviewerRole(session.interview_type)} (${INTERVIEW_TYPE_LABELS[session.interview_type]})`,
      );
    }
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
  }, [session?.config, session?.interview_type]);

  useEffect(() => {
    if (accessToken && sessionId) {
      voice.connect();
    }
  }, [sessionId, accessToken, voice.connect]);

  async function handleStartInterview() {
    setIsStarting(true);
    setRefreshError(null);
    try {
      await voice.startInterview();
      applySessionPatch({ status: "active" });
      void refreshSessionUntilActive();
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
    <div className="space-y-3 pb-24 lg:pb-4">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
          <h1 className="text-xl font-bold tracking-widest text-[var(--text-primary)] sm:text-2xl">
            MOCK INTERVIEW
          </h1>
          <ConnectionStatus state={voice.connectionState} />
        </div>
        <InterviewFunnelStepper
          current="live"
          sessionId={sessionId}
          className="order-3 lg:order-none"
        />
        <div className="hidden flex-wrap items-center gap-2 lg:flex lg:justify-end">
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

      <ConnectionTipsPanel />

      <div className="grid gap-4 lg:grid-cols-12 lg:items-start lg:gap-6">
        <aside className="order-2 lg:order-none lg:col-span-3">
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

        <section className="order-1 space-y-4 lg:order-none lg:col-span-6">
          <InterviewerAvatar
            state={voice.interviewerState}
            audioLevel={voice.audioLevel}
            isRecording={voice.isRecording}
            questionSequence={voice.currentQuestionSequence}
            interviewType={session?.interview_type}
          />
          <CurrentQuestion
            question={voice.currentQuestion}
            sequenceNum={voice.currentQuestionSequence}
          />
          <div className="hidden lg:block">
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
          </div>
        </section>

        <aside className="order-3 space-y-4 lg:col-span-3">
          <DemoMetricsPanel metrics={metrics} />

          <GlassPanel className="p-5">
            <CountdownTimer elapsedSeconds={elapsedSeconds} targetMinutes={targetMinutes} />
          </GlassPanel>
        </aside>
      </div>

      <div className="lg:max-h-48 lg:overflow-y-auto">
        <LiveTranscript entries={voice.transcript} />
      </div>

      <div className="fixed inset-x-0 bottom-0 z-50 border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/95 p-4 backdrop-blur-xl lg:hidden">
        <div className="mx-auto flex max-w-lg flex-col gap-3">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <PracticeModeBadge />
            {canStartInterview ? (
              <Button onClick={handleStartInterview} disabled={isStarting}>
                {isStarting ? "Starting…" : "Start"}
              </Button>
            ) : null}
            {voice.isInterviewStarted ? (
              <Button variant="secondary" onClick={handleEndInterview} disabled={isEnding}>
                {isEnding ? "Ending…" : "End"}
              </Button>
            ) : null}
          </div>
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
        </div>
      </div>
    </div>
  );
}
