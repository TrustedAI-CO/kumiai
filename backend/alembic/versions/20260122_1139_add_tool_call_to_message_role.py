"""add tool_call to message_role enum

Revision ID: add_tool_call_role
Revises:
Create Date: 2026-01-22

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "add_tool_call_role"
down_revision = None  # Will be set by alembic
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'tool_call' to message_role enum
    op.execute("ALTER TYPE message_role ADD VALUE IF NOT EXISTS 'tool_call'")


def downgrade() -> None:
    # Cannot remove enum value in PostgreSQL
    # Would need to recreate the enum type
    pass
