"""Unit tests for SessionService (with mocked repositories)."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.application.dtos.requests import CreateSessionRequest
from app.application.services.exceptions import (
    InvalidSessionStateError,
    ProjectNotFoundError,
    SessionNotFoundError,
)
from app.application.services.session_service import SessionService
from app.core.exceptions import ValidationError
from app.domain.entities import Session
from app.domain.value_objects import SessionStatus, SessionType


@pytest.fixture
def session_service():
    """Session service with mocked dependencies."""
    return SessionService(
        session_repo=AsyncMock(),
        project_repo=AsyncMock(),
        agent_repo=AsyncMock(),
    )


class TestSessionServiceCreate:
    """Test session creation."""

    async def test_create_session_success(self, session_service):
        """Test creating a session successfully."""
        # Setup mocks
        agent_id = "test-agent"
        session_service._session_repo.create.return_value = Session(
            id=uuid4(),
            agent_id=agent_id,
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INITIALIZING,
        )

        request = CreateSessionRequest(
            agent_id=agent_id,
            session_type="specialist",
        )

        result = await session_service.create_session(request)

        assert result.agent_id == agent_id
        assert result.session_type == "specialist"
        assert result.status == "initializing"
        session_service._session_repo.create.assert_called_once()

    async def test_create_pm_session_without_project(self, session_service):
        """Test creating PM session without project raises error."""
        agent_id = "test-pm-agent"

        with pytest.raises(ValidationError) as exc:
            await session_service.create_session(
                CreateSessionRequest(
                    agent_id=agent_id,
                    session_type="pm",
                    # Missing project_id
                )
            )

        assert "PM sessions must have a project_id" in str(exc.value)

    async def test_create_pm_session_project_not_found(self, session_service):
        """Test creating PM session with non-existent project."""
        agent_id = "test-pm-agent"
        project_id = uuid4()
        session_service._project_repo.get_by_id.return_value = None

        with pytest.raises(ProjectNotFoundError) as exc:
            await session_service.create_session(
                CreateSessionRequest(
                    agent_id=agent_id,
                    project_id=project_id,
                    session_type="pm",
                )
            )

        assert "Project" in str(exc.value)
        assert "not found" in str(exc.value)

    async def test_create_pm_session_success(self, session_service):
        """Test creating PM session with valid project."""
        agent_id = "test-pm-agent"
        project_id = uuid4()
        session_id = uuid4()

        session_service._project_repo.get_by_id.return_value = Mock(id=project_id)
        session_service._session_repo.create.return_value = Session(
            id=session_id,
            agent_id=agent_id,
            project_id=project_id,
            session_type=SessionType.PM,
            status=SessionStatus.INITIALIZING,
        )

        request = CreateSessionRequest(
            agent_id=agent_id,
            project_id=project_id,
            session_type="pm",
        )

        result = await session_service.create_session(request)

        assert result.id == session_id
        assert result.agent_id == agent_id
        assert result.project_id == project_id
        assert result.session_type == "pm"
        session_service._project_repo.get_by_id.assert_called_once_with(project_id)

    async def test_create_session_with_context(self, session_service):
        """Test creating session with custom context."""
        agent_id = "test-assistant-agent"
        context = {"custom": "data", "key": "value"}

        session_service._session_repo.create.return_value = Session(
            id=uuid4(),
            agent_id=agent_id,
            project_id=None,
            session_type=SessionType.ASSISTANT,
            status=SessionStatus.INITIALIZING,
            context=context,
        )

        request = CreateSessionRequest(
            agent_id=agent_id,
            session_type="assistant",
            context=context,
        )

        result = await session_service.create_session(request)

        assert result.context == context


class TestSessionServiceGet:
    """Test getting sessions."""

    async def test_get_session_success(self, session_service):
        """Test getting existing session."""
        session_id = uuid4()
        session_service._session_repo.get_by_id.return_value = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )

        result = await session_service.get_session(session_id)

        assert result.id == session_id
        session_service._session_repo.get_by_id.assert_called_once_with(session_id)

    async def test_get_session_not_found(self, session_service):
        """Test getting non-existent session."""
        session_id = uuid4()
        session_service._session_repo.get_by_id.return_value = None

        with pytest.raises(SessionNotFoundError) as exc:
            await session_service.get_session(session_id)

        assert "Session" in str(exc.value)
        assert "not found" in str(exc.value)


class TestSessionServiceList:
    """Test listing sessions."""

    async def test_list_sessions_all_active(self, session_service):
        """Test listing all active sessions."""
        sessions = [
            Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=SessionStatus.IDLE,
            ),
            Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.ASSISTANT,
                status=SessionStatus.THINKING,
            ),
        ]
        session_service._session_repo.get_active_sessions.return_value = sessions

        result = await session_service.list_sessions()

        assert len(result) == 2
        session_service._session_repo.get_active_sessions.assert_called_once()

    async def test_list_sessions_by_project(self, session_service):
        """Test listing sessions filtered by project."""
        project_id = uuid4()
        sessions = [
            Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=project_id,
                session_type=SessionType.PM,
                status=SessionStatus.IDLE,
            ),
        ]
        session_service._session_repo.get_by_project_id.return_value = sessions

        result = await session_service.list_sessions(project_id=project_id)

        assert len(result) == 1
        assert result[0].project_id == project_id
        session_service._session_repo.get_by_project_id.assert_called_once_with(
            project_id
        )

    async def test_list_sessions_by_status(self, session_service):
        """Test listing sessions filtered by status."""
        sessions = [
            Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=SessionStatus.COMPLETED,
            ),
        ]
        session_service._session_repo.get_by_status.return_value = sessions

        result = await session_service.list_sessions(status="completed")

        assert len(result) == 1
        assert result[0].status == "completed"
        session_service._session_repo.get_by_status.assert_called_once()


class TestSessionServiceLifecycle:
    """Test session lifecycle methods."""

    async def test_start_session_success(self, session_service):
        """Test starting a session."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.start_session(session_id)

        assert result.status == "thinking"
        session_service._session_repo.update.assert_called_once()

    async def test_start_session_not_found(self, session_service):
        """Test starting non-existent session."""
        session_id = uuid4()
        session_service._session_repo.get_by_id.return_value = None

        with pytest.raises(SessionNotFoundError):
            await session_service.start_session(session_id)

    async def test_start_session_invalid_state(self, session_service):
        """Test starting session from invalid state."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.COMPLETED,  # Can't start from completed
        )
        session_service._session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidSessionStateError):
            await session_service.start_session(session_id)

    async def test_complete_session_success(self, session_service):
        """Test completing a session."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.complete_session(session_id)

        assert result.status == "completed"
        session_service._session_repo.update.assert_called_once()

    async def test_fail_session_success(self, session_service):
        """Test marking session as failed."""
        session_id = uuid4()
        error_msg = "Something went wrong"
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.THINKING,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.fail_session(session_id, error_msg)

        assert result.status == "error"
        assert result.error_message == error_msg
        session_service._session_repo.update.assert_called_once()

    async def test_interrupt_session_success(self, session_service):
        """Test interrupting a running session."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.interrupt_session(session_id)

        assert result.status == "interrupted"
        session_service._session_repo.update.assert_called_once()

    async def test_interrupt_session_invalid_state(self, session_service):
        """Test interrupting session from non-working state."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,  # Can't interrupt idle session
        )
        session_service._session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidSessionStateError):
            await session_service.interrupt_session(session_id)

    async def test_resume_session_success(self, session_service):
        """Test resuming a completed session."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.COMPLETED,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.resume_session(session_id)

        assert result.status == "idle"
        assert result.error_message is None
        session_service._session_repo.update.assert_called_once()

    async def test_resume_interrupted_session_success(self, session_service):
        """Test resuming an interrupted session."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INTERRUPTED,
        )
        session_service._session_repo.get_by_id.return_value = session
        session_service._session_repo.update.return_value = session

        result = await session_service.resume_session(session_id)

        assert result.status == "idle"
        assert result.error_message is None
        session_service._session_repo.update.assert_called_once()

    async def test_resume_session_invalid_state(self, session_service):
        """Test resuming session from non-terminal state."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.THINKING,  # Can't resume active session
        )
        session_service._session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidSessionStateError):
            await session_service.resume_session(session_id)


class TestSessionServiceDelete:
    """Test session deletion."""

    async def test_delete_session_success(self, session_service):
        """Test deleting a session."""
        session_id = uuid4()
        session_service._session_repo.exists.return_value = True
        session_service._session_repo.delete.return_value = None

        await session_service.delete_session(session_id)

        session_service._session_repo.exists.assert_called_once_with(session_id)
        session_service._session_repo.delete.assert_called_once_with(session_id)

    async def test_delete_session_not_found(self, session_service):
        """Test deleting non-existent session."""
        session_id = uuid4()
        session_service._session_repo.exists.return_value = False

        with pytest.raises(SessionNotFoundError):
            await session_service.delete_session(session_id)
