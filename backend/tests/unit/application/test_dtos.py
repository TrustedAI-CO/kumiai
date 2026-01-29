"""Tests for DTOs."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.dtos.requests import (
    AssignPMRequest,
    CreateProjectRequest,
    CreateSessionRequest,
    ExecuteQueryRequest,
    UpdateProjectRequest,
)
from app.application.dtos.session_dto import SessionDTO
from app.application.dtos.project_dto import ProjectDTO
from app.application.dtos.message_dto import MessageDTO
from app.application.dtos.skill_dto import SkillDTO
from app.domain.entities import Session, Project, Message, Skill
from app.domain.value_objects import SessionStatus, SessionType, MessageRole


class TestCreateSessionRequest:
    """Test CreateSessionRequest validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid session creation request with all fields."""
        request = CreateSessionRequest(
            agent_id="test-agent",
            project_id=uuid4(),
            session_type="pm",
            context={"key": "value"},
        )

        assert request.session_type == "pm"
        assert request.context == {"key": "value"}
        assert request.project_id is not None

    def test_valid_request_minimal_fields(self):
        """Test valid request with minimal fields."""
        request = CreateSessionRequest(
            agent_id="test-agent",
            session_type="specialist",
        )

        assert request.session_type == "specialist"
        assert request.context == {}
        assert request.project_id is None

    def test_invalid_session_type(self):
        """Test invalid session type raises validation error."""
        with pytest.raises(ValidationError) as exc:
            CreateSessionRequest(
                agent_id="test-agent",
                session_type="invalid",
            )

        assert "session_type must be one of" in str(exc.value)

    def test_all_valid_session_types(self):
        """Test all valid session types are accepted."""
        valid_types = ["pm", "specialist", "assistant"]

        for session_type in valid_types:
            request = CreateSessionRequest(
                agent_id="test-agent",
                session_type=session_type,
            )
            assert request.session_type == session_type

    def test_context_defaults_to_empty_dict(self):
        """Test context defaults to empty dict when None."""
        request = CreateSessionRequest(
            agent_id="test-agent",
            session_type="pm",
            context=None,
        )

        assert request.context == {}


class TestExecuteQueryRequest:
    """Test ExecuteQueryRequest validation."""

    def test_valid_request(self):
        """Test valid execute query request."""
        request = ExecuteQueryRequest(
            query="What is the status of the project?",
            stream=True,
        )

        assert request.query == "What is the status of the project?"
        assert request.stream is True

    def test_stream_defaults_to_true(self):
        """Test stream defaults to True."""
        request = ExecuteQueryRequest(query="test query")

        assert request.stream is True

    def test_empty_query_fails(self):
        """Test empty query raises validation error."""
        with pytest.raises(ValidationError):
            ExecuteQueryRequest(query="")

    def test_query_too_long_fails(self):
        """Test query exceeding max length fails."""
        with pytest.raises(ValidationError):
            ExecuteQueryRequest(query="a" * 10001)


class TestCreateProjectRequest:
    """Test CreateProjectRequest validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid project creation request."""
        request = CreateProjectRequest(
            name="My Project",
            description="Project description",
            path="/path/to/project",
            pm_agent_id="test-agent",
        )

        assert request.name == "My Project"
        assert request.description == "Project description"
        assert request.pm_agent_id is not None

    def test_valid_request_minimal_fields(self):
        """Test valid request with minimal fields."""
        request = CreateProjectRequest(
            name="My Project",
            path="/path/to/project",
        )

        assert request.description is None
        assert request.pm_agent_id is None

    def test_empty_name_fails(self):
        """Test empty name raises validation error."""
        with pytest.raises(ValidationError):
            CreateProjectRequest(
                name="",
                path="/path/to/project",
            )

    def test_name_too_long_fails(self):
        """Test name exceeding max length fails."""
        with pytest.raises(ValidationError):
            CreateProjectRequest(
                name="a" * 256,
                path="/path/to/project",
            )

    def test_description_too_long_fails(self):
        """Test description exceeding max length fails."""
        with pytest.raises(ValidationError):
            CreateProjectRequest(
                name="Project",
                path="/path/to/project",
                description="a" * 1001,
            )


class TestUpdateProjectRequest:
    """Test UpdateProjectRequest validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid update request."""
        request = UpdateProjectRequest(
            name="Updated Name",
            description="Updated description",
            path="/new/path",
        )

        assert request.name == "Updated Name"
        assert request.description == "Updated description"
        assert request.path == "/new/path"

    def test_valid_request_with_no_fields(self):
        """Test valid request with no fields (all None)."""
        request = UpdateProjectRequest()

        assert request.name is None
        assert request.description is None
        assert request.path is None

    def test_valid_request_with_partial_fields(self):
        """Test valid request with some fields."""
        request = UpdateProjectRequest(name="New Name")

        assert request.name == "New Name"
        assert request.description is None


class TestAssignPMRequest:
    """Test AssignPMRequest validation."""

    def test_valid_request(self):
        """Test valid assign PM request."""
        pm_id = "test-pm-agent"
        request = AssignPMRequest(pm_agent_id=pm_id)

        assert request.pm_agent_id == pm_id

    def test_missing_pm_agent_id_fails(self):
        """Test missing pm_agent_id raises validation error."""
        with pytest.raises(ValidationError):
            AssignPMRequest()


# NOTE: TestCreateCharacterRequest and TestUpdateCharacterRequest removed - Characters are now file-based (agents)


class TestSessionDTO:
    """Test SessionDTO conversion."""

    def test_from_entity_with_all_fields(self):
        """Test converting entity to DTO with all fields."""
        entity = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=uuid4(),
            session_type=SessionType.PM,
            status=SessionStatus.IDLE,
            claude_session_id="claude-123",
            context={"key": "value"},
            error_message="Test error",
        )

        dto = SessionDTO.from_entity(entity)

        assert dto.id == entity.id
        assert dto.agent_id == entity.agent_id
        assert dto.project_id == entity.project_id
        assert dto.session_type == "pm"
        assert dto.status == "idle"
        assert dto.claude_session_id == "claude-123"
        assert dto.context == {"key": "value"}
        assert dto.error_message == "Test error"

    def test_from_entity_with_minimal_fields(self):
        """Test converting entity with minimal fields."""
        entity = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INITIALIZING,
        )

        dto = SessionDTO.from_entity(entity)

        assert dto.project_id is None
        assert dto.claude_session_id is None
        assert dto.error_message is None
        assert dto.context == {}

    def test_from_entity_enum_conversion(self):
        """Test enum values are properly converted to strings."""
        entity = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )

        dto = SessionDTO.from_entity(entity)

        assert dto.session_type == "specialist"
        assert dto.status == "working"
        assert isinstance(dto.session_type, str)
        assert isinstance(dto.status, str)


class TestProjectDTO:
    """Test ProjectDTO conversion."""

    def test_from_entity_with_all_fields(self):
        """Test converting entity to DTO."""
        entity = Project(
            id=uuid4(),
            name="Test Project",
            description="Test description",
            path="/projects/test",
            pm_agent_id="test-agent",
            pm_session_id=uuid4(),
        )

        dto = ProjectDTO.from_entity(entity)

        assert dto.id == entity.id
        assert dto.name == entity.name
        assert dto.description == entity.description
        assert dto.path == entity.path
        assert dto.pm_agent_id == entity.pm_agent_id
        assert dto.pm_session_id == entity.pm_session_id

    def test_from_entity_without_pm(self):
        """Test converting entity without PM assigned."""
        entity = Project(
            id=uuid4(),
            name="Test Project",
            description=None,
            path="/projects/test",
        )

        dto = ProjectDTO.from_entity(entity)

        assert dto.pm_agent_id is None
        assert dto.pm_session_id is None
        assert dto.description is None


# NOTE: TestCharacterDTO removed - Characters are now file-based (agents)


class TestMessageDTO:
    """Test MessageDTO conversion."""

    def test_from_entity_with_all_fields(self):
        """Test converting entity to DTO."""
        entity = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test message",
            metadata={"tokens": 100},
        )

        dto = MessageDTO.from_entity(entity)

        assert dto.id == entity.id
        assert (
            dto.instance_id == entity.session_id
        )  # DTO uses instance_id, not session_id
        assert dto.role == "user"
        assert dto.content == entity.content
        assert dto.metadata == {"tokens": 100}

    def test_from_entity_enum_conversion(self):
        """Test enum values are properly converted."""
        entity = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.ASSISTANT,
            content="Assistant response",
        )

        dto = MessageDTO.from_entity(entity)

        assert dto.role == "assistant"
        assert isinstance(dto.role, str)


class TestSkillDTO:
    """Test SkillDTO conversion."""

    def test_from_entity_with_all_fields(self):
        """Test converting entity to DTO."""
        entity = Skill(
            id="python-expert",
            name="Python Expert",
            description="Expert in Python programming",
            file_path="/skills/python-expert/",
            tags=["python", "coding", "backend"],
            icon="code",
            icon_color="#3776AB",
        )

        dto = SkillDTO.from_entity(entity)

        assert dto.id == entity.id
        assert dto.name == entity.name
        assert dto.description == entity.description
        assert dto.file_path == entity.file_path
        assert dto.tags == ["python", "coding", "backend"]
        assert dto.icon == "code"
        assert dto.icon_color == "#3776AB"

    def test_from_entity_without_description(self):
        """Test converting entity without description."""
        entity = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill/",
            tags=["test"],
        )

        dto = SkillDTO.from_entity(entity)

        assert dto.description is None
        assert dto.tags == ["test"]
        assert dto.icon == "zap"  # Default icon
        assert dto.icon_color == "#4A90E2"  # Default color
