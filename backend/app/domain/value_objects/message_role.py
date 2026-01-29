"""Message role value object."""

from enum import Enum


class MessageRole(str, Enum):
    """
    Message role in conversation.

    Message roles define the source and type of a message:
    - USER: User query or input
    - ASSISTANT: Assistant response
    - SYSTEM: System message (internal)
    - TOOL_CALL: Tool invocation by assistant
    - TOOL_RESULT: Result from tool execution
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool"
    TOOL_RESULT = "tool_result"

    def is_from_user(self) -> bool:
        """
        Check if message is from the user.

        Returns:
            True if message role is USER, False otherwise

        Examples:
            >>> MessageRole.USER.is_from_user()
            True
            >>> MessageRole.ASSISTANT.is_from_user()
            False
        """
        return self == self.USER

    def is_from_assistant(self) -> bool:
        """
        Check if message is from the assistant.

        Returns:
            True if message role is ASSISTANT, False otherwise

        Examples:
            >>> MessageRole.ASSISTANT.is_from_assistant()
            True
            >>> MessageRole.USER.is_from_assistant()
            False
        """
        return self == self.ASSISTANT

    def is_system_or_tool(self) -> bool:
        """
        Check if message is a system message or tool result.

        Returns:
            True if message role is SYSTEM or TOOL_RESULT, False otherwise

        Examples:
            >>> MessageRole.SYSTEM.is_system_or_tool()
            True
            >>> MessageRole.TOOL_RESULT.is_system_or_tool()
            True
            >>> MessageRole.USER.is_system_or_tool()
            False
        """
        return self in {self.SYSTEM, self.TOOL_RESULT}

    def requires_tool_use_id(self) -> bool:
        """
        Check if this message role requires a tool_use_id.

        Returns:
            True if TOOL_RESULT role, False otherwise

        Examples:
            >>> MessageRole.TOOL_RESULT.requires_tool_use_id()
            True
            >>> MessageRole.USER.requires_tool_use_id()
            False
        """
        return self == self.TOOL_RESULT
