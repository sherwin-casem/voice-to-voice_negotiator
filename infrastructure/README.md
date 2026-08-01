# Infrastructure

Local development infrastructure for the monorepo.

## PostgreSQL

```bash
# From repository root
docker compose -f infrastructure/docker-compose.yml up -d
```

Or use `scripts/dev-db.ps1` / `scripts/dev-db.sh`.

Connection defaults (see root `.env.example`):

- Host: `localhost`
- Port: `5432`
- Database: `voice_negotiator`
- User / password: `postgres` / `postgres`

## Scope

MVP local setup only — PostgreSQL via Docker Compose. No cloud, Redis, or object storage yet.
