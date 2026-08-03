"""Local Postgres bootstrap when Docker/default postgres password is unavailable.

Creates an isolated schema (default: vvn) in an existing database using credentials
that already work on this machine. Does not modify postgres superuser settings.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, text

DEFAULT_ADMIN_URL = "postgresql+psycopg://salesapp:salesapp@localhost:5432/salesapp"
DEFAULT_SCHEMA = "vvn"


def bootstrap(admin_url: str, schema: str) -> str:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": schema},
        ).fetchone()
        if not exists:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            print(f"Created schema {schema}")

    # Reuse admin credentials; tables are isolated by search_path.
    base_url = admin_url.split("?", 1)[0]
    app_url = f"{base_url}?options=-csearch_path%3D{schema}"
    print("Bootstrap complete.")
    print(f"DATABASE_URL={app_url}")
    return app_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap local Postgres schema for VVN")
    parser.add_argument("--admin-url", default=DEFAULT_ADMIN_URL)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    try:
        bootstrap(args.admin_url, args.schema)
        return 0
    except Exception as exc:  # noqa: BLE001 — CLI helper
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        print(
            "\nIf this machine uses different Postgres credentials, either:\n"
            "  1. Start Docker Postgres: docker compose -f infrastructure/docker-compose.yml up -d\n"
            "  2. Create database manually as postgres superuser:\n"
            "       createdb voice_negotiator\n"
            "     then set DATABASE_URL in .env to match your credentials\n",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
