"""add_sender_fields_to_messages

Add sender attribution fields to messages table for proper message rendering.

This migration adds:
- sender_role: VARCHAR(50) - Role of sender ('user', 'pm', 'orchestrator', 'specialist', 'system')
- sender_id: VARCHAR(255) - Character/Agent ID of sender
- sender_name: VARCHAR(255) - Display name of sender
- sender_instance: VARCHAR(255) - Session instance ID of sender
- agent_name: VARCHAR(255) - For specialist messages (legacy compatibility)

Revision ID: abc456def789
Revises: 5d55bfcf3778
Create Date: 2026-01-21 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "abc456def789"
down_revision: Union[str, None] = "5d55bfcf3778"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add sender attribution fields to messages table."""

    # Add sender attribution columns
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
    op.add_column(
        "messages", sa.Column("agent_name", sa.String(length=255), nullable=True)
    )

    # Create indexes for common query patterns
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


def downgrade() -> None:
    """Remove sender attribution fields from messages table."""

    # Drop indexes
    op.drop_index("idx_messages_sender_id", table_name="messages")
    op.drop_index("idx_messages_sender_role", table_name="messages")

    # Drop columns
    op.drop_column("messages", "agent_name")
    op.drop_column("messages", "sender_instance")
    op.drop_column("messages", "sender_name")
    op.drop_column("messages", "sender_id")
    op.drop_column("messages", "sender_role")
