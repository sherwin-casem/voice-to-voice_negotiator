# Shared contracts

Cross-app API types and OpenAPI contract used by the web frontend and FastAPI backend.

## Contents

- `src/index.ts` — TypeScript types for API envelopes and health check
- `openapi.yaml` — OpenAPI 3.1 contract (source of truth for REST shape)

Keep Python Pydantic schemas in `apps/api/app/schemas/` aligned with these contracts.
