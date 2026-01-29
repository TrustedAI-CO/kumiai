"""drop character table

Revision ID: drop_character_table
Revises: ddecbf33ef2e
Create Date: 2026-01-22 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "drop_character_table"
down_revision: Union[str, None] = "ddecbf33ef2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop the characters table.

    The Character model is no longer needed as we've adopted a file-based
    agent model where all agent configuration (including tools, MCPs, skills)
    is stored in CLAUDE.md YAML frontmatter.
    """
    # Drop the characters table
    op.drop_table("characters")


def downgrade() -> None:
    """
    Recreate the characters table.

    This is for rollback purposes only. The table structure is preserved
    from the original schema.
    """
    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
