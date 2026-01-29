"""drop_character_id_from_sessions

Remove character_id column from sessions table. We now exclusively use agent_id.

Revision ID: xyz789abc123
Revises: abc456def789
Create Date: 2026-01-21 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "xyz789abc123"
down_revision: Union[str, None] = "abc456def789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop character_id column and related index/constraint."""

    # Drop index first (if exists)
    op.execute("DROP INDEX IF EXISTS idx_sessions_character_id")

    # Drop foreign key constraint (if exists)
    op.execute(
        "ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_character_id_fkey"
    )

    # Drop the column (if exists)
    op.execute("ALTER TABLE sessions DROP COLUMN IF EXISTS character_id")


def downgrade() -> None:
    """Restore character_id column (data will be NULL)."""

    # Add column back
    op.add_column(
        "sessions", sa.Column("character_id", postgresql.UUID(), nullable=True)
    )

    # Recreate foreign key
    op.create_foreign_key(
        "sessions_character_id_fkey",
        "sessions",
        "characters",
        ["character_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Recreate index
    op.create_index(
        "idx_sessions_character_id",
        "sessions",
        ["character_id"],
        postgresql_where="deleted_at IS NULL",
    )
