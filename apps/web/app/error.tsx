"use client";

import { useEffect } from "react";

import { ButtonLink } from "@/components/ui/ButtonLink";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled application error", error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold text-slate-100">Something went wrong</h1>
      <p className="text-sm text-slate-400">
        An unexpected error occurred. You can retry or return home.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
        >
          Try again
        </button>
        <ButtonLink href="/interviews/new" variant="secondary">
          Back to home
        </ButtonLink>
      </div>
    </main>
  );
}
