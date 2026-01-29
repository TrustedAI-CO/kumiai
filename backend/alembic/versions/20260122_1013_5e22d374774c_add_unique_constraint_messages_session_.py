"""add_unique_constraint_messages_session_sequence

Revision ID: 5e22d374774c
Revises: 7bbbb25175bf
Create Date: 2026-01-22 10:13:58.804602

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5e22d374774c"
down_revision: Union[str, None] = "7bbbb25175bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on (session_id, sequence) to prevent duplicate sequences
    op.create_unique_constraint(
        "uq_messages_session_sequence", "messages", ["session_id", "sequence"]
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint("uq_messages_session_sequence", "messages", type_="unique")
