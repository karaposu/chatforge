"""
In-Memory Storage Adapter - Implementation of StoragePort.

Provides a simple in-memory storage for development and testing.
Data is lost when the application restarts.

Thread-safe implementation using asyncio.Lock for concurrent access.

Example:
    adapter = InMemoryStorageAdapter()

    await adapter.save_message("conv-1", MessageRecord(content="Hi", role="user"))
    history = await adapter.get_conversation("conv-1")
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from chatforge.ports import (
    ConversationRecord,
    MessageRecord,
    StoragePort,
)


logger = logging.getLogger(__name__)


class InMemoryStorageAdapter(StoragePort):
    """
    In-memory implementation of StoragePort.

    Stores conversations and messages in dictionaries with thread-safe access
    using asyncio.Lock. Suitable for development, testing, and single-instance
    deployments.

    Note: Data is not persisted across restarts.

    Thread Safety:
        All mutating operations acquire the lock to prevent race conditions
        when multiple coroutines access the same conversation concurrently.
    """

    def __init__(self):
        """Initialize in-memory storage with lock for thread safety."""
        self._conversations: dict[str, ConversationRecord] = {}
        self._messages: dict[str, list[MessageRecord]] = {}
        self._lock = asyncio.Lock()
        logger.info("InMemoryStorageAdapter initialized (thread-safe)")

    async def setup(self) -> None:
        """No-op for in-memory adapter."""

    async def close(self) -> None:
        """Clear all data."""
        async with self._lock:
            self._conversations.clear()
            self._messages.clear()
        logger.info("InMemoryStorageAdapter data cleared")

    async def save_message(
        self,
        conversation_id: str,
        message: MessageRecord,
        user_id: str | None = None,
    ) -> None:
        """
        Save a message to conversation history.

        Creates the conversation if it doesn't exist.
        Thread-safe: acquires lock during write operations.
        """
        now = datetime.now(timezone.utc)

        async with self._lock:
            # Create or update conversation
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = ConversationRecord(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    platform="api",
                    created_at=now,
                    updated_at=now,
                )
                self._messages[conversation_id] = []
            else:
                # Update timestamp and user_id if provided
                conv = self._conversations[conversation_id]
                conv.updated_at = now
                if user_id:
                    conv.user_id = user_id

            # Add message
            self._messages[conversation_id].append(message)
            total = len(self._messages[conversation_id])

        logger.debug(f"Saved message to conversation {conversation_id} (total: {total})")

    async def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[MessageRecord]:
        """
        Retrieve conversation history.

        Returns messages in chronological order (oldest first).
        """
        if conversation_id not in self._messages:
            return []

        messages = self._messages[conversation_id]

        # Return last `limit` messages in chronological order
        if len(messages) > limit:
            return messages[-limit:]
        return messages.copy()

    async def get_conversation_metadata(
        self,
        conversation_id: str,
    ) -> ConversationRecord | None:
        """Get conversation metadata without messages."""
        return self._conversations.get(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages. Thread-safe."""
        async with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                del self._messages[conversation_id]
                logger.info(f"Deleted conversation {conversation_id}")
                return True
            return False

    async def cleanup_expired(self, ttl_minutes: int = 30) -> int:
        """Remove conversations older than TTL. Thread-safe."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=ttl_minutes)

        async with self._lock:
            expired = [
                conv_id
                for conv_id, conv in self._conversations.items()
                if conv.updated_at < cutoff
            ]

            for conv_id in expired:
                del self._conversations[conv_id]
                del self._messages[conv_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")

        return len(expired)

    async def list_conversations(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationRecord]:
        """List conversations, optionally filtered by user."""
        conversations = list(self._conversations.values())

        # Filter by user if specified
        if user_id:
            conversations = [c for c in conversations if c.user_id == user_id]

        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.updated_at, reverse=True)

        return conversations[:limit]

    async def health_check(self) -> bool:
        """Always healthy for in-memory adapter."""
        return True

    # Additional methods for testing

    def get_message_count(self, conversation_id: str) -> int:
        """Get number of messages in a conversation (for testing)."""
        return len(self._messages.get(conversation_id, []))

    def get_total_conversations(self) -> int:
        """Get total number of conversations (for testing)."""
        return len(self._conversations)

    def clear(self) -> None:
        """Clear all data synchronously (for testing)."""
        self._conversations.clear()
        self._messages.clear()
