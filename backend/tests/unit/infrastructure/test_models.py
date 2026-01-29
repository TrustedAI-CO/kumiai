"""Tests for database models."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    Project,
    Session,
    Message,
    ActivityLog,
    UserProfile,
)

# NOTE: Skill model removed - Skills are now file-based
from app.domain.value_objects import (
    SessionType,
    SessionStatus,
    MessageRole,
    EventType,
)


# NOTE: TestCharacter removed - Characters are now file-based (agents)


class TestProject:
    """Tests for Project model."""

    async def test_create_project(self, db_session: AsyncSession):
        """Test creating a project."""
        agent_id = "test-pm-agent"
        proj = Project(
            name="Test Project",
            description="A test project",
            pm_agent_id=agent_id,
            path="/test/projects/test",
        )
        db_session.add(proj)
        await db_session.commit()
        await db_session.refresh(proj)

        assert proj.id is not None
        assert proj.name == "Test Project"
        assert proj.description == "A test project"
        assert proj.pm_agent_id == agent_id
        assert proj.created_at is not None

    async def test_project_unique_path(
        self, db_session: AsyncSession, project: Project
    ):
        """Test project path uniqueness constraint."""
        duplicate = Project(
            name="Another Project",
            path=project.path,  # Same path
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


class TestSession:
    """Tests for Session model."""

    async def test_create_session(self, db_session: AsyncSession, project: Project):
        """Test creating a session."""
        agent_id = "test-agent"
        sess = Session(
            agent_id=agent_id,
            project_id=project.id,
            session_type=SessionType.PM.value,
            status=SessionStatus.IDLE.value,
            context={"key": "value"},
        )
        db_session.add(sess)
        await db_session.commit()
        await db_session.refresh(sess)

        assert sess.id is not None
        assert sess.agent_id == agent_id
        assert sess.project_id == project.id
        assert sess.session_type == SessionType.PM.value
        assert sess.status == SessionStatus.IDLE.value
        assert sess.context == {"key": "value"}
        assert sess.created_at is not None

    async def test_session_default_status(self, db_session: AsyncSession):
        """Test session has default status of initializing."""
        agent_id = "test-specialist-agent"
        sess = Session(
            agent_id=agent_id,
            session_type=SessionType.SPECIALIST.value,
        )
        db_session.add(sess)
        await db_session.commit()
        await db_session.refresh(sess)

        assert sess.status == SessionStatus.INITIALIZING.value


class TestMessage:
    """Tests for Message model."""

    async def test_create_message(self, db_session: AsyncSession, session: Session):
        """Test creating a message."""
        msg = Message(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content="Hello, user!",
            sequence=1,
            meta={"tokens": 100},
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)

        assert msg.id is not None
        assert msg.session_id == session.id
        assert msg.role == MessageRole.ASSISTANT.value
        assert msg.content == "Hello, user!"
        assert msg.sequence == 1
        assert msg.meta == {"tokens": 100}

    async def test_message_sequence_order(
        self, db_session: AsyncSession, session: Session, message: Message
    ):
        """Test messages can be ordered by sequence."""
        # Create additional messages
        msg2 = Message(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content="Second message",
            sequence=1,
        )
        msg3 = Message(
            session_id=session.id,
            role=MessageRole.USER.value,
            content="Third message",
            sequence=2,
        )
        db_session.add_all([msg2, msg3])
        await db_session.commit()

        # Query messages by sequence
        result = await db_session.execute(
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.sequence)
        )
        messages = result.scalars().all()

        assert len(messages) == 3
        assert messages[0].sequence == 0
        assert messages[1].sequence == 1
        assert messages[2].sequence == 2


# NOTE: TestSkill removed - Skills are now file-based (not database-backed)


class TestActivityLog:
    """Tests for ActivityLog model."""

    async def test_create_activity_log(
        self, db_session: AsyncSession, session: Session
    ):
        """Test creating an activity log."""
        log = ActivityLog(
            session_id=session.id,
            event_type=EventType.MESSAGE_SENT.value,
            event_data={"message_id": "123", "tokens": 50},
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)

        assert log.id is not None
        assert log.session_id == session.id
        assert log.event_type == EventType.MESSAGE_SENT.value
        assert log.event_data == {"message_id": "123", "tokens": 50}
        assert log.created_at is not None


class TestUserProfile:
    """Tests for UserProfile model."""

    async def test_create_user_profile(self, db_session: AsyncSession):
        """Test creating a user profile."""
        profile = UserProfile(
            settings={"theme": "light", "notifications": True},
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert profile.settings == {"theme": "light", "notifications": True}
        assert profile.created_at is not None

    async def test_user_profile_singleton(
        self, db_session: AsyncSession, user_profile: UserProfile
    ):
        """Test user profile singleton constraint."""
        # Try to create a second profile - should fail due to singleton constraint
        second_profile = UserProfile(settings={})
        db_session.add(second_profile)

        with pytest.raises(Exception):  # IntegrityError from unique index
            await db_session.commit()
