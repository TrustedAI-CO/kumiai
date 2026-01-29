"""refactor_message_sender_fields

Refactor message sender fields to simpler schema:
- Drop: sender_role, sender_id, sender_name, sender_instance
- Keep: agent_name (rename to agent_name if needed)
- Add: agent_id, from_instance_id

New schema:
- agent_id: VARCHAR(255) - Source of truth for which agent sent the message
- agent_name: VARCHAR(255) - Display name of the sending agent (already exists)
- from_instance_id: UUID - Session ID where message originated from (for cross-session routing)

Revision ID: def456ghi789
Revises: abc456def789
Create Date: 2026-01-21 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "def456ghi789"
down_revision: Union[str, None] = "abc456def789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Refactor sender attribution fields to simpler schema."""

    # Drop old indexes
    op.drop_index("idx_messages_sender_id", table_name="messages")
    op.drop_index("idx_messages_sender_role", table_name="messages")

    # Add new columns
    op.add_column(
        "messages", sa.Column("agent_id", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "messages",
        sa.Column("from_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Migrate data: sender_id -> agent_id
    op.execute(
        """
        UPDATE messages
        SET agent_id = sender_id
        WHERE sender_id IS NOT NULL
    """
    )

    # Drop old columns
    op.drop_column("messages", "sender_role")
    op.drop_column("messages", "sender_id")
    op.drop_column("messages", "sender_name")
    op.drop_column("messages", "sender_instance")

    # Create new indexes
    op.create_index(
        "idx_messages_agent_id",
        "messages",
        ["agent_id"],
        postgresql_where="agent_id IS NOT NULL",
    )
    op.create_index(
        "idx_messages_from_instance_id",
        "messages",
        ["from_instance_id"],
        postgresql_where="from_instance_id IS NOT NULL",
    )


def downgrade() -> None:
    """Revert to old sender attribution fields."""

    # Drop new indexes
    op.drop_index("idx_messages_from_instance_id", table_name="messages")
    op.drop_index("idx_messages_agent_id", table_name="messages")

    # Add old columns back
    op.add_column(
        "messages", sa.Column("sender_role", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("sender_id", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("sender_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("sender_instance", sa.String(length=255), nullable=True)
    )

    # Migrate data back: agent_id -> sender_id
    op.execute(
        """
        UPDATE messages
        SET sender_id = agent_id
        WHERE agent_id IS NOT NULL
    """
    )

    # Drop new columns
    op.drop_column("messages", "from_instance_id")
    op.drop_column("messages", "agent_id")

    # Recreate old indexes
    op.create_index(
        "idx_messages_sender_role",
        "messages",
        ["sender_role"],
        postgresql_where="sender_role IS NOT NULL",
    )
    op.create_index(
        "idx_messages_sender_id",
        "messages",
        ["sender_id"],
        postgresql_where="sender_id IS NOT NULL",
    )
