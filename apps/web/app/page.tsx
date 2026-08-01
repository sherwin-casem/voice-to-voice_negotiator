import { API_ROUTES } from "@voice/shared";

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6">
      <main className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-10 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Voice-to-Voice Interview Negotiator
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">
          Development shell
        </h1>
        <p className="mt-4 text-base leading-7 text-zinc-600">
          Frontend and API scaffolds are ready. Business features, auth, and
          OpenAI integration are not implemented yet.
        </p>
        <dl className="mt-8 space-y-3 text-sm text-zinc-700">
          <div className="flex justify-between gap-4 border-b border-zinc-100 pb-2">
            <dt className="font-medium">Web</dt>
            <dd>http://localhost:3000</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-zinc-100 pb-2">
            <dt className="font-medium">API</dt>
            <dd>{apiUrl}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="font-medium">Health route</dt>
            <dd>{API_ROUTES.health}</dd>
          </div>
        </dl>
      </main>
    </div>
  );
}
