"""add_team_member_ids_to_projects

Revision ID: add_team_member_ids
Revises: abc123def456
Create Date: 2026-01-24 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_team_member_ids"
down_revision: Union[str, None] = "abc123def456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add team_member_ids column to projects table
    op.add_column(
        "projects",
        sa.Column("team_member_ids", postgresql.ARRAY(sa.String(255)), nullable=True),
    )


def downgrade() -> None:
    # Drop team_member_ids column
    op.drop_column("projects", "team_member_ids")
