"""add_interrupted_to_session_status

Revision ID: 72880b5715bb
Revises: 1b3ab1c8924e
Create Date: 2026-01-23 11:02:13.251266

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "72880b5715bb"
down_revision: Union[str, None] = "1b3ab1c8924e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'interrupted' value to session_status enum
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'interrupted'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex and risky
    # For production, consider creating a new migration instead
    pass
