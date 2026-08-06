"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { InterviewFunnelStepper } from "@/components/interview/InterviewFunnelStepper";
import { PageHeader } from "@/components/layout/PageHeader";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { FieldError, Input, Label } from "@/components/ui/FormControls";
import { Spinner } from "@/components/ui/Alert";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { useAppContext } from "@/context/AppProvider";
import { ApiClientError } from "@/lib/api-client";
import { createSession } from "@/lib/interview-api";
import { routes } from "@/lib/routes";

const FLOW_STEPS = [
  { step: "1", title: "Configure", detail: "Choose interview type, difficulty, and context." },
  { step: "2", title: "Practice", detail: "Voice interview with a live AI interviewer." },
  { step: "3", title: "Review", detail: "Multi-agent scoring and coaching feedback." },
];

export default function CreateInterviewPage() {
  const router = useRouter();
  const { isAuthenticated, isAuthReady } = useAppContext();
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const trimmedTitle = title.trim();
  const isTitleValid = trimmedTitle.length > 0;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isAuthenticated) {
      return;
    }

    if (!isTitleValid) {
      setError("Title is required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const session = await createSession({
        title: trimmedTitle,
      });
      router.push(`/interviews/${session.id}/setup`);
    } catch (caught) {
      const message =
        caught instanceof ApiClientError ? caught.message : "Unable to create interview session.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <InterviewFunnelStepper current="create" className="mb-6" />

      <PageHeader
        title="Create interview"
        description="Start a new practice session. You will configure interview type and context next."
        actions={
          <>
            <ButtonLink href={routes.previewResults} variant="secondary">
              View evaluation
            </ButtonLink>
            <ButtonLink href={routes.evaluations} variant="secondary">
              View evaluations
            </ButtonLink>
          </>
        }
      />

      <GlassPanel className="mb-6 border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-cyan-500/5 p-6">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">How it works</h2>
        <ol className="mt-4 grid gap-4 sm:grid-cols-3">
          {FLOW_STEPS.map((item) => (
            <li key={item.step} className="rounded-xl border border-[var(--border-glass)] bg-black/10 p-4">
              <p className="text-section-label">Step {item.step}</p>
              <p className="mt-2 font-medium text-[var(--text-primary)]">{item.title}</p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">{item.detail}</p>
            </li>
          ))}
        </ol>
      </GlassPanel>

      <Card className="mx-auto max-w-xl">
        <CardHeading>Session details</CardHeading>
        <CardDescription>
          Give this practice session a title so you can find it later. You will set your target
          role, interview type, and difficulty on the next setup step.
        </CardDescription>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="title">
              Title <span className="text-red-400">*</span>
            </Label>
            <Input
              id="title"
              name="title"
              value={title}
              onChange={(event) => {
                setTitle(event.target.value);
                if (error === "Title is required.") {
                  setError(null);
                }
              }}
              placeholder="Senior Backend Engineer — Technical Round"
              maxLength={200}
              required
              aria-required="true"
            />
          </div>
          <FieldError message={error} />
          <div className="flex items-center gap-3">
            <Button
              type="submit"
              disabled={!isAuthReady || !isAuthenticated || !isTitleValid || isSubmitting}
            >
              Continue to setup
            </Button>
            {isSubmitting ? <Spinner label="Creating session" /> : null}
          </div>
        </form>
      </Card>
    </>
  );
}
