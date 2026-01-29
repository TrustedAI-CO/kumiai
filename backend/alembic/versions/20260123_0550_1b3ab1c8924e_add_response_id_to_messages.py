"""add_response_id_to_messages

Revision ID: 1b3ab1c8924e
Revises: 20260123_0100
Create Date: 2026-01-23 05:50:15.410548

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b3ab1c8924e"
down_revision: Union[str, None] = "20260123_0100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add response_id column to messages table
    op.add_column("messages", sa.Column("response_id", sa.String(36), nullable=True))

    # Add index for efficient querying
    op.create_index(
        "idx_messages_response_id",
        "messages",
        ["response_id"],
        postgresql_where=sa.text("response_id IS NOT NULL"),
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("idx_messages_response_id", table_name="messages")

    # Drop column
    op.drop_column("messages", "response_id")
