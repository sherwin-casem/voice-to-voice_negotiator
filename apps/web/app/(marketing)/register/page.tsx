"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { FieldError, Input, Label } from "@/components/ui/FormControls";
import { useAppContext } from "@/context/AppProvider";
import { routes } from "@/lib/routes";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthReady, isAuthenticated } = useAppContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthReady && isAuthenticated) {
      router.replace(routes.createInterview);
    }
  }, [isAuthReady, isAuthenticated, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await register(email.trim(), password);
      router.push(routes.createInterview);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create account.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isAuthReady) {
    return <Spinner label="Checking session" />;
  }

  return (
    <>
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-semibold text-[var(--text-primary)]">Create your account</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Start practicing voice interviews with personalized evaluation.
        </p>
      </div>

      <Card className="mx-auto max-w-md">
        <CardHeading>Sign up</CardHeading>
        <CardDescription>Create an account to save sessions and track progress over time.</CardDescription>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </div>
          <div>
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              minLength={8}
              required
            />
          </div>
          <FieldError message={error} />
          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? "Creating account…" : "Create account"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--text-muted)]">
          Already have an account?{" "}
          <Link href={routes.login} className="text-teal-400 hover:text-teal-300">
            Log in
          </Link>
        </p>
      </Card>

      <div className="mx-auto mt-6 max-w-md">
        <Alert variant="info">Use a password of at least 8 characters.</Alert>
      </div>
    </>
  );
}
