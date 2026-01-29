"""Unit tests for entity-model mappers."""

from datetime import datetime
from uuid import uuid4


from app.domain.entities import (
    Message as MessageEntity,
    Project as ProjectEntity,
    Session as SessionEntity,
)
from app.domain.value_objects import MessageRole, SessionStatus, SessionType
from app.infrastructure.database.mappers import (
    MessageMapper,
    ProjectMapper,
    SessionMapper,
)
from app.infrastructure.database.models import Message, Project, Session

# NOTE: SkillMapper tests removed - Skills are now file-based


class TestSessionMapper:
    """Test SessionMapper bidirectional conversions."""

    def test_model_to_entity(self):
        """Test converting model to entity."""
        now = datetime.utcnow()
        model = Session(
            id=uuid4(),
            agent_id=uuid4(),
            project_id=uuid4(),
            session_type="pm",
            status="idle",
            claude_session_id="claude_abc123",
            context={"key": "value", "count": 42},
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        entity = SessionMapper.to_entity(model)

        assert entity.id == model.id
        assert entity.agent_id == model.agent_id
        assert entity.project_id == model.project_id
        assert entity.session_type == SessionType.PM
        assert entity.status == SessionStatus.IDLE
        assert entity.claude_session_id == "claude_abc123"
        assert entity.context == {"key": "value", "count": 42}
        assert entity.error_message is None
        assert entity.created_at == now
        assert entity.updated_at == now

    def test_entity_to_model(self):
        """Test converting entity to model."""
        now = datetime.utcnow()
        entity = SessionEntity(
            id=uuid4(),
            agent_id="test-agent",
            project_id=uuid4(),
            session_type=SessionType.PM,
            status=SessionStatus.IDLE,
            claude_session_id="claude_abc123",
            context={"key": "value"},
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        model = SessionMapper.to_model(entity)

        assert model.id == entity.id
        assert model.agent_id == entity.agent_id
        assert model.project_id == entity.project_id
        assert model.session_type == "pm"
        assert model.status == "idle"
        assert model.claude_session_id == "claude_abc123"
        assert model.context == {"key": "value"}
        assert model.error_message is None

    def test_entity_to_model_updates_existing(self):
        """Test converting entity updates existing model."""
        existing_model = Session(id=uuid4())
        entity = SessionEntity(
            id=existing_model.id,
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )

        updated_model = SessionMapper.to_model(entity, existing_model)

        assert updated_model is existing_model  # Same object
        assert updated_model.id == entity.id
        assert updated_model.status == "working"
        assert updated_model.project_id is None

    def test_model_to_entity_with_none_context(self):
        """Test converting model with None context to entity."""
        model = Session(
            id=uuid4(),
            agent_id=uuid4(),
            project_id=None,
            session_type="specialist",
            status="initializing",
            context=None,  # None in DB
        )

        entity = SessionMapper.to_entity(model)

        assert entity.context == {}  # Converted to empty dict

    def test_roundtrip_conversion(self):
        """Test entity -> model -> entity preserves data."""
        original = SessionEntity(
            id=uuid4(),
            agent_id="test-specialist",
            project_id=uuid4(),
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
            context={"nested": {"data": [1, 2, 3]}},
            error_message="Test error",
        )

        model = SessionMapper.to_model(original)
        recovered = SessionMapper.to_entity(model)

        assert recovered.id == original.id
        assert recovered.agent_id == original.agent_id
        assert recovered.session_type == original.session_type
        assert recovered.status == original.status
        assert recovered.context == original.context
        assert recovered.error_message == original.error_message


class TestProjectMapper:
    """Test ProjectMapper bidirectional conversions."""

    def test_model_to_entity(self):
        """Test converting model to entity."""
        now = datetime.utcnow()
        model = Project(
            id=uuid4(),
            name="Test Project",
            description="Project description",
            pm_agent_id=uuid4(),
            pm_session_id=uuid4(),
            path="/path/to/project",
            created_at=now,
            updated_at=now,
        )

        entity = ProjectMapper.to_entity(model)

        assert entity.id == model.id
        assert entity.name == "Test Project"
        assert entity.description == "Project description"
        assert entity.pm_agent_id == model.pm_agent_id
        assert entity.pm_session_id == model.pm_session_id
        assert entity.path == "/path/to/project"

    def test_entity_to_model(self):
        """Test converting entity to model."""
        entity = ProjectEntity(
            id=uuid4(),
            name="My Project",
            description=None,
            pm_agent_id=None,
            pm_session_id=None,
            path="/workspace/myproject",
        )

        model = ProjectMapper.to_model(entity)

        assert model.id == entity.id
        assert model.name == "My Project"
        assert model.description is None
        assert model.pm_agent_id is None
        assert model.pm_session_id is None
        assert model.path == "/workspace/myproject"

    def test_roundtrip_conversion(self):
        """Test entity -> model -> entity preserves data."""
        original = ProjectEntity(
            id=uuid4(),
            name="Test",
            description="Description",
            pm_agent_id=uuid4(),
            pm_session_id=uuid4(),
            path="/test/path",
        )

        model = ProjectMapper.to_model(original)
        recovered = ProjectMapper.to_entity(model)

        assert recovered.id == original.id
        assert recovered.name == original.name
        assert recovered.description == original.description
        assert recovered.pm_agent_id == original.pm_agent_id
        assert recovered.pm_session_id == original.pm_session_id
        assert recovered.path == original.path


# NOTE: TestCharacterMapper removed - Characters are now file-based (agents)


class TestMessageMapper:
    """Test MessageMapper bidirectional conversions."""

    def test_model_to_entity(self):
        """Test converting model to entity."""
        now = datetime.utcnow()
        model = Message(
            id=uuid4(),
            session_id=uuid4(),
            role="user",
            content="Hello, world!",
            tool_use_id=None,
            sequence=0,
            meta={"source": "api", "ip": "127.0.0.1"},
            created_at=now,
        )

        entity = MessageMapper.to_entity(model)

        assert entity.id == model.id
        assert entity.session_id == model.session_id
        assert entity.role == MessageRole.USER
        assert entity.content == "Hello, world!"
        assert entity.tool_use_id is None
        assert entity.sequence == 0
        assert entity.metadata == {"source": "api", "ip": "127.0.0.1"}
        assert entity.created_at == now

    def test_entity_to_model(self):
        """Test converting entity to model."""
        entity = MessageEntity(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.ASSISTANT,
            content="Response message",
            tool_use_id="tool_123",
            sequence=5,
            metadata={"model": "claude-3", "tokens": 150},
        )

        model = MessageMapper.to_model(entity)

        assert model.id == entity.id
        assert model.session_id == entity.session_id
        assert model.role == "assistant"
        assert model.content == "Response message"
        assert model.tool_use_id == "tool_123"
        assert model.sequence == 5
        assert model.meta == {"model": "claude-3", "tokens": 150}

    def test_model_to_entity_with_none_metadata(self):
        """Test converting model with None metadata to entity."""
        model = Message(
            id=uuid4(),
            session_id=uuid4(),
            role="system",
            content="System message",
            sequence=0,
            meta=None,  # None in DB
        )

        entity = MessageMapper.to_entity(model)

        assert entity.metadata == {}  # Converted to empty dict

    def test_roundtrip_conversion(self):
        """Test entity -> model -> entity preserves data."""
        original = MessageEntity(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.TOOL_RESULT,
            content='{"result": "success"}',
            tool_use_id="tool_456",
            sequence=10,
            metadata={"duration_ms": 234},
        )

        model = MessageMapper.to_model(original)
        recovered = MessageMapper.to_entity(model)

        assert recovered.id == original.id
        assert recovered.session_id == original.session_id
        assert recovered.role == original.role
        assert recovered.content == original.content
        assert recovered.tool_use_id == original.tool_use_id
        assert recovered.sequence == original.sequence
        assert recovered.metadata == original.metadata


# NOTE: TestSkillMapper removed - Skills are now file-based (not database-backed)
