#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
