"""fix projects path unique constraint for soft deletes

Revision ID: fix_path_constraint
Revises: 20260121_1600_refactor_message_sender_fields
Create Date: 2026-01-21 11:32:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fix_path_constraint"
down_revision: Union[str, None] = "0cd45723ec3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace the simple unique constraint on projects.path with a partial unique index
    that only applies to non-deleted projects.

    This allows the same path to be reused after a project is soft-deleted.
    """
    # Drop the existing unique constraint on path
    op.drop_constraint("projects_path_key", "projects", type_="unique")

    # Create a partial unique index that only applies to non-deleted projects
    op.create_index(
        "idx_projects_path_unique",
        "projects",
        ["path"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """
    Revert to the simple unique constraint.

    WARNING: This will fail if there are soft-deleted projects with duplicate paths.
    """
    # Drop the partial unique index
    op.drop_index("idx_projects_path_unique", table_name="projects")

    # Recreate the simple unique constraint
    op.create_unique_constraint("projects_path_key", "projects", ["path"])
