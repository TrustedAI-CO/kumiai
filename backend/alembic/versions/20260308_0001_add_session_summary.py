"""Add summary column to sessions table

Revision ID: add_session_summary_20260308
Revises: add_task_layer_20260308
Create Date: 2026-03-08 00:01:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_session_summary_20260308"
down_revision: Union[str, None] = "291e73a4c1bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sessions", "summary")
