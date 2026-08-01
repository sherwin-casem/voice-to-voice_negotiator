# Web

Next.js frontend for the Voice-to-Voice Interview Negotiator.

## Run independently

```bash
npm install
npm run dev
```

From the repository root you can also run `npm run dev:web`.

## Environment

Set `NEXT_PUBLIC_API_URL` in the root `.env` file (default: `http://localhost:8000`).

## Shared types

Imports API contracts from `@voice/shared` (`packages/shared`).
