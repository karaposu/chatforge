"""
Test SQLiteStorageAdapter (Layer 3: Adapter with Database).

This module tests SQLiteStorageAdapter with a temporary SQLite database.
Tests persistence, JSON serialization, and all StoragePort operations.

Test Strategy:
- Use pytest tmp_path fixture for temporary databases
- Test all StoragePort interface methods
- Test persistence across adapter instances
- Test JSON metadata serialization/deserialization
- Test table creation and initialization
- Test concurrency

Note: Async operations throughout - SQLite adapter uses aiosqlite.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chatforge.adapters.storage.sqlite import SQLiteStorageAdapter
from chatforge.ports.storage import ConversationRecord, MessageRecord


# =============================================================================
# SETUP AND INITIALIZATION TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_adapter_creation_with_temp_db(tmp_path: Path):
    """Test SQLiteStorageAdapter creates database file."""
    db_path = tmp_path / "test.db"
    adapter = SQLiteStorageAdapter(database_path=str(db_path))

    # Initialize by calling health check
    await adapter.health_check()

    # Database file should exist
    assert db_path.exists()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_adapter_creates_tables(tmp_path: Path):
    """Test that tables are created on first operation."""
    db_path = tmp_path / "test.db"
    adapter = SQLiteStorageAdapter(database_path=str(db_path))

    # Save a message (should trigger table creation)
    message = MessageRecord(content="Test", role="user")
    await adapter.save_message("conv-1", message)

    # Verify tables exist by querying
    import aiosqlite

    async with aiosqlite.connect(str(db_path)) as db:
        # Check conversations table
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None

        # Check messages table
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_adapter_setup_is_idempotent(tmp_path: Path):
    """Test that setup() can be called multiple times."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Call setup multiple times
    await adapter.setup()
    await adapter.setup()
    await adapter.setup()

    # Should not error
    health = await adapter.health_check()
    assert health is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_adapter_health_check(tmp_path: Path):
    """Test health check returns True when DB is accessible."""
    db_path = tmp_path / "test.db"
    adapter = SQLiteStorageAdapter(database_path=str(db_path))

    health = await adapter.health_check()
    assert health is True


# =============================================================================
# MESSAGE SAVE/RETRIEVE TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_and_retrieve_single_message(tmp_path: Path):
    """Test saving and retrieving a single message."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    message = MessageRecord(content="Hello, SQLite!", role="user")
    await adapter.save_message("conv-1", message)

    # Retrieve messages using get_conversation()
    messages = await adapter.get_conversation("conv-1")

    assert len(messages) == 1
    assert messages[0].content == "Hello, SQLite!"
    assert messages[0].role == "user"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_multiple_messages_preserves_order(tmp_path: Path):
    """Test that messages are retrieved in insertion order."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    messages = [
        MessageRecord(content="First", role="user"),
        MessageRecord(content="Second", role="assistant"),
        MessageRecord(content="Third", role="user"),
    ]

    for msg in messages:
        await adapter.save_message("conv-order", msg)

    retrieved = await adapter.get_conversation("conv-order")

    assert len(retrieved) == 3
    assert [msg.content for msg in retrieved] == ["First", "Second", "Third"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_with_limit(tmp_path: Path):
    """Test retrieving messages with limit."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save 10 messages
    for i in range(10):
        await adapter.save_message(
            "conv-limit", MessageRecord(content=f"Message {i}", role="user")
        )

    # Get last 5 messages
    messages = await adapter.get_conversation("conv-limit", limit=5)

    assert len(messages) == 5
    # Should get messages 5-9 (last 5)
    assert messages[0].content == "Message 5"
    assert messages[-1].content == "Message 9"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_empty_conversation(tmp_path: Path):
    """Test retrieving messages from non-existent conversation."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    messages = await adapter.get_conversation("non-existent")
    assert messages == []


# =============================================================================
# MESSAGE METADATA TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_and_retrieve_message_with_metadata(tmp_path: Path):
    """Test that metadata is serialized/deserialized correctly."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    metadata = {
        "tool_calls": [{"name": "search", "args": {"query": "test"}}],
        "model": "gpt-4o-mini",
        "tokens_used": 150,
    }

    message = MessageRecord(content="Response", role="assistant", metadata=metadata)
    await adapter.save_message("conv-meta", message)

    # Retrieve and verify metadata
    messages = await adapter.get_conversation("conv-meta")
    assert len(messages) == 1

    retrieved_meta = messages[0].metadata
    assert retrieved_meta["tool_calls"] == [{"name": "search", "args": {"query": "test"}}]
    assert retrieved_meta["model"] == "gpt-4o-mini"
    assert retrieved_meta["tokens_used"] == 150


@pytest.mark.unit
@pytest.mark.asyncio
async def test_message_with_empty_metadata(tmp_path: Path):
    """Test message with empty metadata dict."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    message = MessageRecord(content="No metadata", role="user", metadata={})
    await adapter.save_message("conv-empty-meta", message)

    messages = await adapter.get_conversation("conv-empty-meta")
    assert messages[0].metadata == {}


# =============================================================================
# CONVERSATION METADATA TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_metadata_after_save(tmp_path: Path):
    """Test getting conversation metadata."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save a message (creates conversation)
    message = MessageRecord(content="Test", role="user")
    await adapter.save_message("conv-123", message, user_id="user-456")

    # Get metadata
    metadata = await adapter.get_conversation_metadata("conv-123")

    assert metadata is not None
    assert metadata.conversation_id == "conv-123"
    assert metadata.user_id == "user-456"
    assert metadata.platform == "api"  # Default platform


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conversation_metadata_nonexistent(tmp_path: Path):
    """Test getting metadata for non-existent conversation."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    metadata = await adapter.get_conversation_metadata("non-existent")
    assert metadata is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_message_creates_conversation_implicitly(tmp_path: Path):
    """Test that saving a message creates conversation if it doesn't exist."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save message without explicit conversation creation
    message = MessageRecord(content="Implicit conversation", role="user")
    await adapter.save_message("conv-implicit", message, user_id="user-789")

    # Should succeed
    messages = await adapter.get_conversation("conv-implicit")
    assert len(messages) == 1


# =============================================================================
# CONVERSATION DELETION TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_conversation(tmp_path: Path):
    """Test deleting a conversation and its messages."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Create conversation with messages
    for i in range(5):
        await adapter.save_message(
            "conv-delete", MessageRecord(content=f"Msg {i}", role="user")
        )

    messages = await adapter.get_conversation("conv-delete")
    assert len(messages) == 5

    # Delete conversation
    result = await adapter.delete_conversation("conv-delete")
    assert result is True

    # Messages should be gone
    messages = await adapter.get_conversation("conv-delete")
    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_nonexistent_conversation(tmp_path: Path):
    """Test deleting non-existent conversation returns False."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    result = await adapter.delete_conversation("non-existent")
    # SQLite adapter returns False for non-existent conversations
    assert result is False


# =============================================================================
# CLEANUP EXPIRED TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_expired_old_conversations(tmp_path: Path):
    """Test cleanup removes old conversations."""
    import aiosqlite

    db_path = tmp_path / "test.db"
    adapter = SQLiteStorageAdapter(database_path=str(db_path))

    # Create old conversation
    await adapter.save_message("conv-old", MessageRecord(content="Old", role="user"))

    # Manually update the conversation's updated_at to be old
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (old_time, "conv-old"),
        )
        await db.commit()

    # Create recent conversation
    await adapter.save_message("conv-recent", MessageRecord(content="Recent", role="user"))

    # Clean up conversations older than 30 minutes
    deleted_count = await adapter.cleanup_expired(ttl_minutes=30)

    assert deleted_count == 1

    # Old conversation should be gone
    old_messages = await adapter.get_conversation("conv-old")
    assert old_messages == []

    # Recent conversation should still exist
    recent_messages = await adapter.get_conversation("conv-recent")
    assert len(recent_messages) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_expired_no_expired_conversations(tmp_path: Path):
    """Test cleanup with no expired conversations."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Create recent conversation
    message = MessageRecord(content="Recent", role="user")
    await adapter.save_message("conv-recent", message)

    # Clean up (nothing should be deleted)
    deleted_count = await adapter.cleanup_expired(ttl_minutes=30)

    assert deleted_count == 0


# =============================================================================
# LIST CONVERSATIONS TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_all(tmp_path: Path):
    """Test listing all conversations."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Create multiple conversations
    for i in range(5):
        await adapter.save_message(
            f"conv-{i}",
            MessageRecord(content="Test", role="user"),
            user_id=f"user-{i}",
        )

    conversations = await adapter.list_conversations()

    assert len(conversations) == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_filtered_by_user(tmp_path: Path):
    """Test listing conversations filtered by user_id."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Create conversations for different users
    await adapter.save_message(
        "conv-1", MessageRecord(content="Test", role="user"), user_id="alice"
    )
    await adapter.save_message(
        "conv-2", MessageRecord(content="Test", role="user"), user_id="alice"
    )
    await adapter.save_message(
        "conv-3", MessageRecord(content="Test", role="user"), user_id="bob"
    )

    # List Alice's conversations
    alice_convs = await adapter.list_conversations(user_id="alice")
    assert len(alice_convs) == 2

    # List Bob's conversations
    bob_convs = await adapter.list_conversations(user_id="bob")
    assert len(bob_convs) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_conversations_with_limit(tmp_path: Path):
    """Test listing conversations with limit."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Create 10 conversations
    for i in range(10):
        await adapter.save_message(
            f"conv-{i}", MessageRecord(content="Test", role="user")
        )

    # Get only 5
    conversations = await adapter.list_conversations(limit=5)

    assert len(conversations) == 5


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_data_persists_across_adapter_instances(tmp_path: Path):
    """Test that data persists when creating new adapter instance."""
    db_path = tmp_path / "persistent.db"

    # First adapter - save data
    adapter1 = SQLiteStorageAdapter(database_path=str(db_path))
    message = MessageRecord(content="Persistent message", role="user")
    await adapter1.save_message("conv-persist", message)

    # Second adapter - retrieve data
    adapter2 = SQLiteStorageAdapter(database_path=str(db_path))
    messages = await adapter2.get_conversation("conv-persist")

    assert len(messages) == 1
    assert messages[0].content == "Persistent message"


# =============================================================================
# CONVERSATION ISOLATION TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_conversations_are_isolated(tmp_path: Path):
    """Test that different conversations don't interfere."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save to different conversations
    await adapter.save_message("conv-A", MessageRecord(content="Message A", role="user"))
    await adapter.save_message("conv-B", MessageRecord(content="Message B", role="user"))
    await adapter.save_message(
        "conv-A", MessageRecord(content="Message A2", role="assistant")
    )

    # Verify isolation
    messages_a = await adapter.get_conversation("conv-A")
    messages_b = await adapter.get_conversation("conv-B")

    assert len(messages_a) == 2
    assert len(messages_b) == 1
    assert messages_a[0].content == "Message A"
    assert messages_b[0].content == "Message B"


# =============================================================================
# TIMESTAMP TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_message_timestamps_preserved(tmp_path: Path):
    """Test that message created_at timestamps are preserved."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    message = MessageRecord(content="Timestamped", role="user", created_at=custom_time)

    await adapter.save_message("conv-time", message)

    messages = await adapter.get_conversation("conv-time")
    assert len(messages) == 1

    # Timestamp should be preserved (within 1 second tolerance for SQLite datetime serialization)
    time_diff = abs((messages[0].created_at - custom_time).total_seconds())
    assert time_diff < 1.0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_long_message_content(tmp_path: Path):
    """Test saving very long message content."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    long_content = "x" * 100_000  # 100KB message
    message = MessageRecord(content=long_content, role="user")

    await adapter.save_message("conv-long", message)

    messages = await adapter.get_conversation("conv-long")
    assert len(messages) == 1
    assert len(messages[0].content) == 100_000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_special_characters_in_content(tmp_path: Path):
    """Test that special characters are handled correctly."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    special_content = "Hello 'world' \"test\" \n\t\r emoji 🚀"
    message = MessageRecord(content=special_content, role="user")

    await adapter.save_message("conv-special", message)

    messages = await adapter.get_conversation("conv-special")
    assert messages[0].content == special_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_null_user_id(tmp_path: Path):
    """Test saving message with null user_id."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    message = MessageRecord(content="Anonymous", role="user")
    await adapter.save_message("conv-anon", message, user_id=None)

    messages = await adapter.get_conversation("conv-anon")
    assert len(messages) == 1


# =============================================================================
# CONCURRENCY TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_message_saves(tmp_path: Path):
    """Test concurrent message saves to same conversation."""
    import asyncio

    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save 50 messages concurrently
    tasks = [
        adapter.save_message(
            "conv-concurrent", MessageRecord(content=f"Message {i}", role="user")
        )
        for i in range(50)
    ]

    await asyncio.gather(*tasks)

    # All messages should be saved
    messages = await adapter.get_conversation("conv-concurrent")
    assert len(messages) == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_reads(tmp_path: Path):
    """Test concurrent reads from same conversation."""
    import asyncio

    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save some messages first
    for i in range(10):
        await adapter.save_message(
            "conv-read", MessageRecord(content=f"Msg {i}", role="user")
        )

    # Read concurrently
    tasks = [adapter.get_conversation("conv-read") for _ in range(20)]
    results = await asyncio.gather(*tasks)

    # All reads should succeed with same data
    assert all(len(msgs) == 10 for msgs in results)


# =============================================================================
# CLOSE TESTS
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_is_idempotent(tmp_path: Path):
    """Test that close() can be called multiple times."""
    adapter = SQLiteStorageAdapter(database_path=str(tmp_path / "test.db"))

    # Save some data
    await adapter.save_message("conv-1", MessageRecord(content="Test", role="user"))

    # Close multiple times
    await adapter.close()
    await adapter.close()
    await adapter.close()

    # Should not error
