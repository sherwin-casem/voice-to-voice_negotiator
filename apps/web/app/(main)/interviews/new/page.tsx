"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { FieldError, Input, Label } from "@/components/ui/FormControls";
import { Spinner } from "@/components/ui/Alert";
import { useAppContext } from "@/context/AppProvider";
import { ApiClientError } from "@/lib/api-client";
import { createSession } from "@/lib/interview-api";

export default function CreateInterviewPage() {
  const router = useRouter();
  const { userId } = useAppContext();
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!userId) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const session = await createSession(userId, {
        title: title.trim() || null,
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
      <PageHeader
        title="Create interview"
        description="Start a new practice session. You will configure interview type and context next."
      />

      <Card className="max-w-xl">
        <CardTitle>Session details</CardTitle>
        <CardDescription>Optional title to help you identify this session later.</CardDescription>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              name="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Senior Backend Engineer — Technical Round"
              maxLength={200}
            />
          </div>
          <FieldError message={error} />
          <div className="flex items-center gap-3">
            <Button type="submit" disabled={!userId || isSubmitting}>
              Continue to setup
            </Button>
            {isSubmitting ? <Spinner label="Creating session" /> : null}
          </div>
        </form>
      </Card>
    </>
  );
}
