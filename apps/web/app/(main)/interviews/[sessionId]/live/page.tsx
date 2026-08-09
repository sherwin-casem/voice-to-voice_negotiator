"use client";

import type { InterviewSessionStatus, SessionResponse } from "@voice/shared";
import { getInterviewerRole, INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CountdownTimer } from "@/components/interview/CountdownTimer";
import { ConnectionStatus } from "@/components/interview/ConnectionStatus";
import { CurrentQuestion } from "@/components/interview/CurrentQuestion";
import { InterviewFunnelStepper } from "@/components/interview/InterviewFunnelStepper";
import { InterviewerAvatar } from "@/components/interview/InterviewerAvatar";
import { LiveTranscript } from "@/components/interview/LiveTranscript";
import { MicControls } from "@/components/interview/MicControls";
import { SessionNotesPanel } from "@/components/interview/SessionNotesPanel";
import { PracticeModeBadge } from "@/components/ui/Badge";
import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { useAppContext } from "@/context/AppProvider";
import { useInterviewTimer } from "@/hooks/useInterviewTimer";
import { useSession } from "@/hooks/useSession";
import { useVoiceInterview } from "@/hooks/useVoiceInterview";
import { ApiClientError } from "@/lib/api-client";
import { endSession, getSession } from "@/lib/interview-api";

function ConnectionTipsPanel() {
  return (
    <GlassPanel className="p-4 lg:hidden">
      <h2 className="text-section-label mb-3">Before you start</h2>
      <ul className="grid gap-2 text-sm text-[var(--text-muted)] sm:grid-cols-2">
        <li>Use headphones to reduce echo.</li>
        <li>Allow microphone access when prompted.</li>
        <li>Find a quiet space with stable internet.</li>
        <li>Tap Start answer to record your response.</li>
      </ul>
    </GlassPanel>
  );
}

function isStartableSessionStatus(status: string | null | undefined): boolean {
  return status === "configured" || status === "active";
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
      setSessionPatch((previous) => {
        const sessionKey = loadedSession?.id ?? previous?.sessionId ?? sessionId;
        if (!sessionKey) {
          return previous;
        }
        const mergedPatch = {
          ...(previous?.sessionId === sessionKey ? previous.patch : {}),
          ...patch,
        };
        return { sessionId: sessionKey, patch: mergedPatch };
      });
    },
    [loadedSession, sessionId],
  );

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
      if (status === "unknown") {
        return;
      }
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
    } catch {
      try {
        await endSession(sessionId);
        await refreshSession();
        router.push(`/interviews/${sessionId}/results`);
      } catch (restError) {
        setRefreshError(
          restError instanceof Error
            ? restError.message
            : "Unable to end interview gracefully.",
        );
      }
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

  const interviewNotStarted = !voice.isInterviewStarted;
  const effectiveSessionStatus =
    voice.voiceSessionStatus ?? session?.status ?? null;
  const sessionAllowsStart = isStartableSessionStatus(effectiveSessionStatus);
  const canStartInterview =
    voice.isSessionReady && interviewNotStarted && sessionAllowsStart;
  const isSessionFinished =
    effectiveSessionStatus === "completed" ||
    effectiveSessionStatus === "abandoned" ||
    effectiveSessionStatus === "evaluation_failed";
  const showStartInterview =
    interviewNotStarted &&
    session?.status !== "completing" &&
    !isSessionFinished;

  useEffect(() => {
    if (isLoading || !session || !voice.isSessionReady) {
      return;
    }
    if (effectiveSessionStatus === "created") {
      router.replace(`/interviews/${sessionId}/setup`);
    }
  }, [
    effectiveSessionStatus,
    isLoading,
    router,
    session,
    sessionId,
    voice.isSessionReady,
  ]);

  const startButtonLabel = isStarting
    ? "Starting…"
    : !voice.isSessionReady
      ? "Connecting…"
      : !sessionAllowsStart
        ? effectiveSessionStatus === "created"
          ? "Complete setup"
          : "Cannot start"
        : "Start interview";

  const startHelperText = !voice.isSessionReady
    ? "Connecting to the interviewer…"
    : !sessionAllowsStart
      ? effectiveSessionStatus === "created"
        ? "Finish setup before starting the live interview."
        : "This session cannot be started in its current state."
      : "Start the interview to begin the first question.";

  const canAnswer =
    voice.isInterviewStarted &&
    voice.connectionState === "connected" &&
    (voice.answerPhase === "ready" ||
      voice.answerPhase === "recording" ||
      voice.answerPhase === "paused" ||
      (voice.answerPhase === "locked" && voice.interviewerState === "speaking"));

  const startInterviewButton = showStartInterview ? (
    <Button
      onClick={handleStartInterview}
      disabled={!canStartInterview || isStarting}
      className="min-w-[11rem] px-6 py-2.5 text-sm shadow-[0_0_28px_rgba(20,184,166,0.35)]"
    >
      {startButtonLabel}
    </Button>
  ) : null;

  const micControls = voice.isInterviewStarted ? (
    <MicControls
      isEnabled={voice.isMicEnabled}
      isRecording={voice.isRecording}
      permissionDenied={voice.permissionDenied}
      canAnswer={canAnswer}
      onToggleMic={handleToggleMic}
      onFinishAnswer={voice.finishAnswer}
      disabled={false}
      compact
      embedded
    />
  ) : (
    <div className="flex flex-col items-center gap-2 py-1">
      {startInterviewButton}
      <p className="text-center text-xs text-slate-400">
        {startHelperText}
        {effectiveSessionStatus === "created" && voice.isSessionReady ? (
          <>
            {" "}
            <Link
              href={`/interviews/${sessionId}/setup`}
              className="font-medium text-teal-400 underline-offset-2 hover:text-teal-300 hover:underline"
            >
              Go to setup
            </Link>
          </>
        ) : null}
      </p>
    </div>
  );

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
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-x-hidden pb-28 lg:gap-4 lg:pb-0">
      <header className="flex shrink-0 flex-col gap-2.5 lg:flex-row lg:items-center lg:justify-between lg:gap-3">
        <div className="flex min-w-0 flex-wrap items-center gap-3 sm:gap-4">
          <h1 className="text-lg font-bold tracking-[0.18em] text-[var(--text-primary)] sm:text-xl">
            MOCK INTERVIEW
          </h1>
          <ConnectionStatus state={voice.connectionState} />
        </div>
        <InterviewFunnelStepper
          current="live"
          sessionId={sessionId}
          className="order-3 min-w-0 opacity-80 lg:order-none lg:justify-center"
        />
        <div className="flex min-w-0 flex-wrap items-center gap-2 lg:justify-end">
          <PracticeModeBadge />
          <div className="hidden lg:contents">
            {showStartInterview ? (
              <Button
                onClick={handleStartInterview}
                disabled={!canStartInterview || isStarting}
              >
                {startButtonLabel}
              </Button>
            ) : null}
          </div>
          {voice.isInterviewStarted ? (
            <Button variant="secondary" onClick={handleEndInterview} disabled={isEnding}>
              {isEnding ? "Ending…" : "End interview"}
            </Button>
          ) : null}
        </div>
      </header>

      {(loadError || voice.errorMessage || voice.permissionDenied) && (
        <div className="shrink-0 space-y-2">
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

      {/* Stage-first layout: center dominates; constrained so the page stays in-viewport */}
      <div className="grid min-h-0 min-w-0 flex-1 items-stretch gap-3 lg:grid-cols-[220px_minmax(0,1fr)_200px] lg:gap-4 xl:grid-cols-[240px_minmax(0,1fr)_220px]">
        <aside className="order-2 hidden min-h-0 min-w-0 lg:order-none lg:block">
          <SessionNotesPanel notes={notes} />
        </aside>

        <section className="order-1 flex min-h-0 min-w-0 flex-col gap-3 lg:order-none">
          <InterviewerAvatar
            state={voice.interviewerState}
            audioLevel={voice.audioLevel}
            isRecording={voice.isRecording}
            questionSequence={voice.currentQuestionSequence}
            interviewType={session?.interview_type}
            footer={<div className="hidden lg:block">{micControls}</div>}
          />
          <CurrentQuestion
            question={voice.currentQuestion}
            sequenceNum={voice.currentQuestionSequence}
          />
        </section>

        <aside className="order-3 min-w-0 space-y-3 lg:order-none lg:space-y-4">
          <GlassPanel className="p-4 sm:p-5">
            <CountdownTimer
              elapsedSeconds={elapsedSeconds}
              targetMinutes={targetMinutes}
              running={isTimerRunning}
            />
          </GlassPanel>
          <div className="lg:hidden">
            <SessionNotesPanel notes={notes} />
          </div>
        </aside>
      </div>

      <div className="shrink-0">
        <LiveTranscript entries={voice.transcript} />
      </div>

      <div className="fixed inset-x-0 bottom-0 z-50 border-t border-[var(--border-glass)] bg-[var(--bg-deep)]/95 p-3 backdrop-blur-xl lg:hidden">
        <div className="mx-auto flex max-w-lg flex-col gap-2.5">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <PracticeModeBadge />
            {voice.isInterviewStarted ? (
              <Button
                variant="secondary"
                onClick={handleEndInterview}
                disabled={isEnding}
                className="px-4 py-2 text-sm"
              >
                {isEnding ? "Ending…" : "End"}
              </Button>
            ) : null}
          </div>
          {micControls}
        </div>
      </div>
    </div>
  );
}
