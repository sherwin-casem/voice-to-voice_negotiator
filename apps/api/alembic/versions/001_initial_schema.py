"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-01

"""

from typing import Sequence, Union

from alembic import op

from app.db.base import Base
from app.db import models  # noqa: F401

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UPDATED_AT_TABLES = (
    "users",
    "user_profiles",
    "resumes",
    "job_descriptions",
    "interview_configurations",
    "interview_sessions",
    "candidate_answers",
    "evaluation_runs",
    "improvement_recommendations",
    "background_jobs",
)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    for table_name in UPDATED_AT_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table_name}_updated_at
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
            """
        )


def downgrade() -> None:
    for table_name in reversed(UPDATED_AT_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_updated_at ON {table_name};")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
