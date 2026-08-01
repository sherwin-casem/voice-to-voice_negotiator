# Development Guide

## Monorepo structure

| Path | Stack | Run independently |
|------|-------|-------------------|
| `apps/api` | FastAPI, SQLAlchemy, Alembic, uv | Yes — `uv run uvicorn app.main:app --reload` from `apps/api` |
| `apps/web` | Next.js, TypeScript, Tailwind | Yes — `npm run dev` from `apps/web` |
| `packages/shared` | TypeScript types, OpenAPI | Built/consumed by web; Python schemas mirror contracts |

## Environment variables

Copy `.env.example` to `.env` at the repository root. The API loads root `.env` automatically.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/voice_negotiator` | PostgreSQL connection |
| `DATABASE_ECHO` | `false` | SQLAlchemy SQL logging |
| `API_HOST` | `0.0.0.0` | Uvicorn bind host |
| `API_PORT` | `8000` | Uvicorn port |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins (comma-separated) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL for the web app |

## Database

```bash
docker compose up -d
uv run --directory apps/api alembic upgrade head
```

## Testing

```bash
# API
uv run --directory apps/api pytest

# Web lint
npm run lint:web
```

## Shared contracts

- TypeScript: `@voice/shared` (`packages/shared`)
- OpenAPI: `packages/shared/openapi.yaml`
- Python: `apps/api/app/schemas/` — keep aligned with shared contract

When adding endpoints, update all three locations together.
