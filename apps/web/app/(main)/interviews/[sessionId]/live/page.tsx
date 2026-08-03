"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
import { useInterviewSocket } from "@/hooks/useInterviewSocket";
import { useInterviewTimer } from "@/hooks/useInterviewTimer";
import { useMicrophone } from "@/hooks/useMicrophone";
import { ApiClientError } from "@/lib/api-client";
import { endSession, getSession, startSession } from "@/lib/interview-api";
import type { SessionResponse } from "@voice/shared";

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

  const live = useInterviewSocket(sessionId, userId);
  const microphone = useMicrophone();
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
      live.connect();
    }
  }, [live.connect, sessionId, userId]);

  async function handleStartInterview() {
    if (!userId) {
      return;
    }
    setIsStarting(true);
    try {
      const updated = await startSession(userId, sessionId);
      setSession(updated);
      live.startInterview();
    } catch (caught) {
      setLoadError(
        caught instanceof ApiClientError ? caught.message : "Unable to start interview.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function handleEndInterview() {
    if (!userId) {
      return;
    }
    setIsEnding(true);
    try {
      await endSession(userId, sessionId);
      live.disconnect();
      microphone.disable();
      router.push(`/interviews/${sessionId}/results`);
    } catch (caught) {
      setLoadError(caught instanceof ApiClientError ? caught.message : "Unable to end interview.");
    } finally {
      setIsEnding(false);
    }
  }

  async function handleToggleMic() {
    if (microphone.isRecording) {
      microphone.stopRecording();
      return;
    }
    if (!microphone.isEnabled) {
      await microphone.enable();
    }
    microphone.startRecording();
  }

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
            {session?.status !== "active" ? (
              <Button onClick={handleStartInterview} disabled={isStarting}>
                Start interview
              </Button>
            ) : null}
            <Button variant="secondary" onClick={handleEndInterview} disabled={isEnding}>
              End interview
            </Button>
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

      {live.errorMessage ? (
        <div className="mb-6">
          <Alert variant="warning" title="Connection issue">
            {live.errorMessage}
          </Alert>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-1">
          {session ? (
            <InterviewStatusPanel status={session.status} questionCount={session.question_count} />
          ) : null}
          <InterviewerStatePanel state={live.interviewerState} />
          <ConnectionStatus state={live.connectionState} />
          <InterviewTimer elapsedSeconds={elapsedSeconds} />
        </div>

        <div className="space-y-6 lg:col-span-2">
          <CurrentQuestion
            question={live.currentQuestion}
            sequenceNum={live.currentQuestionSequence}
          />
          <LiveTranscript entries={live.transcript} />
          <div className="grid gap-6 md:grid-cols-2">
            <MicControls
              isEnabled={microphone.isEnabled}
              isRecording={microphone.isRecording}
              permissionDenied={microphone.permissionDenied}
              onToggleMic={handleToggleMic}
              onFinishAnswer={live.finishAnswer}
              disabled={session?.status !== "active"}
            />
            <AudioActivityIndicator
              level={microphone.level}
              isActive={microphone.isRecording}
            />
          </div>
        </div>
      </div>
    </>
  );
}
