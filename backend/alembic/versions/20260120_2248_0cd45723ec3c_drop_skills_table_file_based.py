"""drop_skills_table_file_based

Skills are now stored as files following Claude SDK format:
  /data/skills/{skill-id}/SKILL.md (with YAML frontmatter)

This migration drops the `skills` table and all related indexes.

Revision ID: 0cd45723ec3c
Revises: 49faaf1fafb
Create Date: 2026-01-20 22:48:33.766832

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0cd45723ec3c"
down_revision: Union[str, None] = "49faaf1fafb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop skills table - skills are now file-based."""
    # Drop indexes first
    op.drop_index("idx_skills_deleted_at", table_name="skills", if_exists=True)
    op.drop_index(
        "idx_skills_tags", table_name="skills", if_exists=True, postgresql_using="gin"
    )
    op.drop_index("idx_skills_name", table_name="skills", if_exists=True)

    # Drop table
    op.drop_table("skills")


def downgrade() -> None:
    """Recreate skills table (for rollback purposes only)."""
    # Note: This recreates the table structure but will not restore data
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column(
            "tags", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Recreate indexes
    op.create_index(
        "idx_skills_name",
        "skills",
        ["name"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_skills_tags",
        "skills",
        ["tags"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
        postgresql_using="gin",
    )
    op.create_index("idx_skills_deleted_at", "skills", ["deleted_at"], unique=False)
