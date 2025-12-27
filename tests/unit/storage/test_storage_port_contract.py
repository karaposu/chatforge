"""
Test StoragePort Contract (Layer 4: Port + Adapter Compliance).

This module tests that all StoragePort implementations (InMemoryStorageAdapter,
SQLiteStorageAdapter) properly implement the StoragePort interface and behave
consistently.

Test Strategy:
- Use pytest.mark.parametrize to test both adapters with same tests
- Verify all required methods exist
- Verify consistent behavior across implementations
- Verify return types and contracts

This ensures:
- New adapters can be added and validated against the contract
- All adapters behave consistently
- Code depending on StoragePort can use any adapter interchangeably
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chatforge.adapters.storage import InMemoryStorageAdapter
from chatforge.adapters.storage.sqlite import SQLiteStorageAdapter
from chatforge.ports.storage import (
    ConversationRecord,
    MessageRecord,
    StoragePort,
)


# =============================================================================
# FIXTURES FOR ADAPTER INSTANCES
# =============================================================================


@pytest.fixture
def in_memory_adapter():
    """Create InMemoryStorageAdapter instance."""
    return InMemoryStorageAdapter()


@pytest.fixture
def sqlite_adapter(tmp_path: Path):
    """Create SQLiteStorageAdapter with temp database."""
    db_path = tmp_path / "test.db"
    return SQLiteStorageAdapter(database_path=str(db_path))


@pytest.fixture(params=["in_memory", "sqlite"])
def storage_adapter(request, in_memory_adapter, sqlite_adapter):
    """
    Parametrized fixture that provides both adapter types.

    Tests using this fixture will run once for each adapter implementation.
    """
    if request.param == "in_memory":
        return in_memory_adapter
    elif request.param == "sqlite":
        return sqlite_adapter


# =============================================================================
# INTERFACE COMPLIANCE TESTS
# =============================================================================


@pytest.mark.unit
def test_adapter_implements_storage_port(storage_adapter: StoragePort):
    """Test that adapter implements StoragePort interface."""
    assert isinstance(storage_adapter, StoragePort)


@pytest.mark.unit
def test_adapter_has_required_methods(storage_adapter: StoragePort):
    """Test that adapter has all required StoragePort methods."""
    required_methods = [
        "save_message",
        "get_conversation",
        "get_conversation_metadata",
        "delete_conversation",
        "cleanup_expired",
        "list_conversations",
        "setup",
        "close",
        "health_check",
    ]

    for method_name in required_methods:
        assert hasattr(storage_adapter, method_name), f"Missing method: {method_name}"
        assert callable(getattr(storage_adapter, method_name))


# =============================================================================
# BASIC CRUD OPERATIONS CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_save_and_retrieve_message(storage_adapter: StoragePort):
    """Test basic save and retrieve message operation."""
    message = MessageRecord(content="Test message", role="user")
    await storage_adapter.save_message("conv-1", message)

    messages = await storage_adapter.get_conversation("conv-1")

    assert len(messages) == 1
    assert messages[0].content == "Test message"
    assert messages[0].role == "user"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_get_nonexistent_conversation(storage_adapter: StoragePort):
    """Test that getting non-existent conversation returns empty list."""
    messages = await storage_adapter.get_conversation("non-existent")
    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_save_multiple_messages(storage_adapter: StoragePort):
    """Test saving multiple messages preserves order."""
    messages = [
        MessageRecord(content="First", role="user"),
        MessageRecord(content="Second", role="assistant"),
        MessageRecord(content="Third", role="user"),
    ]

    for msg in messages:
        await storage_adapter.save_message("conv-multi", msg)

    retrieved = await storage_adapter.get_conversation("conv-multi")

    assert len(retrieved) == 3
    assert [msg.content for msg in retrieved] == ["First", "Second", "Third"]
    assert [msg.role for msg in retrieved] == ["user", "assistant", "user"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_limit_parameter(storage_adapter: StoragePort):
    """Test that limit parameter works correctly."""
    # Save 10 messages
    for i in range(10):
        await storage_adapter.save_message(
            "conv-limit", MessageRecord(content=f"Message {i}", role="user")
        )

    # Get last 5 messages
    messages = await storage_adapter.get_conversation("conv-limit", limit=5)

    assert len(messages) == 5
    # Should get last 5 messages
    assert messages[0].content == "Message 5"
    assert messages[-1].content == "Message 9"


# =============================================================================
# METADATA OPERATIONS CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_message_metadata_preserved(storage_adapter: StoragePort):
    """Test that message metadata is preserved."""
    metadata = {
        "model": "gpt-4o-mini",
        "tokens_used": 100,
        "tool_calls": [{"name": "search"}],
    }

    message = MessageRecord(content="Test", role="assistant", metadata=metadata)
    await storage_adapter.save_message("conv-meta", message)

    messages = await storage_adapter.get_conversation("conv-meta")

    assert messages[0].metadata["model"] == "gpt-4o-mini"
    assert messages[0].metadata["tokens_used"] == 100
    assert messages[0].metadata["tool_calls"] == [{"name": "search"}]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_get_conversation_metadata(storage_adapter: StoragePort):
    """Test getting conversation metadata."""
    # Save a message (creates conversation)
    await storage_adapter.save_message(
        "conv-123", MessageRecord(content="Test", role="user"), user_id="user-456"
    )

    # Get metadata
    metadata = await storage_adapter.get_conversation_metadata("conv-123")

    assert metadata is not None
    assert metadata.conversation_id == "conv-123"
    assert metadata.user_id == "user-456"
    assert metadata.platform == "api"  # Default


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_get_nonexistent_conversation_metadata(
    storage_adapter: StoragePort,
):
    """Test that getting metadata for non-existent conversation returns None."""
    metadata = await storage_adapter.get_conversation_metadata("non-existent")
    assert metadata is None


# =============================================================================
# DELETION CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_delete_conversation(storage_adapter: StoragePort):
    """Test deleting a conversation."""
    # Create conversation
    for i in range(3):
        await storage_adapter.save_message(
            "conv-delete", MessageRecord(content=f"Msg {i}", role="user")
        )

    messages_before = await storage_adapter.get_conversation("conv-delete")
    assert len(messages_before) == 3

    # Delete
    result = await storage_adapter.delete_conversation("conv-delete")
    assert result is True

    # Verify deleted
    messages_after = await storage_adapter.get_conversation("conv-delete")
    assert messages_after == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_delete_nonexistent_conversation(storage_adapter: StoragePort):
    """Test deleting non-existent conversation returns False."""
    result = await storage_adapter.delete_conversation("non-existent")
    assert result is False


# =============================================================================
# LIST CONVERSATIONS CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_list_conversations(storage_adapter: StoragePort):
    """Test listing all conversations."""
    # Create multiple conversations
    for i in range(5):
        await storage_adapter.save_message(
            f"conv-{i}", MessageRecord(content="Test", role="user")
        )

    conversations = await storage_adapter.list_conversations()

    assert len(conversations) >= 5  # At least 5 (may have more from other tests)
    conv_ids = [c.conversation_id for c in conversations]
    for i in range(5):
        assert f"conv-{i}" in conv_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_list_conversations_filtered_by_user(
    storage_adapter: StoragePort,
):
    """Test listing conversations filtered by user_id."""
    # Create conversations for different users
    await storage_adapter.save_message(
        "conv-alice-1", MessageRecord(content="Test", role="user"), user_id="alice"
    )
    await storage_adapter.save_message(
        "conv-alice-2", MessageRecord(content="Test", role="user"), user_id="alice"
    )
    await storage_adapter.save_message(
        "conv-bob-1", MessageRecord(content="Test", role="user"), user_id="bob"
    )

    # Filter by alice
    alice_convs = await storage_adapter.list_conversations(user_id="alice")
    alice_ids = [c.conversation_id for c in alice_convs]

    assert "conv-alice-1" in alice_ids
    assert "conv-alice-2" in alice_ids
    assert "conv-bob-1" not in alice_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_list_conversations_with_limit(storage_adapter: StoragePort):
    """Test listing conversations with limit."""
    # Create 10 conversations
    for i in range(10):
        await storage_adapter.save_message(
            f"conv-limit-{i}", MessageRecord(content="Test", role="user")
        )

    # Get only 5
    conversations = await storage_adapter.list_conversations(limit=5)

    assert len(conversations) == 5


# =============================================================================
# LIFECYCLE METHODS CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_setup_is_idempotent(storage_adapter: StoragePort):
    """Test that setup() can be called multiple times without error."""
    await storage_adapter.setup()
    await storage_adapter.setup()
    await storage_adapter.setup()

    # Should not error
    health = await storage_adapter.health_check()
    assert health is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_health_check(storage_adapter: StoragePort):
    """Test that health_check() returns True."""
    health = await storage_adapter.health_check()
    assert health is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_close_is_idempotent(storage_adapter: StoragePort):
    """Test that close() can be called multiple times without error."""
    # Save some data first
    await storage_adapter.save_message(
        "conv-close", MessageRecord(content="Test", role="user")
    )

    # Close multiple times
    await storage_adapter.close()
    await storage_adapter.close()
    await storage_adapter.close()

    # Should not error


# =============================================================================
# TIMESTAMP CONSISTENCY CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_message_timestamps_are_timezone_aware(
    storage_adapter: StoragePort,
):
    """Test that all timestamps are timezone-aware."""
    message = MessageRecord(content="Test", role="user")
    await storage_adapter.save_message("conv-tz", message)

    messages = await storage_adapter.get_conversation("conv-tz")

    assert messages[0].created_at.tzinfo is not None
    assert messages[0].created_at.tzinfo == timezone.utc


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_conversation_timestamps_are_timezone_aware(
    storage_adapter: StoragePort,
):
    """Test that conversation timestamps are timezone-aware."""
    await storage_adapter.save_message(
        "conv-tz-meta", MessageRecord(content="Test", role="user")
    )

    metadata = await storage_adapter.get_conversation_metadata("conv-tz-meta")

    assert metadata is not None
    assert metadata.created_at.tzinfo is not None
    assert metadata.updated_at.tzinfo is not None


# =============================================================================
# DATA ISOLATION CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_conversations_are_isolated(storage_adapter: StoragePort):
    """Test that different conversations don't interfere with each other."""
    # Save to different conversations
    await storage_adapter.save_message(
        "conv-A", MessageRecord(content="Message A", role="user")
    )
    await storage_adapter.save_message(
        "conv-B", MessageRecord(content="Message B", role="user")
    )
    await storage_adapter.save_message(
        "conv-A", MessageRecord(content="Message A2", role="assistant")
    )

    # Verify isolation
    messages_a = await storage_adapter.get_conversation("conv-A")
    messages_b = await storage_adapter.get_conversation("conv-B")

    assert len(messages_a) == 2
    assert len(messages_b) == 1
    assert messages_a[0].content == "Message A"
    assert messages_a[1].content == "Message A2"
    assert messages_b[0].content == "Message B"


# =============================================================================
# SPECIAL CHARACTERS AND EDGE CASES CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_special_characters_in_content(storage_adapter: StoragePort):
    """Test that special characters are handled correctly."""
    special_content = "Hello 'world' \"test\" \n\t\r emoji 🚀 < > & % $"
    message = MessageRecord(content=special_content, role="user")

    await storage_adapter.save_message("conv-special", message)

    messages = await storage_adapter.get_conversation("conv-special")
    # Allow for minor differences in null byte handling
    assert messages[0].content.replace("\x00", "") == special_content.replace(
        "\x00", ""
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_long_message_content(storage_adapter: StoragePort):
    """Test handling of very long message content."""
    long_content = "x" * 10_000  # 10KB message
    message = MessageRecord(content=long_content, role="user")

    await storage_adapter.save_message("conv-long", message)

    messages = await storage_adapter.get_conversation("conv-long")
    assert len(messages[0].content) == 10_000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_null_user_id(storage_adapter: StoragePort):
    """Test that null user_id is handled correctly."""
    message = MessageRecord(content="Anonymous", role="user")
    await storage_adapter.save_message("conv-anon", message, user_id=None)

    messages = await storage_adapter.get_conversation("conv-anon")
    assert len(messages) == 1

    metadata = await storage_adapter.get_conversation_metadata("conv-anon")
    assert metadata is not None
    # user_id can be None
    assert metadata.user_id is None


# =============================================================================
# RETURN TYPE CONTRACT
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_get_conversation_returns_list_of_message_records(
    storage_adapter: StoragePort,
):
    """Test that get_conversation returns list of MessageRecord objects."""
    await storage_adapter.save_message(
        "conv-types", MessageRecord(content="Test", role="user")
    )

    messages = await storage_adapter.get_conversation("conv-types")

    assert isinstance(messages, list)
    assert all(isinstance(msg, MessageRecord) for msg in messages)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_list_conversations_returns_list_of_conversation_records(
    storage_adapter: StoragePort,
):
    """Test that list_conversations returns list of ConversationRecord objects."""
    await storage_adapter.save_message(
        "conv-list-type", MessageRecord(content="Test", role="user")
    )

    conversations = await storage_adapter.list_conversations()

    assert isinstance(conversations, list)
    assert all(isinstance(conv, ConversationRecord) for conv in conversations)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_get_conversation_metadata_returns_conversation_record_or_none(
    storage_adapter: StoragePort,
):
    """Test that get_conversation_metadata returns ConversationRecord or None."""
    # Existing conversation
    await storage_adapter.save_message(
        "conv-meta-type", MessageRecord(content="Test", role="user")
    )

    metadata = await storage_adapter.get_conversation_metadata("conv-meta-type")
    assert isinstance(metadata, ConversationRecord)

    # Non-existent conversation
    metadata_none = await storage_adapter.get_conversation_metadata("non-existent-type")
    assert metadata_none is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_delete_conversation_returns_bool(storage_adapter: StoragePort):
    """Test that delete_conversation returns bool."""
    # Existing conversation
    await storage_adapter.save_message(
        "conv-del-type", MessageRecord(content="Test", role="user")
    )

    result_true = await storage_adapter.delete_conversation("conv-del-type")
    assert isinstance(result_true, bool)
    assert result_true is True

    # Non-existent conversation
    result_false = await storage_adapter.delete_conversation("non-existent-del")
    assert isinstance(result_false, bool)
    assert result_false is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_cleanup_expired_returns_int(storage_adapter: StoragePort):
    """Test that cleanup_expired returns int."""
    result = await storage_adapter.cleanup_expired(ttl_minutes=30)

    assert isinstance(result, int)
    assert result >= 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contract_health_check_returns_bool(storage_adapter: StoragePort):
    """Test that health_check returns bool."""
    result = await storage_adapter.health_check()

    assert isinstance(result, bool)
