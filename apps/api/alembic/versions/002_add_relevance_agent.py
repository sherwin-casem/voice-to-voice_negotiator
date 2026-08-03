"""add relevance_evaluation to agent_name enum

Revision ID: 002_add_relevance_agent
Revises: 001_initial_schema
Create Date: 2026-08-03

"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_add_relevance_agent"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE agent_name ADD VALUE IF NOT EXISTS 'relevance_evaluation'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
