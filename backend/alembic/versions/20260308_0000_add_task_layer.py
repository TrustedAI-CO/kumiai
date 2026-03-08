"""Add task layer: tasks table and task_id on sessions

Revision ID: add_task_layer_20260308
Revises: 20260305_add_cli_backend
Create Date: 2026-03-08 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_task_layer_20260308"
down_revision: Union[str, None] = "20260130_0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="open"
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_tasks_project_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(trim(name)) > 0", name="chk_tasks_name_not_empty"),
    )
    op.create_index(
        "idx_tasks_project_id",
        "tasks",
        ["project_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_tasks_status",
        "tasks",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_tasks_deleted_at", "tasks", ["deleted_at"])

    op.add_column(
        "sessions",
        sa.Column("task_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sessions_task_id",
        "sessions",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_sessions_task_id",
        "sessions",
        ["task_id"],
        postgresql_where=sa.text("task_id IS NOT NULL AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_sessions_task_id", table_name="sessions")
    op.drop_constraint("fk_sessions_task_id", "sessions", type_="foreignkey")
    op.drop_column("sessions", "task_id")

    op.drop_index("idx_tasks_deleted_at", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_index("idx_tasks_project_id", table_name="tasks")
    op.drop_table("tasks")
