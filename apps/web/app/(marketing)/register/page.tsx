"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { FieldError, Input, Label } from "@/components/ui/FormControls";
import { useAppContext } from "@/context/AppProvider";
import { routes } from "@/lib/routes";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { register, isAuthReady, isAuthenticated } = useAppContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = searchParams.get("next") ?? routes.createInterview;

  useEffect(() => {
    if (isAuthReady && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthReady, isAuthenticated, nextPath, router]);

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
      router.push(nextPath);
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
        <Link href={`${routes.login}?next=${encodeURIComponent(nextPath)}`} className="text-teal-400 hover:text-teal-300">
          Log in
        </Link>
      </p>
    </Card>
  );
}

export default function RegisterPage() {
  return (
    <>
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-semibold text-[var(--text-primary)]">Create your account</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Start practicing voice interviews with personalized evaluation.
        </p>
      </div>
      <Suspense fallback={<Spinner label="Loading" />}>
        <RegisterForm />
      </Suspense>
      <div className="mx-auto mt-6 max-w-md">
        <Alert variant="info">Use a password of at least 8 characters.</Alert>
      </div>
    </>
  );
}
