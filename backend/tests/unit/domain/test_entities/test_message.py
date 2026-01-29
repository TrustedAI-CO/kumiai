"""Tests for Message domain entity."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.message import Message
from app.domain.value_objects import MessageRole


class TestMessageCreation:
    """Tests for Message entity creation."""

    def test_create_message_with_required_fields(self):
        """Test creating a message with required fields."""
        message_id = uuid4()
        session_id = uuid4()
        content = "Test message content"

        message = Message(
            id=message_id,
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
        )

        assert message.id == message_id
        assert message.session_id == session_id
        assert message.role == MessageRole.USER
        assert message.content == content
        assert message.tool_use_id is None
        assert message.sequence == 0
        assert message.metadata == {}
        assert isinstance(message.created_at, datetime)

    def test_create_message_with_optional_fields(self):
        """Test creating a message with optional fields."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.TOOL_RESULT,
            content="Tool result",
            tool_use_id="tool_123",
            sequence=5,
            metadata={"key": "value"},
        )

        assert message.tool_use_id == "tool_123"
        assert message.sequence == 5
        assert message.metadata == {"key": "value"}


class TestMessageRoleChecks:
    """Tests for Message role check methods."""

    def test_is_tool_result_for_tool_result_role(self):
        """Test is_tool_result returns True for TOOL_RESULT role."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.TOOL_RESULT,
            content="Test",
            tool_use_id="tool_123",
        )

        assert message.is_tool_result() is True
        assert message.is_user_message() is False
        assert message.is_assistant_message() is False

    def test_is_user_message_for_user_role(self):
        """Test is_user_message returns True for USER role."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
        )

        assert message.is_user_message() is True
        assert message.is_tool_result() is False
        assert message.is_assistant_message() is False

    def test_is_assistant_message_for_assistant_role(self):
        """Test is_assistant_message returns True for ASSISTANT role."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.ASSISTANT,
            content="Test",
        )

        assert message.is_assistant_message() is True
        assert message.is_user_message() is False
        assert message.is_tool_result() is False

    def test_all_role_checks_false_for_system_role(self):
        """Test all specific role checks return False for SYSTEM role."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.SYSTEM,
            content="Test",
        )

        assert message.is_user_message() is False
        assert message.is_assistant_message() is False
        assert message.is_tool_result() is False


class TestMessageValidation:
    """Tests for Message.validate() method."""

    def test_validate_with_valid_user_message_passes(self):
        """Test validate passes with valid user message."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test content",
        )

        # Should not raise
        message.validate()

    def test_validate_with_valid_assistant_message_passes(self):
        """Test validate passes with valid assistant message."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.ASSISTANT,
            content="Test response",
        )

        # Should not raise
        message.validate()

    def test_validate_with_valid_tool_result_message_passes(self):
        """Test validate passes with valid tool result message."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.TOOL_RESULT,
            content="Tool output",
            tool_use_id="tool_123",
        )

        # Should not raise
        message.validate()

    def test_validate_empty_content_raises_error(self):
        """Test validate raises error for empty content."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="",
        )

        with pytest.raises(ValidationError) as exc_info:
            message.validate()

        assert "Message content cannot be empty" in str(exc_info.value)

    def test_validate_tool_result_without_tool_use_id_raises_error(self):
        """Test validate raises error for tool result without tool_use_id."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.TOOL_RESULT,
            content="Tool output",
        )

        with pytest.raises(ValidationError) as exc_info:
            message.validate()

        assert "Tool result messages must have tool_use_id" in str(exc_info.value)

    def test_validate_negative_sequence_raises_error(self):
        """Test validate raises error for negative sequence."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
            sequence=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            message.validate()

        assert "Message sequence must be non-negative" in str(exc_info.value)

    def test_validate_zero_sequence_passes(self):
        """Test validate passes for zero sequence."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
            sequence=0,
        )

        # Should not raise
        message.validate()

    def test_validate_positive_sequence_passes(self):
        """Test validate passes for positive sequence."""
        message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
            sequence=10,
        )

        # Should not raise
        message.validate()
