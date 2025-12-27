"""
Test Storage Models (Layer 1: Pure Dataclass Logic).

This module tests MessageRecord and ConversationRecord dataclasses
without any storage operations. These are pure data structures with
no dependencies.

Test Strategy:
- Test dataclass creation and defaults
- Test to_dict() conversion
- Test datetime handling (timezone-aware)
- Test metadata typing
- Test field validation

Note: No async operations needed - these are pure data structures.
"""

from datetime import datetime, timezone

import pytest

from chatforge.ports.storage import (
    ConversationMetadata,
    ConversationRecord,
    MessageMetadata,
    MessageRecord,
)


# =============================================================================
# MESSAGE RECORD TESTS
# =============================================================================

@pytest.mark.unit
def test_message_record_creation():
    """Test basic MessageRecord creation."""
    message = MessageRecord(
        content="Hello, world!",
        role="user"
    )

    assert message.content == "Hello, world!"
    assert message.role == "user"
    assert isinstance(message.created_at, datetime)
    assert message.created_at.tzinfo is not None  # Must be timezone-aware
    assert message.metadata == {}


@pytest.mark.unit
def test_message_record_with_metadata():
    """Test MessageRecord with metadata."""
    metadata: MessageMetadata = {
        "tool_calls": [{"name": "search", "args": {"query": "test"}}],
        "model": "gpt-4o-mini",
        "tokens_used": 150,
    }

    message = MessageRecord(
        content="Search result",
        role="assistant",
        metadata=metadata
    )

    assert message.metadata["tool_calls"] == [{"name": "search", "args": {"query": "test"}}]
    assert message.metadata["model"] == "gpt-4o-mini"
    assert message.metadata["tokens_used"] == 150


@pytest.mark.unit
def test_message_record_to_dict():
    """Test MessageRecord.to_dict() conversion."""
    message = MessageRecord(
        content="Test message",
        role="user",
        metadata={"trace_id": "abc123"}
    )

    result = message.to_dict()

    # to_dict() only includes role and content (for agent consumption)
    assert result == {
        "role": "user",
        "content": "Test message",
    }
    # Metadata is NOT included in to_dict()
    assert "metadata" not in result


@pytest.mark.unit
def test_message_record_assistant_role():
    """Test MessageRecord with assistant role."""
    message = MessageRecord(
        content="I can help with that",
        role="assistant"
    )

    assert message.role == "assistant"
    assert message.to_dict()["role"] == "assistant"


@pytest.mark.unit
def test_message_record_custom_timestamp():
    """Test MessageRecord with custom timestamp."""
    custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    message = MessageRecord(
        content="Old message",
        role="user",
        created_at=custom_time
    )

    assert message.created_at == custom_time
    assert message.created_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_message_record_timezone_aware():
    """Test that created_at is always timezone-aware."""
    message = MessageRecord(content="Test", role="user")

    # Should have timezone info (UTC)
    assert message.created_at.tzinfo is not None
    assert message.created_at.tzinfo == timezone.utc


# =============================================================================
# MESSAGE METADATA TESTS
# =============================================================================

@pytest.mark.unit
def test_message_metadata_all_fields():
    """Test MessageMetadata with all fields."""
    metadata: MessageMetadata = {
        "tool_calls": [{"name": "calculator", "args": {"x": 10}}],
        "tool_outputs": [{"result": 100}],
        "attachments": ["file1.pdf", "image.png"],
        "model": "claude-3-opus",
        "tokens_used": 500,
        "trace_id": "trace-abc-123",
    }

    # All fields should be accessible
    assert len(metadata["tool_calls"]) == 1
    assert metadata["model"] == "claude-3-opus"
    assert metadata["tokens_used"] == 500


@pytest.mark.unit
def test_message_metadata_partial_fields():
    """Test MessageMetadata with partial fields (TypedDict total=False)."""
    # Only some fields provided
    metadata: MessageMetadata = {
        "model": "gpt-4o",
        "tokens_used": 100,
    }

    assert metadata["model"] == "gpt-4o"
    assert "tool_calls" not in metadata  # Optional field


@pytest.mark.unit
def test_message_metadata_empty():
    """Test empty MessageMetadata."""
    metadata: MessageMetadata = {}

    # Should be valid (all fields are optional)
    assert metadata == {}


# =============================================================================
# CONVERSATION RECORD TESTS
# =============================================================================

@pytest.mark.unit
def test_conversation_record_creation():
    """Test basic ConversationRecord creation."""
    conversation = ConversationRecord(
        conversation_id="conv-123",
        user_id="user-456"
    )

    assert conversation.conversation_id == "conv-123"
    assert conversation.user_id == "user-456"
    assert conversation.platform == "api"  # Default
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.updated_at, datetime)
    assert conversation.metadata == {}


@pytest.mark.unit
def test_conversation_record_with_platform():
    """Test ConversationRecord with custom platform."""
    conversation = ConversationRecord(
        conversation_id="conv-slack-1",
        user_id="user-1",
        platform="slack"
    )

    assert conversation.platform == "slack"


@pytest.mark.unit
def test_conversation_record_nullable_user():
    """Test ConversationRecord with null user_id."""
    conversation = ConversationRecord(
        conversation_id="conv-anonymous",
        user_id=None
    )

    assert conversation.user_id is None
    assert conversation.conversation_id == "conv-anonymous"


@pytest.mark.unit
def test_conversation_record_with_metadata():
    """Test ConversationRecord with metadata."""
    metadata: ConversationMetadata = {
        "source": "web-chat",
        "tags": ["support", "billing"],
        "resolved": False,
        "custom": {"priority": "high"}
    }

    conversation = ConversationRecord(
        conversation_id="conv-support-1",
        user_id="user-123",
        metadata=metadata
    )

    assert conversation.metadata["source"] == "web-chat"
    assert conversation.metadata["tags"] == ["support", "billing"]
    assert conversation.metadata["resolved"] is False
    assert conversation.metadata["custom"]["priority"] == "high"


@pytest.mark.unit
def test_conversation_record_timestamps_timezone_aware():
    """Test that timestamps are timezone-aware."""
    conversation = ConversationRecord(
        conversation_id="conv-1",
        user_id="user-1"
    )

    assert conversation.created_at.tzinfo is not None
    assert conversation.updated_at.tzinfo is not None
    assert conversation.created_at.tzinfo == timezone.utc
    assert conversation.updated_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_conversation_record_custom_timestamps():
    """Test ConversationRecord with custom timestamps."""
    created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2024, 1, 2, 14, 30, 0, tzinfo=timezone.utc)

    conversation = ConversationRecord(
        conversation_id="conv-1",
        user_id="user-1",
        created_at=created,
        updated_at=updated
    )

    assert conversation.created_at == created
    assert conversation.updated_at == updated


# =============================================================================
# CONVERSATION METADATA TESTS
# =============================================================================

@pytest.mark.unit
def test_conversation_metadata_all_fields():
    """Test ConversationMetadata with all fields."""
    metadata: ConversationMetadata = {
        "source": "slack",
        "tags": ["urgent", "bug-report"],
        "resolved": True,
        "custom": {
            "department": "engineering",
            "severity": "high",
            "assigned_to": "john@example.com"
        }
    }

    assert metadata["source"] == "slack"
    assert len(metadata["tags"]) == 2
    assert metadata["resolved"] is True
    assert metadata["custom"]["department"] == "engineering"


@pytest.mark.unit
def test_conversation_metadata_partial_fields():
    """Test ConversationMetadata with partial fields."""
    metadata: ConversationMetadata = {
        "source": "api",
        "tags": ["general"]
    }

    assert metadata["source"] == "api"
    assert "resolved" not in metadata  # Optional
    assert "custom" not in metadata  # Optional


@pytest.mark.unit
def test_conversation_metadata_empty():
    """Test empty ConversationMetadata."""
    metadata: ConversationMetadata = {}

    # Should be valid (all fields are optional)
    assert metadata == {}


# =============================================================================
# DATACLASS IMMUTABILITY TESTS
# =============================================================================

@pytest.mark.unit
def test_message_record_is_mutable():
    """Test that MessageRecord fields can be modified (dataclass default)."""
    message = MessageRecord(content="Original", role="user")

    # Dataclasses are mutable by default
    message.content = "Modified"
    assert message.content == "Modified"


@pytest.mark.unit
def test_conversation_record_is_mutable():
    """Test that ConversationRecord fields can be modified."""
    conversation = ConversationRecord(
        conversation_id="conv-1",
        user_id="user-1"
    )

    # Update timestamp (common pattern in storage adapters)
    new_time = datetime(2024, 2, 1, 10, 0, 0, tzinfo=timezone.utc)
    conversation.updated_at = new_time

    assert conversation.updated_at == new_time


# =============================================================================
# INTEGRATION SCENARIO TESTS
# =============================================================================

@pytest.mark.unit
def test_message_record_for_agent_consumption():
    """Test MessageRecord.to_dict() produces agent-ready format."""
    messages = [
        MessageRecord(content="What's the weather?", role="user"),
        MessageRecord(content="It's sunny today", role="assistant"),
        MessageRecord(content="Thanks!", role="user"),
    ]

    # Convert to agent format
    agent_messages = [msg.to_dict() for msg in messages]

    assert agent_messages == [
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "It's sunny today"},
        {"role": "user", "content": "Thanks!"},
    ]


@pytest.mark.unit
def test_conversation_with_rich_metadata():
    """Test realistic conversation with comprehensive metadata."""
    conversation = ConversationRecord(
        conversation_id="conv-support-12345",
        user_id="customer-67890",
        platform="zendesk",
        metadata={
            "source": "web-widget",
            "tags": ["billing", "subscription", "urgent"],
            "resolved": False,
            "custom": {
                "ticket_id": "TICK-001",
                "priority": "high",
                "assigned_agent": "agent-42",
                "sla_deadline": "2024-01-15T17:00:00Z",
            }
        }
    )

    assert conversation.platform == "zendesk"
    assert "urgent" in conversation.metadata["tags"]
    assert conversation.metadata["custom"]["priority"] == "high"


@pytest.mark.unit
def test_message_with_tool_execution_metadata():
    """Test message with tool call metadata."""
    message = MessageRecord(
        content="I'll search for that information.",
        role="assistant",
        metadata={
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": '{"query": "Python async best practices"}'
                    }
                }
            ],
            "tool_outputs": [
                {
                    "tool_call_id": "call_abc123",
                    "output": "Found 10 results about Python async..."
                }
            ],
            "model": "gpt-4o",
            "tokens_used": 250
        }
    )

    assert len(message.metadata["tool_calls"]) == 1
    assert message.metadata["tool_calls"][0]["function"]["name"] == "web_search"
    assert len(message.metadata["tool_outputs"]) == 1


@pytest.mark.unit
def test_default_timestamps_are_recent():
    """Test that default timestamps are recent (within last second)."""
    before = datetime.now(timezone.utc)
    message = MessageRecord(content="Test", role="user")
    after = datetime.now(timezone.utc)

    # Timestamp should be between before and after
    assert before <= message.created_at <= after


@pytest.mark.unit
def test_conversation_and_message_timestamp_consistency():
    """Test that conversation and message timestamps can be compared."""
    conversation = ConversationRecord(
        conversation_id="conv-1",
        user_id="user-1"
    )

    message = MessageRecord(content="Test", role="user")

    # Both should be timezone-aware and comparable
    assert conversation.created_at.tzinfo == message.created_at.tzinfo
    # Message should be created around the same time as conversation
    time_diff = abs((conversation.created_at - message.created_at).total_seconds())
    assert time_diff < 1.0  # Less than 1 second difference
