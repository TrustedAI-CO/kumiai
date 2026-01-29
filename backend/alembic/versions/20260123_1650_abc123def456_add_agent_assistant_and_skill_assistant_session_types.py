"""add_agent_assistant_and_skill_assistant_session_types

Add 'agent_assistant' and 'skill_assistant' to session_type ENUM.

This migration:
1. Creates new session_type ENUM with additional types
2. Updates sessions table to use new ENUM
3. Drops old ENUM type

Revision ID: abc123def456
Revises: 29ae23aa411f
Create Date: 2026-01-23 16:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "abc123def456"
down_revision: Union[str, None] = "29ae23aa411f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'agent_assistant' and 'skill_assistant' to session_type ENUM."""

    # Step 1: Create new ENUM type with additional values
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        CREATE TYPE session_type_new AS ENUM (
            'pm',
            'specialist',
            'assistant',
            'agent_assistant',
            'skill_assistant'
        );
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
    """Remove 'agent_assistant' and 'skill_assistant' from session_type ENUM."""

    # Step 1: Create new ENUM type without additional values
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        CREATE TYPE session_type_new AS ENUM ('pm', 'specialist', 'assistant');
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
