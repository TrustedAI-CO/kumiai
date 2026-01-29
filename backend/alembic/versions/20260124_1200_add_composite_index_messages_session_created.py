"""add_composite_index_messages_session_created

Revision ID: composite_msg_idx
Revises: add_team_member_ids
Create Date: 2026-01-24 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "composite_msg_idx"
down_revision: Union[str, None] = "add_team_member_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index for (session_id, created_at DESC)
    # This optimizes get_by_session_ordered queries which filter by session_id
    # and order by created_at DESC
    op.create_index(
        "idx_messages_session_id_created_at",
        "messages",
        ["session_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index("idx_messages_session_id_created_at", table_name="messages")
