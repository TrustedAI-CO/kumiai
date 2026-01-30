"""add cancelled status to session_status enum

Revision ID: 20260130_0000
Revises: 20260124_1200
Create Date: 2026-01-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260130_0000"
down_revision: Union[str, None] = (
    "20260124_1200_add_composite_index_messages_session_created"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'cancelled' to session_status enum."""
    # Add 'cancelled' value to enum (PostgreSQL only - SQLite doesn't have enums)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'cancelled'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'session_status')
            ) THEN
                ALTER TYPE session_status ADD VALUE 'cancelled';
            END IF;
        END$$;
    """
    )


def downgrade() -> None:
    """Remove 'cancelled' from session_status enum.

    Note: PostgreSQL does not support removing enum values directly.
    Manual intervention required if downgrade is needed.
    """
    pass
