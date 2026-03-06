"""add cli_backend to sessions

Revision ID: 20260305_0000
Revises: 20260130_0000
Create Date: 2026-03-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_0000"
down_revision: Union[str, None] = "20260130_0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cli_backend column to sessions table."""
    op.add_column(
        "sessions",
        sa.Column(
            "cli_backend",
            sa.String(50),
            nullable=False,
            server_default="claude",
        ),
    )


def downgrade() -> None:
    """Remove cli_backend column from sessions table."""
    op.drop_column("sessions", "cli_backend")
