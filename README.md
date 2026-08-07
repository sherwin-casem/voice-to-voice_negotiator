# Voice-to-Voice Interview Negotiator

AI-powered voice interview practice with multi-agent evaluation.

## Repository layout

```
voice-to-voice-negotiator/
├── apps/
│   ├── web/          Next.js, TypeScript, Tailwind CSS
│   └── api/          FastAPI, uv, pytest, SQLAlchemy
├── packages/
│   └── shared/       Shared API contracts and TypeScript types
├── docs/             Architecture and database design
├── infrastructure/   Local Docker Compose (PostgreSQL)
├── scripts/          Development helpers
├── Agents.md
├── README.md
└── .env.example
```

## Prerequisites

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (for local PostgreSQL)

## Quick start

### 1. Environment

```bash
cp .env.example .env
```

### 2. PostgreSQL

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### 3. API

```bash
uv sync --directory apps/api
uv run --directory apps/api alembic upgrade head
npm run dev:api
```

On Windows, use `run_dev.py` (via `npm run dev:api` or `scripts/dev-api.ps1`) so async PostgreSQL works. On Linux/macOS you may also run `uv run --directory apps/api uvicorn app.main:app --reload --port 8000`.

API docs: http://localhost:8000/docs

### 4. Web

```bash
npm install
npm run dev:web
```

Web app: http://localhost:3000

## Development scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.ps1` | Install JS and Python dependencies |
| `npm run dev:api` | Run FastAPI with reload (Windows-safe event loop) |
| `npm run dev:web` | Run Next.js dev server |
| `scripts/dev-db.ps1` | Start PostgreSQL via Docker Compose |
| `scripts/test-api.ps1` | Run API pytest suite |

Unix equivalents are available as `.sh` files.

## Documentation

- [Architecture](docs/architecture.md)
- [Database schema](docs/database.md)
- [AI integration layer](docs/ai-integration.md)
- [Development guide](docs/development.md)
- [Agents.md](Agents.md) — engineering principles

## Current scope

Initial scaffolding only: health endpoint, database models/migrations, and frontend shell. Authentication, OpenAI integration, and interview features are not implemented yet.
