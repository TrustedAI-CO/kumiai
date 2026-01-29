"""remove_orchestrator_session_type

Remove 'orchestrator' from session_type ENUM.

This migration:
1. Creates new session_type ENUM without 'orchestrator'
2. Updates sessions table to use new ENUM
3. Drops old ENUM type

Revision ID: 5d55bfcf3778
Revises: def789ghi012
Create Date: 2026-01-21 10:34:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d55bfcf3778"
down_revision: Union[str, None] = "def789ghi012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove 'orchestrator' from session_type ENUM."""

    # Step 1: Create new ENUM type without 'orchestrator'
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        CREATE TYPE session_type_new AS ENUM ('pm', 'specialist', 'assistant');
    """
        )
    )

    # Step 2: Convert the column to use the new type
    # Using USING clause to handle the conversion
    conn.execute(
        sa.text(
            """
        ALTER TABLE sessions
        ALTER COLUMN session_type TYPE session_type_new
        USING session_type::text::session_type_new;
    """
        )
    )

    # Step 3: Drop the old ENUM type
    conn.execute(
        sa.text(
            """
        DROP TYPE session_type;
    """
        )
    )

    # Step 4: Rename the new type to the original name
    conn.execute(
        sa.text(
            """
        ALTER TYPE session_type_new RENAME TO session_type;
    """
        )
    )


def downgrade() -> None:
    """Restore 'orchestrator' to session_type ENUM."""

    # Step 1: Create new ENUM type with 'orchestrator'
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        CREATE TYPE session_type_new AS ENUM ('pm', 'orchestrator', 'specialist', 'assistant');
    """
        )
    )

    # Step 2: Convert the column to use the new type
    conn.execute(
        sa.text(
            """
        ALTER TABLE sessions
        ALTER COLUMN session_type TYPE session_type_new
        USING session_type::text::session_type_new;
    """
        )
    )

    # Step 3: Drop the old ENUM type
    conn.execute(
        sa.text(
            """
        DROP TYPE session_type;
    """
        )
    )

    # Step 4: Rename the new type to the original name
    conn.execute(
        sa.text(
            """
        ALTER TYPE session_type_new RENAME TO session_type;
    """
        )
    )
