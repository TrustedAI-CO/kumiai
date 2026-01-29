"""remove_sequence_constraint_use_created_at

Revision ID: 20260123_0100
Revises: drop_character_table
Create Date: 2026-01-23 01:00:00.000000

Remove unique constraint on (session_id, sequence) to eliminate race conditions.
Messages will now be ordered by created_at timestamp instead of sequence number.
The sequence field is kept for backward compatibility but is no longer enforced unique.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260123_0100"
down_revision: Union[str, None] = "drop_character_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unique constraint on (session_id, sequence)."""
    # Drop the unique constraint
    op.drop_constraint("uq_messages_session_sequence", "messages", type_="unique")


def downgrade() -> None:
    """Restore unique constraint on (session_id, sequence)."""
    # Recreate the unique constraint
    op.create_unique_constraint(
        "uq_messages_session_sequence", "messages", ["session_id", "sequence"]
    )
