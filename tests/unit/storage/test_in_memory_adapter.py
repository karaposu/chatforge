"""
Test InMemoryStorageAdapter (Layer 2: Adapter Isolation).

This module tests the InMemoryStorageAdapter implementation without
depending on other components. All async operations are tested.

Test Strategy:
- Test all StoragePort methods
- Test thread-safety (concurrent operations)
- Test TTL cleanup
- Test limit/filtering
- Test edge cases (empty, non-existent)
- Test helper methods

Note: All tests use async/await since storage operations are async.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from chatforge.adapters.storage import InMemoryStorageAdapter
from chatforge.ports.storage import (
    ConversationRecord,
    MessageRecord,
)


# =============================================================================
# SETUP / TEARDOWN TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_adapter_initialization():
    """Test InMemoryStorageAdapter initialization."""
    adapter = InMemoryStorageAdapter()

    # Should be empty initially
    assert adapter.get_total_conversations() == 0

    # Should be healthy
    assert await adapter.health_check() is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_adapter_setup_is_noop():
    """Test that setup() is a no-op for in-memory adapter."""
    adapter = InMemoryStorageAdapter()

    # setup() should not raise and should do nothing
    await adapter.setup()

    assert adapter.get_total_conversations() == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_adapter_close_clears_data():
    """Test that close() clears all data."""
    adapter = InMemoryStorageAdapter()

    # Add some data
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="Test", role="user")
    )

    assert adapter.get_total_conversations() == 1

    # Close should clear data
    await adapter.close()

    assert adapter.get_total_conversations() == 0


# =============================================================================
# SAVE MESSAGE TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_single_message():
    """Test saving a single message."""
    adapter = InMemoryStorageAdapter()

    message = MessageRecord(content="Hello", role="user")
    await adapter.save_message("conv-1", message)

    # Conversation should be created
    assert adapter.get_total_conversations() == 1
    assert adapter.get_message_count("conv-1") == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_creates_conversation():
    """Test that saving a message creates conversation if not exists."""
    adapter = InMemoryStorageAdapter()

    await adapter.save_message(
        "conv-new",
        MessageRecord(content="First message", role="user"),
        user_id="user-123"
    )

    # Check conversation was created
    metadata = await adapter.get_conversation_metadata("conv-new")

    assert metadata is not None
    assert metadata.conversation_id == "conv-new"
    assert metadata.user_id == "user-123"
    assert metadata.platform == "api"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_multiple_messages():
    """Test saving multiple messages to same conversation."""
    adapter = InMemoryStorageAdapter()

    messages = [
        MessageRecord(content="Message 1", role="user"),
        MessageRecord(content="Response 1", role="assistant"),
        MessageRecord(content="Message 2", role="user"),
    ]

    for msg in messages:
        await adapter.save_message("conv-1", msg)

    assert adapter.get_message_count("conv-1") == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_updates_timestamp():
    """Test that saving a message updates conversation updated_at."""
    adapter = InMemoryStorageAdapter()

    # Save first message
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="First", role="user")
    )

    meta1 = await adapter.get_conversation_metadata("conv-1")
    assert meta1 is not None
    first_updated = meta1.updated_at

    # Wait a bit
    await asyncio.sleep(0.01)

    # Save second message
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="Second", role="user")
    )

    meta2 = await adapter.get_conversation_metadata("conv-1")
    assert meta2 is not None

    # Timestamp should be updated
    assert meta2.updated_at > first_updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_updates_user_id():
    """Test that saving with user_id updates conversation."""
    adapter = InMemoryStorageAdapter()

    # Create conversation without user_id
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="First", role="user")
    )

    # Add message with user_id
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="Second", role="user"),
        user_id="user-123"
    )

    metadata = await adapter.get_conversation_metadata("conv-1")
    assert metadata is not None
    assert metadata.user_id == "user-123"


# =============================================================================
# GET CONVERSATION TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_empty():
    """Test getting a conversation that doesn't exist."""
    adapter = InMemoryStorageAdapter()

    messages = await adapter.get_conversation("non-existent")

    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_chronological_order():
    """Test that messages are returned in chronological order."""
    adapter = InMemoryStorageAdapter()

    # Add messages with small delays
    for i in range(5):
        await adapter.save_message(
            "conv-1",
            MessageRecord(content=f"Message {i}", role="user")
        )
        await asyncio.sleep(0.001)  # Ensure different timestamps

    messages = await adapter.get_conversation("conv-1")

    # Should be in order (oldest first)
    assert len(messages) == 5
    for i, msg in enumerate(messages):
        assert msg.content == f"Message {i}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_with_limit():
    """Test getting conversation with limit."""
    adapter = InMemoryStorageAdapter()

    # Add 10 messages
    for i in range(10):
        await adapter.save_message(
            "conv-1",
            MessageRecord(content=f"Message {i}", role="user")
        )

    # Get last 5
    messages = await adapter.get_conversation("conv-1", limit=5)

    assert len(messages) == 5
    # Should be last 5 messages (5-9)
    assert messages[0].content == "Message 5"
    assert messages[4].content == "Message 9"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_limit_larger_than_total():
    """Test limit larger than total messages."""
    adapter = InMemoryStorageAdapter()

    # Add 3 messages
    for i in range(3):
        await adapter.save_message(
            "conv-1",
            MessageRecord(content=f"Message {i}", role="user")
        )

    # Request limit of 100
    messages = await adapter.get_conversation("conv-1", limit=100)

    # Should return all 3
    assert len(messages) == 3


# =============================================================================
# GET CONVERSATION METADATA TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_metadata():
    """Test getting conversation metadata."""
    adapter = InMemoryStorageAdapter()

    await adapter.save_message(
        "conv-1",
        MessageRecord(content="Test", role="user"),
        user_id="user-123"
    )

    metadata = await adapter.get_conversation_metadata("conv-1")

    assert metadata is not None
    assert metadata.conversation_id == "conv-1"
    assert metadata.user_id == "user-123"
    assert isinstance(metadata.created_at, datetime)
    assert isinstance(metadata.updated_at, datetime)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_metadata_non_existent():
    """Test getting metadata for non-existent conversation."""
    adapter = InMemoryStorageAdapter()

    metadata = await adapter.get_conversation_metadata("non-existent")

    assert metadata is None


# =============================================================================
# DELETE CONVERSATION TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_conversation():
    """Test deleting a conversation."""
    adapter = InMemoryStorageAdapter()

    # Create conversation
    await adapter.save_message(
        "conv-to-delete",
        MessageRecord(content="Test", role="user")
    )

    assert adapter.get_total_conversations() == 1

    # Delete it
    deleted = await adapter.delete_conversation("conv-to-delete")

    assert deleted is True
    assert adapter.get_total_conversations() == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_conversation_removes_messages():
    """Test that deleting conversation removes all messages."""
    adapter = InMemoryStorageAdapter()

    # Add multiple messages
    for i in range(5):
        await adapter.save_message(
            "conv-1",
            MessageRecord(content=f"Message {i}", role="user")
        )

    assert adapter.get_message_count("conv-1") == 5

    # Delete conversation
    await adapter.delete_conversation("conv-1")

    # Messages should be gone
    messages = await adapter.get_conversation("conv-1")
    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_non_existent_conversation():
    """Test deleting a conversation that doesn't exist."""
    adapter = InMemoryStorageAdapter()

    deleted = await adapter.delete_conversation("non-existent")

    assert deleted is False


# =============================================================================
# CLEANUP EXPIRED TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_expired_no_expired():
    """Test cleanup when no conversations are expired."""
    adapter = InMemoryStorageAdapter()

    # Create recent conversation
    await adapter.save_message(
        "conv-recent",
        MessageRecord(content="Recent", role="user")
    )

    # Cleanup with 30 minute TTL (should delete nothing)
    deleted = await adapter.cleanup_expired(ttl_minutes=30)

    assert deleted == 0
    assert adapter.get_total_conversations() == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_expired_removes_old_conversations():
    """Test that cleanup removes old conversations."""
    adapter = InMemoryStorageAdapter()

    # Create old conversation by manually setting timestamp
    await adapter.save_message(
        "conv-old",
        MessageRecord(content="Old message", role="user")
    )

    # Manually set old timestamp
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    conv = await adapter.get_conversation_metadata("conv-old")
    if conv:
        conv.updated_at = old_time

    # Cleanup with 30 minute TTL
    deleted = await adapter.cleanup_expired(ttl_minutes=30)

    assert deleted == 1
    assert adapter.get_total_conversations() == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_expired_keeps_recent():
    """Test that cleanup keeps recent conversations."""
    adapter = InMemoryStorageAdapter()

    # Create old and recent conversations
    await adapter.save_message(
        "conv-old",
        MessageRecord(content="Old", role="user")
    )
    await adapter.save_message(
        "conv-recent",
        MessageRecord(content="Recent", role="user")
    )

    # Set one to be old
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    conv_old = await adapter.get_conversation_metadata("conv-old")
    if conv_old:
        conv_old.updated_at = old_time

    # Cleanup with 30 minute TTL
    deleted = await adapter.cleanup_expired(ttl_minutes=30)

    assert deleted == 1
    assert adapter.get_total_conversations() == 1

    # Recent conversation should still exist
    messages = await adapter.get_conversation("conv-recent")
    assert len(messages) == 1


# =============================================================================
# LIST CONVERSATIONS TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_empty():
    """Test listing conversations when none exist."""
    adapter = InMemoryStorageAdapter()

    conversations = await adapter.list_conversations()

    assert conversations == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations():
    """Test listing all conversations."""
    adapter = InMemoryStorageAdapter()

    # Create multiple conversations
    for i in range(5):
        await adapter.save_message(
            f"conv-{i}",
            MessageRecord(content=f"Message {i}", role="user"),
            user_id=f"user-{i}"
        )

    conversations = await adapter.list_conversations()

    assert len(conversations) == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_sorted_by_updated():
    """Test that conversations are sorted by updated_at (newest first)."""
    adapter = InMemoryStorageAdapter()

    # Create conversations with delays
    await adapter.save_message("conv-1", MessageRecord(content="First", role="user"))
    await asyncio.sleep(0.01)
    await adapter.save_message("conv-2", MessageRecord(content="Second", role="user"))
    await asyncio.sleep(0.01)
    await adapter.save_message("conv-3", MessageRecord(content="Third", role="user"))

    conversations = await adapter.list_conversations()

    # Should be newest first
    assert conversations[0].conversation_id == "conv-3"
    assert conversations[1].conversation_id == "conv-2"
    assert conversations[2].conversation_id == "conv-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_filtered_by_user():
    """Test filtering conversations by user_id."""
    adapter = InMemoryStorageAdapter()

    # Create conversations for different users
    await adapter.save_message(
        "conv-1",
        MessageRecord(content="User 1 msg", role="user"),
        user_id="user-1"
    )
    await adapter.save_message(
        "conv-2",
        MessageRecord(content="User 2 msg", role="user"),
        user_id="user-2"
    )
    await adapter.save_message(
        "conv-3",
        MessageRecord(content="User 1 msg 2", role="user"),
        user_id="user-1"
    )

    # Get conversations for user-1
    user1_convs = await adapter.list_conversations(user_id="user-1")

    assert len(user1_convs) == 2
    assert all(c.user_id == "user-1" for c in user1_convs)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_with_limit():
    """Test limiting number of conversations returned."""
    adapter = InMemoryStorageAdapter()

    # Create 10 conversations
    for i in range(10):
        await adapter.save_message(
            f"conv-{i}",
            MessageRecord(content=f"Message {i}", role="user")
        )

    # Get only 5
    conversations = await adapter.list_conversations(limit=5)

    assert len(conversations) == 5


# =============================================================================
# CONCURRENT ACCESS TESTS (Thread Safety)
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_message_saves():
    """Test that concurrent saves are thread-safe."""
    adapter = InMemoryStorageAdapter()

    # Save 100 messages concurrently
    tasks = [
        adapter.save_message(
            "conv-concurrent",
            MessageRecord(content=f"Message {i}", role="user")
        )
        for i in range(100)
    ]

    await asyncio.gather(*tasks)

    # All messages should be saved
    assert adapter.get_message_count("conv-concurrent") == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_conversation_creation():
    """Test creating multiple conversations concurrently."""
    adapter = InMemoryStorageAdapter()

    # Create 50 conversations concurrently
    tasks = [
        adapter.save_message(
            f"conv-{i}",
            MessageRecord(content="Test", role="user")
        )
        for i in range(50)
    ]

    await asyncio.gather(*tasks)

    assert adapter.get_total_conversations() == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_read_write():
    """Test concurrent reads and writes."""
    adapter = InMemoryStorageAdapter()

    # Create initial conversation
    await adapter.save_message(
        "conv-rw",
        MessageRecord(content="Initial", role="user")
    )

    # Concurrent writes and reads
    async def write_messages():
        for i in range(10):
            await adapter.save_message(
                "conv-rw",
                MessageRecord(content=f"Message {i}", role="user")
            )

    async def read_messages():
        for _ in range(10):
            await adapter.get_conversation("conv-rw")

    await asyncio.gather(
        write_messages(),
        read_messages(),
        write_messages(),
        read_messages()
    )

    # Should have initial + 20 messages
    assert adapter.get_message_count("conv-rw") == 21


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================

@pytest.mark.unit
def test_get_message_count_helper():
    """Test get_message_count() helper method."""
    adapter = InMemoryStorageAdapter()

    # Empty conversation
    assert adapter.get_message_count("non-existent") == 0


@pytest.mark.unit
def test_get_total_conversations_helper():
    """Test get_total_conversations() helper method."""
    adapter = InMemoryStorageAdapter()

    assert adapter.get_total_conversations() == 0


@pytest.mark.unit
def test_clear_helper():
    """Test clear() synchronous helper method."""
    adapter = InMemoryStorageAdapter()

    # Add data (sync methods for testing)
    adapter._conversations["conv-1"] = ConversationRecord(
        conversation_id="conv-1",
        user_id="user-1"
    )
    adapter._messages["conv-1"] = [MessageRecord(content="Test", role="user")]

    assert adapter.get_total_conversations() == 1

    # Clear
    adapter.clear()

    assert adapter.get_total_conversations() == 0
    assert adapter.get_message_count("conv-1") == 0


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_with_empty_content():
    """Test saving message with empty content."""
    adapter = InMemoryStorageAdapter()

    message = MessageRecord(content="", role="user")
    await adapter.save_message("conv-1", message)

    messages = await adapter.get_conversation("conv-1")
    assert len(messages) == 1
    assert messages[0].content == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_with_long_content():
    """Test saving message with very long content."""
    adapter = InMemoryStorageAdapter()

    long_content = "x" * 100000  # 100K characters
    message = MessageRecord(content=long_content, role="user")

    await adapter.save_message("conv-1", message)

    messages = await adapter.get_conversation("conv-1")
    assert messages[0].content == long_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_many_conversations():
    """Test adapter with many conversations."""
    adapter = InMemoryStorageAdapter()

    # Create 1000 conversations
    for i in range(1000):
        await adapter.save_message(
            f"conv-{i}",
            MessageRecord(content="Test", role="user")
        )

    assert adapter.get_total_conversations() == 1000

    # List should respect limit
    conversations = await adapter.list_conversations(limit=100)
    assert len(conversations) == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_conversation_with_many_messages():
    """Test conversation with many messages."""
    adapter = InMemoryStorageAdapter()

    # Add 1000 messages to one conversation
    for i in range(1000):
        await adapter.save_message(
            "conv-big",
            MessageRecord(content=f"Message {i}", role="user")
        )

    assert adapter.get_message_count("conv-big") == 1000

    # Get with limit should return last N
    messages = await adapter.get_conversation("conv-big", limit=50)
    assert len(messages) == 50
    assert messages[0].content == "Message 950"  # Last 50 start at 950
