"use client";

import type { ConfigureSessionRequest, DifficultyLevel, InterviewType } from "@voice/shared";
import { DIFFICULTY_LEVEL_LABELS, INTERVIEW_TYPE_LABELS } from "@voice/shared";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { InterviewFunnelStepper } from "@/components/interview/InterviewFunnelStepper";
import { PageHeader } from "@/components/layout/PageHeader";
import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { FieldError, FieldHint, Input, Label, Select, Textarea } from "@/components/ui/FormControls";
import { useAppContext } from "@/context/AppProvider";
import { useSession } from "@/hooks/useSession";
import { ApiClientError } from "@/lib/api-client";
import {
  configureSession,
  createJobDescription,
  createResume,
} from "@/lib/interview-api";

const INTERVIEW_TYPES = Object.keys(INTERVIEW_TYPE_LABELS) as InterviewType[];
const DIFFICULTY_LEVELS = Object.keys(DIFFICULTY_LEVEL_LABELS) as DifficultyLevel[];

export default function InterviewSetupPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const router = useRouter();
  const { isAuthenticated } = useAppContext();
  const { session, error: sessionError, isLoading: loadingSession } = useSession(sessionId);

  const [interviewType, setInterviewType] = useState<InterviewType | "">("");
  const [difficulty, setDifficulty] = useState<DifficultyLevel | "">("");
  const [targetRole, setTargetRole] = useState("");
  const effectiveTargetRole = targetRole || session?.title || "";
  const [companyContext, setCompanyContext] = useState("");
  const [maxQuestions, setMaxQuestions] = useState("5");
  const [resumeText, setResumeText] = useState("");
  const [jobDescriptionText, setJobDescriptionText] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    interviewType?: string;
    difficulty?: string;
  }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isConfigurationValid = interviewType !== "" && difficulty !== "";

  function validateConfiguration() {
    const nextErrors: { interviewType?: string; difficulty?: string } = {};

    if (!interviewType) {
      nextErrors.interviewType = "Interview type is required.";
    }
    if (!difficulty) {
      nextErrors.difficulty = "Difficulty is required.";
    }

    setFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isAuthenticated) {
      return;
    }

    if (!validateConfiguration()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      let resumeId: string | null = null;
      let jobDescriptionId: string | null = null;

      if (resumeText.trim()) {
        const resume = await createResume({
          title: "Session resume",
          raw_text: resumeText.trim(),
        });
        resumeId = resume.id;
      }

      if (jobDescriptionText.trim()) {
        const jobDescription = await createJobDescription({
          title: "Session job description",
          raw_text: jobDescriptionText.trim(),
        });
        jobDescriptionId = jobDescription.id;
      }

      const body: ConfigureSessionRequest = {
        interview_type: interviewType as InterviewType,
        difficulty: difficulty as DifficultyLevel,
        target_role: effectiveTargetRole.trim() || null,
        company_context: companyContext.trim() || null,
        max_questions: Number(maxQuestions) || null,
        resume_id: resumeId,
        job_description_id: jobDescriptionId,
      };

      await configureSession(sessionId, body);
      router.push(`/interviews/${sessionId}/live`);
    } catch (caught) {
      setSubmitError(
        caught instanceof ApiClientError ? caught.message : "Unable to configure session.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loadingSession) {
    return <Spinner label="Loading session" />;
  }

  if (sessionError) {
    return <Alert variant="error" title="Session unavailable">{sessionError}</Alert>;
  }

  return (
    <>
      <InterviewFunnelStepper current="setup" sessionId={sessionId} className="mb-6" />

      <PageHeader
        title="Interview setup"
        description="Configure interview type, difficulty, and optional resume or job description context."
      />

      <p className="mb-6">
        <Link
          href="/interviews/new"
          className="text-sm font-medium text-teal-400 underline-offset-2 hover:text-teal-300 hover:underline"
        >
          ← Back to create
        </Link>
      </p>

      <form className="grid gap-6 lg:grid-cols-2" onSubmit={handleSubmit}>
        <Card>
          <CardHeading>Interview configuration</CardHeading>
          <CardDescription>These settings drive the AI interviewer behavior.</CardDescription>
          <div className="mt-4 space-y-4">
            <div>
              <Label htmlFor="interview-type" required>
                Interview type
              </Label>
              <Select
                id="interview-type"
                name="interview_type"
                value={interviewType}
                required
                aria-required="true"
                aria-invalid={fieldErrors.interviewType ? true : undefined}
                onChange={(event) => {
                  setInterviewType(event.target.value as InterviewType | "");
                  if (fieldErrors.interviewType) {
                    setFieldErrors((previous) => ({ ...previous, interviewType: undefined }));
                  }
                }}
              >
                <option value="" disabled>
                  Select interview type
                </option>
                {INTERVIEW_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {INTERVIEW_TYPE_LABELS[type]}
                  </option>
                ))}
              </Select>
              <FieldHint>Behavioral, technical, system design, leadership, or HR.</FieldHint>
              <FieldError message={fieldErrors.interviewType} />
            </div>
            <div>
              <Label htmlFor="difficulty" required>
                Difficulty
              </Label>
              <Select
                id="difficulty"
                name="difficulty"
                value={difficulty}
                required
                aria-required="true"
                aria-invalid={fieldErrors.difficulty ? true : undefined}
                onChange={(event) => {
                  setDifficulty(event.target.value as DifficultyLevel | "");
                  if (fieldErrors.difficulty) {
                    setFieldErrors((previous) => ({ ...previous, difficulty: undefined }));
                  }
                }}
              >
                <option value="" disabled>
                  Select difficulty
                </option>
                {DIFFICULTY_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {DIFFICULTY_LEVEL_LABELS[level]}
                  </option>
                ))}
              </Select>
              <FieldHint>Calibrates question depth and interviewer expectations.</FieldHint>
              <FieldError message={fieldErrors.difficulty} />
            </div>
            <div>
              <Label htmlFor="target-role">Target role</Label>
              <Input
                id="target-role"
                value={effectiveTargetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="Senior Backend Engineer"
              />
            </div>
            <div>
              <Label htmlFor="company-context">Company context</Label>
              <Textarea
                id="company-context"
                rows={3}
                value={companyContext}
                onChange={(event) => setCompanyContext(event.target.value)}
                placeholder="Fast-growing fintech, high-scale payments platform..."
              />
            </div>
            <div>
              <Label htmlFor="max-questions">Maximum questions</Label>
              <Input
                id="max-questions"
                type="number"
                min={1}
                max={50}
                value={maxQuestions}
                onChange={(event) => setMaxQuestions(event.target.value)}
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeading>Context documents</CardHeading>
          <CardDescription>Optional resume and job description text for tailored questions.</CardDescription>
          <div className="mt-4 space-y-4">
            <div>
              <Label htmlFor="resume-text">Resume text</Label>
              <Textarea
                id="resume-text"
                rows={6}
                value={resumeText}
                onChange={(event) => setResumeText(event.target.value)}
                placeholder="Paste resume content..."
              />
            </div>
            <div>
              <Label htmlFor="job-description-text">Job description text</Label>
              <Textarea
                id="job-description-text"
                rows={6}
                value={jobDescriptionText}
                onChange={(event) => setJobDescriptionText(event.target.value)}
                placeholder="Paste job description content..."
              />
            </div>
          </div>
        </Card>

        <div className="lg:col-span-2">
          <FieldError message={submitError} />
          <div className="mt-2 flex items-center gap-3">
            <Button type="submit" disabled={isSubmitting || !isConfigurationValid}>
              Save and start live interview
            </Button>
            {isSubmitting ? <Spinner label="Saving configuration" /> : null}
          </div>
        </div>
      </form>
    </>
  );
}
