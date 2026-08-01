#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Installing root npm workspaces..."
cd "$ROOT"
npm install

echo "Installing Python dependencies with uv..."
uv sync --directory "$ROOT/apps/api"

if [[ "${1:-}" == "--migrate" ]]; then
  echo "Running database migrations..."
  uv run --directory "$ROOT/apps/api" alembic upgrade head
fi

echo "Setup complete."
