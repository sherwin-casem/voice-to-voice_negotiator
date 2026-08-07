"""make refresh_tokens.token_hash unique

Revision ID: 003_unique_refresh_token_hash
Revises: 002_add_relevance_agent
Create Date: 2026-08-07

"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_unique_refresh_token_hash"
down_revision: Union[str, None] = "002_add_relevance_agent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove any duplicate hashes before adding the unique constraint
    # (keep the most recently created row for each hash).
    op.execute(
        """
        DELETE FROM refresh_tokens a
        USING refresh_tokens b
        WHERE a.token_hash = b.token_hash
          AND a.created_at < b.created_at
        """
    )
    op.create_unique_constraint(
        "uq_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_refresh_tokens_token_hash", "refresh_tokens", type_="unique")
