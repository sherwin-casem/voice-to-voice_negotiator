# API

FastAPI backend for the Voice-to-Voice Interview Negotiator.

## Setup

```bash
# From repo root
uv sync --directory apps/api

# Run migrations (requires PostgreSQL)
uv run --directory apps/api alembic upgrade head
```

## Development

```bash
uv run --directory apps/api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
uv run --directory apps/api pytest
```

OpenAPI docs: http://localhost:8000/docs
