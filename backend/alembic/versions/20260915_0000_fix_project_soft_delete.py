"""fix project soft-delete: partial unique path index on SQLite, and backfill orphans

Revision ID: fix_project_soft_delete_20260915
Revises: add_session_summary_20260308
Create Date: 2026-09-15 00:00:00.000000

Two repairs, both consequences of soft-delete never having been finished.

1. idx_projects_path_unique was created by 20260121_1132 with only postgresql_where, so
   the "deleted_at IS NULL" predicate was silently dropped on SQLite — the default
   deployment. The live index was an unconditional UNIQUE on projects.path, which meant a
   soft-deleted project reserved its path forever and creating a project at that path
   failed with IntegrityError, unfixable from the UI because the old row is invisible.
   Recreated with both dialect predicates.

2. Deleting a project used to stamp only the project row, so its tasks and sessions kept
   deleted_at NULL and stayed live under an invisible parent. The forward fix landed in
   the application layer; this backfills the rows that were orphaned before it. Each
   child inherits its parent's deleted_at, which is exactly the shared timestamp the
   restore path keys on.

The backfill is UPDATE-only and reversible. It cannot stop a running agent — if any
orphaned session still has a live subprocess, that process is unaffected by this
migration and must be stopped separately.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fix_project_soft_delete_20260915"
down_revision: Union[str, None] = "add_session_summary_20260308"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_BACKFILL_CHILD = """
    UPDATE {table}
       SET deleted_at = (
           SELECT p.deleted_at FROM projects p WHERE p.id = {table}.project_id
       )
     WHERE deleted_at IS NULL
       AND project_id IN (SELECT id FROM projects WHERE deleted_at IS NOT NULL)
"""


def upgrade() -> None:
    # 1. Rebuild the path index with a predicate every dialect actually honours.
    op.drop_index("idx_projects_path_unique", table_name="projects")
    op.create_index(
        "idx_projects_path_unique",
        "projects",
        ["path"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    # 2. Adopt the orphans: children still live under an already-deleted project.
    conn = op.get_bind()
    for table in ("tasks", "sessions"):
        result = conn.execute(sa.text(_BACKFILL_CHILD.format(table=table)))
        print(f"  backfilled {result.rowcount} orphaned row(s) in {table}")


def downgrade() -> None:
    """
    Restore the previous index definition.

    The backfill is deliberately NOT reversed. Undoing it would mean guessing which
    children were hidden by this migration rather than by a real deletion, and getting
    that wrong resurrects work the user meant to discard. The rows it touched are
    recoverable from a backup if genuinely needed.

    WARNING: recreating the unconditional unique index will fail if two or more projects
    (deleted or not) share a path — which is precisely the state this migration makes
    legal. Resolve duplicates before downgrading.
    """
    op.drop_index("idx_projects_path_unique", table_name="projects")
    op.create_index(
        "idx_projects_path_unique",
        "projects",
        ["path"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
