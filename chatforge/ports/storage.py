"""
Storage Port - Abstract interface for conversation persistence.

This port defines the contract for conversation storage.
Implementations can include PostgreSQL, Redis, SQLite, or in-memory stores.

The core agent logic depends only on this interface, enabling:
- Easy swapping of storage backends
- TTL-based cleanup
- User/session isolation
- Mock implementations for testing

The interface has two layers:
1. Legacy interface (required): save_message, get_conversation, etc.
2. Extended interface (optional): create_chat, log_tool_call, start_agent_run, etc.

Simple adapters only need to implement the legacy interface.
Full-featured adapters can implement the extended interface for observability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict

# Storage types are part of the port interface
from chatforge.ports.storage_types import (
    ChatRecord,
    MessageRecord,
    ToolCallRecord,
    AgentRunRecord,
    MessageMetadata,
    ChatMetadata,
    TokenUsage,
)

# Legacy alias
ConversationRecord = ChatRecord
ConversationMetadata = ChatMetadata


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime for dataclass defaults."""
    return datetime.now(timezone.utc)


class StoragePort(ABC):
    """
    Abstract port for conversation storage.

    This interface defines the contract that all storage adapters
    must implement. The core agent logic depends only on this interface,
    enabling:

    - Easy swapping of storage backends (PostgreSQL -> Redis)
    - Mock implementations for testing
    - TTL-based cleanup for compliance
    - Multiple simultaneous storage configurations
    """

    @abstractmethod
    async def save_message(
        self,
        conversation_id: str,
        message: MessageRecord,
        user_id: str | None = None,
    ) -> None:
        """
        Save a message to conversation history.

        If the conversation doesn't exist, it will be created.
        Updates the conversation's updated_at timestamp.

        Args:
            conversation_id: Unique identifier for the conversation.
            message: The message to save.
            user_id: Optional user identifier for the conversation owner.
        """

    @abstractmethod
    async def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[MessageRecord]:
        """
        Retrieve conversation history.

        Returns messages in chronological order (oldest first).

        Args:
            conversation_id: Unique identifier for the conversation.
            limit: Maximum number of messages to return.

        Returns:
            List of MessageRecord objects in chronological order.
        """

    @abstractmethod
    async def get_conversation_metadata(
        self,
        conversation_id: str,
    ) -> ConversationRecord | None:
        """
        Get conversation metadata without messages.

        Args:
            conversation_id: Unique identifier for the conversation.

        Returns:
            ConversationRecord if found, None otherwise.
        """

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Used for TTL compliance and user-requested deletion.

        Args:
            conversation_id: Unique identifier for the conversation.

        Returns:
            True if conversation was deleted, False if not found.
        """

    @abstractmethod
    async def cleanup_expired(self, ttl_minutes: int = 30) -> int:
        """
        Remove conversations older than TTL.

        Args:
            ttl_minutes: Maximum age of conversations in minutes.

        Returns:
            Number of conversations deleted.
        """

    @abstractmethod
    async def list_conversations(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationRecord]:
        """
        List conversations, optionally filtered by user.

        Args:
            user_id: If provided, only return conversations for this user.
            limit: Maximum number of conversations to return.

        Returns:
            List of ConversationRecord objects, newest first.
        """

    # Optional lifecycle methods (can be no-ops)

    async def setup(self) -> None:
        """
        Initialize the storage backend.

        Called on application startup. Implementations may:
        - Create database tables
        - Establish connection pools
        - Run migrations
        """

    async def close(self) -> None:
        """
        Clean up resources.

        Called on application shutdown. Implementations may:
        - Close connection pools
        - Flush pending writes
        """

    async def health_check(self) -> bool:
        """
        Check if the storage backend is healthy.

        Returns:
            True if the backend is operational.
        """
        return True

    # =========================================================================
    # Extended Interface (Optional)
    # =========================================================================
    # These methods provide full observability features.
    # Adapters can override them; default implementations raise NotImplementedError.

    # Chat Operations

    async def create_chat(
        self,
        user_id: str,
        title: str | None = None,
        system_prompt: str | None = None,
        settings: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatRecord:
        """
        Create a new chat.

        Args:
            user_id: Owner of the chat
            title: Optional display name
            system_prompt: Default system prompt
            settings: Model configuration
            metadata: App-specific data

        Returns:
            The created ChatRecord
        """
        raise NotImplementedError("Extended interface not implemented")

    async def get_chat(self, chat_id: int) -> ChatRecord | None:
        """Get a chat by ID."""
        raise NotImplementedError("Extended interface not implemented")

    async def update_chat(
        self,
        chat_id: int,
        title: str | None = None,
        system_prompt: str | None = None,
        settings: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatRecord | None:
        """Update a chat."""
        raise NotImplementedError("Extended interface not implemented")

    async def delete_chat(self, chat_id: int, soft: bool = True) -> bool:
        """Delete a chat (soft delete by default)."""
        raise NotImplementedError("Extended interface not implemented")

    async def list_chats(
        self,
        user_id: str | None = None,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ChatRecord]:
        """List chats, optionally filtered by user."""
        raise NotImplementedError("Extended interface not implemented")

    # Message Operations (Extended)

    async def get_messages(
        self,
        chat_id: int,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[MessageRecord]:
        """Get messages for a chat."""
        raise NotImplementedError("Extended interface not implemented")

    async def delete_message(self, message_id: int, soft: bool = True) -> bool:
        """Delete a message."""
        raise NotImplementedError("Extended interface not implemented")

    # Tool Call Operations

    async def log_tool_call(
        self,
        message_id: int,
        tool_name: str,
        input_params: dict[str, Any],
        run_id: int | None = None,
        tool_version: str | None = None,
    ) -> ToolCallRecord:
        """
        Log a tool call.

        Args:
            message_id: Which message triggered this
            tool_name: Name of the tool
            input_params: Parameters passed to the tool
            run_id: Part of which agent run
            tool_version: Tool version if tracked

        Returns:
            The created ToolCallRecord
        """
        raise NotImplementedError("Extended interface not implemented")

    async def update_tool_call(
        self,
        tool_call_id: int,
        status: str,
        output_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        execution_time_ms: int | None = None,
    ) -> ToolCallRecord | None:
        """Update a tool call with results."""
        raise NotImplementedError("Extended interface not implemented")

    async def get_tool_calls(
        self,
        message_id: int | None = None,
        run_id: int | None = None,
    ) -> list[ToolCallRecord]:
        """Get tool calls filtered by message or run."""
        raise NotImplementedError("Extended interface not implemented")

    # Agent Run Operations

    async def start_agent_run(
        self,
        chat_id: int,
        agent_name: str,
        trigger_message_id: int | None = None,
        agent_version: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentRunRecord:
        """
        Start a new agent run.

        Args:
            chat_id: Which chat this run belongs to
            agent_name: Name/type of agent
            trigger_message_id: Message that triggered this run
            agent_version: Version if tracked
            input_data: Initial input
            metadata: App-specific data

        Returns:
            The created AgentRunRecord
        """
        raise NotImplementedError("Extended interface not implemented")

    async def complete_agent_run(
        self,
        run_id: int,
        status: str,
        final_result: dict[str, Any] | None = None,
        error_message: str | None = None,
        total_steps: int | None = None,
        total_tool_calls: int | None = None,
        token_usage: dict[str, Any] | None = None,
        cost: float | None = None,
    ) -> AgentRunRecord | None:
        """Complete an agent run with results."""
        raise NotImplementedError("Extended interface not implemented")

    async def get_agent_run(self, run_id: int) -> AgentRunRecord | None:
        """Get an agent run by ID."""
        raise NotImplementedError("Extended interface not implemented")

    async def list_agent_runs(
        self,
        chat_id: int | None = None,
        agent_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[AgentRunRecord]:
        """List agent runs with optional filters."""
        raise NotImplementedError("Extended interface not implemented")
