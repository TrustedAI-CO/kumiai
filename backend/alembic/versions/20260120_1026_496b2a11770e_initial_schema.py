"""Initial schema

Revision ID: 496b2a11770e
Revises:
Create Date: 2026-01-20 10:26:31.123456

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "496b2a11770e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types only if they don't exist
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_type') THEN
                CREATE TYPE session_type AS ENUM ('pm', 'orchestrator', 'specialist', 'assistant');
            END IF;
        END$$;
    """
        )
    )
    conn.execute(
        sa.text(
            """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status') THEN
                CREATE TYPE session_status AS ENUM ('initializing', 'idle', 'thinking', 'working', 'waiting', 'completed', 'error', 'cancelled');
            END IF;
        END$$;
    """
        )
    )
    conn.execute(
        sa.text(
            """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role') THEN
                CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system', 'tool_result');
            END IF;
        END$$;
    """
        )
    )
    conn.execute(
        sa.text(
            """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type') THEN
                CREATE TYPE event_type AS ENUM ('session_created', 'session_started', 'session_completed', 'session_failed', 'message_sent', 'tool_executed', 'project_created', 'project_updated');
            END IF;
        END$$;
    """
        )
    )

    # Create characters table (no dependencies)
    op.create_table(
        "characters",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="chk_characters_name_not_empty"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_characters_deleted_at", "characters", ["deleted_at"])
    op.create_index(
        "idx_characters_name",
        "characters",
        ["name"],
        postgresql_where="deleted_at IS NULL",
    )
    op.create_index(
        "idx_characters_role",
        "characters",
        ["role"],
        postgresql_where="deleted_at IS NULL",
    )

    # Create projects table WITHOUT pm_session_id foreign key (circular dependency)
    op.create_table(
        "projects",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pm_character_id", sa.UUID(), nullable=True),
        sa.Column("pm_session_id", sa.UUID(), nullable=True),  # FK added later
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="chk_projects_name_not_empty"
        ),
        sa.CheckConstraint(
            "length(trim(path)) > 0", name="chk_projects_path_not_empty"
        ),
        sa.ForeignKeyConstraint(
            ["pm_character_id"], ["characters.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )
    op.create_index("idx_projects_deleted_at", "projects", ["deleted_at"])
    op.create_index(
        "idx_projects_name", "projects", ["name"], postgresql_where="deleted_at IS NULL"
    )
    op.create_index(
        "idx_projects_pm_character_id",
        "projects",
        ["pm_character_id"],
        postgresql_where="deleted_at IS NULL",
    )

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("character_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column(
            "session_type",
            sa.Enum(
                "pm",
                "orchestrator",
                "specialist",
                "assistant",
                name="session_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "initializing",
                "idle",
                "thinking",
                "working",
                "waiting",
                "completed",
                "error",
                "cancelled",
                name="session_status",
                create_type=False,
            ),
            server_default="initializing",
            nullable=False,
        ),
        sa.Column("claude_session_id", sa.String(length=255), nullable=True),
        sa.Column("context", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["character_id"], ["characters.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sessions_character_id",
        "sessions",
        ["character_id"],
        postgresql_where="deleted_at IS NULL",
    )
    op.create_index(
        "idx_sessions_created_at",
        "sessions",
        [sa.text("created_at DESC")],
        postgresql_where="deleted_at IS NULL",
    )
    op.create_index("idx_sessions_deleted_at", "sessions", ["deleted_at"])
    op.create_index(
        "idx_sessions_project_id",
        "sessions",
        ["project_id"],
        postgresql_where="deleted_at IS NULL",
    )
    op.create_index(
        "idx_sessions_status",
        "sessions",
        ["status"],
        postgresql_where="deleted_at IS NULL",
    )

    # Now add the circular foreign key constraint
    op.create_foreign_key(
        "fk_projects_pm_session_id",
        "projects",
        "sessions",
        ["pm_session_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "assistant",
                "system",
                "tool_result",
                name="message_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_use_id", sa.String(length=255), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("sequence >= 0", name="chk_messages_sequence_non_negative"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_session_id_sequence", "messages", ["session_id", "sequence"]
    )
    op.create_index("idx_messages_created_at", "messages", [sa.text("created_at DESC")])
    op.create_index(
        "idx_messages_tool_use_id",
        "messages",
        ["tool_use_id"],
        postgresql_where="tool_use_id IS NOT NULL",
    )

    # Create skills table
    op.create_table(
        "skills",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
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
    op.create_index("idx_skills_deleted_at", "skills", ["deleted_at"])
    op.create_index(
        "idx_skills_name", "skills", ["name"], postgresql_where="deleted_at IS NULL"
    )
    op.create_index(
        "idx_skills_tags",
        "skills",
        ["tags"],
        postgresql_where="deleted_at IS NULL",
        postgresql_using="gin",
    )

    # Create activity_logs table
    op.create_table(
        "activity_logs",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "session_created",
                "session_started",
                "session_completed",
                "session_failed",
                "message_sent",
                "tool_executed",
                "project_created",
                "project_updated",
                name="event_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "event_data", postgresql.JSONB(), server_default="{}", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_activity_logs_session_id", "activity_logs", ["session_id"])
    op.create_index("idx_activity_logs_event_type", "activity_logs", ["event_type"])
    op.create_index(
        "idx_activity_logs_created_at", "activity_logs", [sa.text("created_at DESC")]
    )

    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("settings", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create singleton constraint using expression index
    op.execute("CREATE UNIQUE INDEX idx_user_profiles_singleton ON user_profiles ((1))")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("user_profiles")
    op.drop_table("activity_logs")
    op.drop_table("messages")
    op.drop_table("skills")

    # Drop circular foreign key first
    op.drop_constraint("fk_projects_pm_session_id", "projects", type_="foreignkey")

    op.drop_table("sessions")
    op.drop_table("projects")
    op.drop_table("characters")

    # Drop ENUM types
    event_type_enum.drop(op.get_bind(), checkfirst=True)
    message_role_enum.drop(op.get_bind(), checkfirst=True)
    session_status_enum.drop(op.get_bind(), checkfirst=True)
    session_type_enum.drop(op.get_bind(), checkfirst=True)
