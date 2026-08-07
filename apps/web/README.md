# Web

Next.js frontend for the Voice-to-Voice Interview Negotiator.

## Run independently

```bash
npm install
npm run dev
```

From the repository root you can also run `npm run dev:web`.

## Environment

Copy `apps/web/.env.example` to `apps/web/.env.local`.

- Leave `NEXT_PUBLIC_API_URL` empty in local dev so the browser calls same-origin `/api/*`, which Next.js rewrites to the backend.
- Set `API_PROXY_TARGET` to your API origin (default `http://127.0.0.1:8000`). A mismatched port breaks sign-up and log-in.
- Set `NEXT_PUBLIC_WS_URL` for live voice interviews (default `ws://127.0.0.1:8000`).

## Shared types

Imports API contracts from `@voice/shared` (`packages/shared`).
