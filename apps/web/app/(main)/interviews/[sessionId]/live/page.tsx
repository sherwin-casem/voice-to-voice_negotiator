"use client";

import type { InterviewSessionStatus, SessionResponse } from "@voice/shared";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AudioActivityIndicator } from "@/components/interview/AudioActivityIndicator";
import { ConnectionStatus } from "@/components/interview/ConnectionStatus";
import { CurrentQuestion } from "@/components/interview/CurrentQuestion";
import { InterviewStatusPanel } from "@/components/interview/InterviewStatusPanel";
import { InterviewTimer } from "@/components/interview/InterviewTimer";
import { InterviewerStatePanel } from "@/components/interview/InterviewerStatePanel";
import { LiveTranscript } from "@/components/interview/LiveTranscript";
import { MicControls } from "@/components/interview/MicControls";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { useAppContext } from "@/context/AppProvider";
import { useInterviewTimer } from "@/hooks/useInterviewTimer";
import { useVoiceInterview } from "@/hooks/useVoiceInterview";
import { ApiClientError } from "@/lib/api-client";
import { getSession } from "@/lib/interview-api";

export default function LiveInterviewPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const router = useRouter();
  const { userId } = useAppContext();

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isEnding, setIsEnding] = useState(false);

  const refreshSession = useCallback(async () => {
    if (!userId || !sessionId) {
      return;
    }
    try {
      const loaded = await getSession(userId, sessionId);
      setSession(loaded);
    } catch (caught) {
      setLoadError(
        caught instanceof ApiClientError ? caught.message : "Unable to refresh session.",
      );
    }
  }, [sessionId, userId]);

  const voice = useVoiceInterview(sessionId, userId, {
    onSessionStatusChange: (status, questionCount) => {
      setSession((previous) =>
        previous
          ? {
              ...previous,
              status: status as InterviewSessionStatus,
              question_count: questionCount,
            }
          : previous,
      );
    },
    onSessionEnded: () => {
      void refreshSession();
    },
    onTurnComplete: () => {
      void refreshSession();
    },
  });

  const elapsedSeconds = useInterviewTimer(session?.status === "active");

  useEffect(() => {
    if (!userId || !sessionId) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    getSession(userId, sessionId)
      .then((loaded) => {
        if (!cancelled) {
          setSession(loaded);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setLoadError(
            caught instanceof ApiClientError ? caught.message : "Unable to load session.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId, userId]);

  useEffect(() => {
    if (userId && sessionId) {
      voice.connect();
    }
  }, [sessionId, userId, voice.connect]);

  async function handleStartInterview() {
    setIsStarting(true);
    setLoadError(null);
    try {
      await voice.startInterview();
      await refreshSession();
    } catch (caught) {
      setLoadError(
        caught instanceof Error ? caught.message : "Unable to start voice interview.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function handleEndInterview() {
    setIsEnding(true);
    setLoadError(null);
    try {
      await voice.endInterview();
      voice.disconnect();
      await refreshSession();
      router.push(`/interviews/${sessionId}/results`);
    } catch (caught) {
      setLoadError(
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
    return <Alert variant="error" title="Unable to open interview">{loadError}</Alert>;
  }

  return (
    <>
      <PageHeader
        title={session?.title ?? "Live interview"}
        description="Practice with the AI interviewer in real time."
        actions={
          <>
            {canStartInterview ? (
              <Button onClick={handleStartInterview} disabled={isStarting}>
                Start interview
              </Button>
            ) : null}
            {voice.isInterviewStarted ? (
              <Button variant="secondary" onClick={handleEndInterview} disabled={isEnding}>
                End interview
              </Button>
            ) : null}
            <ButtonLink href={`/interviews/${sessionId}/results`} variant="secondary">
              View results
            </ButtonLink>
          </>
        }
      />

      {loadError ? (
        <div className="mb-6">
          <Alert variant="error">{loadError}</Alert>
        </div>
      ) : null}

      {voice.errorMessage ? (
        <div className="mb-6">
          <Alert variant="warning" title="Connection issue">
            {voice.errorMessage}
          </Alert>
        </div>
      ) : null}

      {voice.permissionDenied ? (
        <div className="mb-6">
          <Alert variant="warning" title="Microphone blocked">
            Allow microphone access in your browser settings to answer by voice.
          </Alert>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-1">
          {session ? (
            <InterviewStatusPanel status={session.status} questionCount={session.question_count} />
          ) : null}
          <InterviewerStatePanel state={voice.interviewerState} />
          <ConnectionStatus state={voice.connectionState} />
          <InterviewTimer elapsedSeconds={elapsedSeconds} />
        </div>

        <div className="space-y-6 lg:col-span-2">
          <CurrentQuestion
            question={voice.currentQuestion}
            sequenceNum={voice.currentQuestionSequence}
          />
          <LiveTranscript entries={voice.transcript} />
          <div className="grid gap-6 md:grid-cols-2">
            <MicControls
              isEnabled={voice.isMicEnabled}
              isRecording={voice.isRecording}
              permissionDenied={voice.permissionDenied}
              canAnswer={canAnswer}
              onToggleMic={handleToggleMic}
              onFinishAnswer={voice.finishAnswer}
              disabled={!voice.isInterviewStarted}
            />
            <AudioActivityIndicator level={voice.audioLevel} isActive={voice.isRecording} />
          </div>
        </div>
      </div>
    </>
  );
}
