# API

FastAPI backend for the Voice-to-Voice Interview Negotiator.

## Application structure

```
app/
├── main.py              # ASGI entrypoint
├── factory.py           # create_app() — middleware, handlers, routers
├── config.py            # Environment-based settings
├── api/
│   ├── deps.py          # Shared FastAPI dependencies (DB sessions)
│   └── rest/
│       ├── router.py    # /api/v1 foundation routes
│       ├── health.py
│       └── features.py  # Optional feature routers (not mounted yet)
├── core/
│   ├── middleware.py    # Request ID / correlation ID
│   ├── logging.py       # Structured logging setup
│   ├── exceptions.py    # AppError hierarchy
│   └── error_handlers.py
├── db/
│   ├── session.py       # Sync/async engines and session factories
│   ├── health.py        # Database connectivity checks
│   └── models/          # SQLAlchemy models
└── schemas/             # Pydantic API schemas
```

Foundation scope today: health check, configuration, database connectivity, structured errors, logging, and migrations. Interview, voice, auth, and OpenAI integrations live in module folders but are not registered on the app router yet.

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

Health check: `GET http://localhost:8000/api/v1/health`

## Tests

```bash
# Foundation tests (default)
uv run --directory apps/api pytest -m "not feature"

# AI integration layer
uv run --directory apps/api pytest tests/ai -q

# All tests including feature modules
uv run --directory apps/api pytest
```

See [AI integration layer](../../docs/ai-integration.md).

OpenAPI docs: http://localhost:8000/docs
