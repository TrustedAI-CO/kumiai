"""SQLAlchemy database models.

Cross-database compatible models that work with both SQLite and PostgreSQL.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    TypeDecorator,
    func,
    text,
)
from sqlalchemy.types import CHAR
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import domain value objects for type hints and validation

Base = declarative_base()


# Cross-database compatible types
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type on PostgreSQL, otherwise uses CHAR(36)
    storing UUIDs as strings.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(GUID)
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, str):
                return UUID(value)
            return value


# Models
class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pm_agent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    pm_session_id: Mapped[Optional[UUID]] = mapped_column(
        GUID,
        ForeignKey(
            "sessions.id", name="fk_projects_pm_session_id", ondelete="SET NULL"
        ),
        nullable=True,
    )
    team_member_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON,  # Cross-database: JSON works on both SQLite and PostgreSQL
        nullable=True,
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    pm_session: Mapped[Optional["Session"]] = relationship(
        "Session", foreign_keys=[pm_session_id], post_update=True
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="chk_projects_name_not_empty"),
        CheckConstraint("length(trim(path)) > 0", name="chk_projects_path_not_empty"),
        Index("idx_projects_name", "name", postgresql_where="deleted_at IS NULL"),
        Index(
            "idx_projects_pm_agent_id",
            "pm_agent_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_projects_deleted_at", "deleted_at"),
        # Partial unique index: path must be unique only for non-deleted projects
        Index(
            "idx_projects_path_unique",
            "path",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )


class Session(Base):
    """Session/Agent Instance model."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        GUID,
        ForeignKey("projects.id", name="fk_sessions_project_id", ondelete="CASCADE"),
        nullable=True,
    )
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="initializing",
    )
    claude_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project", foreign_keys=[project_id], post_update=True
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        Index(
            "idx_sessions_agent_id",
            "agent_id",
            postgresql_where="deleted_at IS NULL AND agent_id IS NOT NULL",
        ),
        Index(
            "idx_sessions_project_id",
            "project_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_sessions_status", "status", postgresql_where="deleted_at IS NULL"),
        Index(
            "idx_sessions_created_at",
            text("created_at DESC"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("idx_sessions_deleted_at", "deleted_at"),
    )


class Message(Base):
    """Message model."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        GUID,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),  # Cross-database: use String instead of ENUM
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_use_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    meta: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Sender attribution fields
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_instance_id: Mapped[Optional[UUID]] = mapped_column(GUID, nullable=True)

    # Response grouping (for UI message bubbles)
    response_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    # Constraints
    __table_args__ = (
        CheckConstraint("sequence >= 0", name="chk_messages_sequence_non_negative"),
        # Note: Unique constraint on (session_id, sequence) was removed to eliminate race conditions
        # Messages are now ordered by created_at instead
        Index("idx_messages_session_id_sequence", "session_id", "sequence"),
        Index(
            "idx_messages_session_id_created_at", "session_id", text("created_at DESC")
        ),  # Composite index for get_by_session_ordered
        Index("idx_messages_created_at", text("created_at DESC")),
        Index(
            "idx_messages_tool_use_id",
            "tool_use_id",
            postgresql_where="tool_use_id IS NOT NULL",
        ),
        Index(
            "idx_messages_agent_id", "agent_id", postgresql_where="agent_id IS NOT NULL"
        ),
        Index(
            "idx_messages_from_instance_id",
            "from_instance_id",
            postgresql_where="from_instance_id IS NOT NULL",
        ),
        Index(
            "idx_messages_response_id",
            "response_id",
            postgresql_where="response_id IS NOT NULL",
        ),
    )


# NOTE: Skill model removed - Skills are now file-based (Claude SDK format)
# See: app/infrastructure/filesystem/skill_repository.py


class ActivityLog(Base):
    """Activity log model."""

    __tablename__ = "activity_logs"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        GUID,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session")

    # Constraints
    __table_args__ = (
        Index("idx_activity_logs_session_id", "session_id"),
        Index("idx_activity_logs_event_type", "event_type"),
        Index("idx_activity_logs_created_at", text("created_at DESC")),
    )


class UserProfile(Base):
    """User profile model (singleton table)."""

    __tablename__ = "user_profiles"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Singleton constraint (cross-database compatible)
    __table_args__ = (Index("idx_user_profiles_singleton", text("1"), unique=True),)


class SessionFile(Base):
    """File attachment model for chat sessions."""

    __tablename__ = "session_files"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        GUID,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[Optional[UUID]] = mapped_column(
        GUID,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extracted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="uploaded",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session")
    message: Mapped[Optional["Message"]] = relationship("Message")

    # Constraints
    __table_args__ = (
        CheckConstraint("file_size >= 0", name="chk_session_files_size_non_negative"),
        CheckConstraint(
            "length(trim(filename)) > 0", name="chk_session_files_filename_not_empty"
        ),
        Index("idx_session_files_session_id", "session_id"),
        Index(
            "idx_session_files_message_id",
            "message_id",
            postgresql_where="message_id IS NOT NULL",
        ),
        Index("idx_session_files_created_at", text("created_at DESC")),
        Index(
            "idx_session_files_file_hash",
            "file_hash",
            postgresql_where="file_hash IS NOT NULL",
        ),
    )
