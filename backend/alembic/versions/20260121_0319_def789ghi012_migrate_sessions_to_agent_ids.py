"""migrate_sessions_to_agent_ids

Migrate sessions from Character UUIDs to Agent string IDs.

This migration:
1. Adds agent_id column (VARCHAR)
2. Makes character_id nullable
3. Adds check constraint to ensure at least one is set

Revision ID: def789ghi012
Revises: 0cd45723ec3c
Create Date: 2026-01-21 03:19:00.000000

NOTE (2026-09-15): down_revision used to read "abc123def456". That was a hand-typed
placeholder id, and on 2026-01-23 a real revision was created that happened to use the
same string — closing a 13-revision cycle in the graph
(def789ghi012 -> abc123def456 -> ... -> 5d55bfcf3778 -> def789ghi012). `alembic history`
hung forever as a result. Repointed at 0cd45723ec3c, the actual predecessor by date
(2026-01-20 22:48). Nothing re-runs: every database is already stamped past this point.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "def789ghi012"
down_revision: Union[str, None] = "0cd45723ec3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate from Character UUIDs to Agent string IDs."""
    # Step 1: Add new agent_id column
    op.add_column("sessions", sa.Column("agent_id", sa.String(255), nullable=True))

    # Step 2: Make character_id nullable
    # First, drop the NOT NULL constraint
    op.alter_column(
        "sessions", "character_id", existing_type=postgresql.UUID(), nullable=True
    )

    # Step 3: Add check constraint to ensure at least one is set
    op.create_check_constraint(
        "chk_sessions_has_agent_or_character",
        "sessions",
        "(agent_id IS NOT NULL) OR (character_id IS NOT NULL)",
    )

    # Step 4: Drop the foreign key constraint on character_id
    # Make it optional since we're moving to agent_id
    op.drop_constraint("sessions_character_id_fkey", "sessions", type_="foreignkey")

    # Step 5: Re-add foreign key but as nullable (SET NULL on delete)
    op.create_foreign_key(
        "sessions_character_id_fkey",
        "sessions",
        "characters",
        ["character_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Step 6: Add index on agent_id
    op.create_index(
        "idx_sessions_agent_id",
        "sessions",
        ["agent_id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL AND agent_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Rollback to Character UUIDs only (WARNING: data loss)."""
    # Drop new index
    op.drop_index("idx_sessions_agent_id", table_name="sessions", if_exists=True)

    # Drop foreign key
    op.drop_constraint("sessions_character_id_fkey", "sessions", type_="foreignkey")

    # Drop check constraint
    op.drop_constraint("chk_sessions_has_agent_or_character", "sessions", type_="check")

    # Make character_id NOT NULL again (will fail if there are NULL values)
    op.alter_column(
        "sessions", "character_id", existing_type=postgresql.UUID(), nullable=False
    )

    # Restore original foreign key constraint
    op.create_foreign_key(
        "sessions_character_id_fkey",
        "sessions",
        "characters",
        ["character_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop agent_id column
    op.drop_column("sessions", "agent_id")
