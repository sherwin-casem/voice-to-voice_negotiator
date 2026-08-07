"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Alert, Spinner } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardHeading } from "@/components/ui/Card";
import { FieldError, Input, Label } from "@/components/ui/FormControls";
import { GlowArt } from "@/components/ui/GlowArt";
import { useAppContext } from "@/context/AppProvider";
import { registerWithNext, routes, sanitizeNextPath } from "@/lib/routes";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthReady, isAuthenticated } = useAppContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = sanitizeNextPath(searchParams.get("next"), routes.createInterview);

  useEffect(() => {
    if (isAuthReady && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthReady, isAuthenticated, nextPath, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await login(email.trim(), password);
      router.push(nextPath);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isAuthReady) {
    return <Spinner label="Checking session" />;
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeading>Log in</CardHeading>
      <CardDescription>Sign in to practice interviews and view your evaluations.</CardDescription>
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
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <FieldError message={error} />
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? "Signing in…" : "Log in"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-[var(--text-muted)]">
        Don&apos;t have an account?{" "}
        <Link href={registerWithNext(nextPath)} className="text-teal-400 hover:text-teal-300">
          Sign up
        </Link>
      </p>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <div className="relative">
      <GlowArt
        src="/backgrounds/voice-crystal.png"
        width={298}
        height={223}
        sizes="24rem"
        className="absolute left-1/2 top-1/2 w-96 max-w-none -translate-x-1/2 -translate-y-1/2 opacity-40"
      />
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-semibold text-[var(--text-primary)]">Welcome back</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Access your interview practice and evaluation history.
        </p>
      </div>
      <Suspense fallback={<Spinner label="Loading" />}>
        <LoginForm />
      </Suspense>
      <div className="mx-auto mt-6 max-w-md">
        <Alert variant="info">
          Evaluations and interview practice require an account so your sessions stay private.
        </Alert>
      </div>
    </div>
  );
}
