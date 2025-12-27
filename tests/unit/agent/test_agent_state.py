"""
Unit tests for AgentState.

Tests the pure state structure without any agent logic.
This is Layer 1 testing - pure data structures and types.
"""

import pytest

from chatforge.services.agent.state import AgentState


# =============================================================================
# LAYER 1: Pure Logic Tests (State Structure)
# =============================================================================


@pytest.mark.unit
def test_agent_state_creation_minimal():
    """Test creating AgentState with only required fields."""
    state: AgentState = {
        "messages": [{"role": "user", "content": "Hello"}],
    }

    assert "messages" in state
    assert len(state["messages"]) == 1
    assert state["messages"][0]["role"] == "user"
    assert state["messages"][0]["content"] == "Hello"


@pytest.mark.unit
def test_agent_state_creation_full():
    """Test creating AgentState with all optional fields."""
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        "user_id": "user123",
        "conversation_id": "conv456",
        "metadata": {
            "platform": "test",
            "timestamp": "2024-12-01T00:00:00Z",
        },
    }

    assert state["messages"] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    assert state["user_id"] == "user123"
    assert state["conversation_id"] == "conv456"
    assert state["metadata"]["platform"] == "test"


@pytest.mark.unit
def test_agent_state_optional_fields():
    """Test that all fields except messages are optional."""
    state: AgentState = {
        "messages": [],
    }

    # Should not raise KeyError
    user_id = state.get("user_id")
    conversation_id = state.get("conversation_id")
    metadata = state.get("metadata")

    assert user_id is None
    assert conversation_id is None
    assert metadata is None


@pytest.mark.unit
def test_agent_state_messages_is_list():
    """Test that messages field is a list."""
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ],
    }

    assert isinstance(state["messages"], list)
    assert len(state["messages"]) == 3


@pytest.mark.unit
def test_agent_state_metadata_is_dict():
    """Test that metadata field can hold arbitrary data."""
    state: AgentState = {
        "messages": [],
        "metadata": {
            "custom_field": "custom_value",
            "nested": {
                "key": "value",
            },
            "list_data": [1, 2, 3],
        },
    }

    assert isinstance(state["metadata"], dict)
    assert state["metadata"]["custom_field"] == "custom_value"
    assert state["metadata"]["nested"]["key"] == "value"
    assert state["metadata"]["list_data"] == [1, 2, 3]


@pytest.mark.unit
def test_agent_state_empty_messages():
    """Test that messages can be an empty list."""
    state: AgentState = {
        "messages": [],
    }

    assert state["messages"] == []
    assert len(state["messages"]) == 0


@pytest.mark.unit
def test_agent_state_update():
    """Test updating AgentState fields."""
    state: AgentState = {
        "messages": [],
    }

    # Add user_id
    state["user_id"] = "user123"
    assert state["user_id"] == "user123"

    # Add conversation_id
    state["conversation_id"] = "conv456"
    assert state["conversation_id"] == "conv456"

    # Add messages
    state["messages"].append({"role": "user", "content": "Hello"})
    assert len(state["messages"]) == 1


@pytest.mark.unit
def test_agent_state_message_structure():
    """Test that message dictionaries have correct structure."""
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
        ],
    }

    # Check first message
    msg1 = state["messages"][0]
    assert "role" in msg1
    assert "content" in msg1
    assert msg1["role"] == "user"
    assert isinstance(msg1["content"], str)

    # Check second message
    msg2 = state["messages"][1]
    assert msg2["role"] == "assistant"
    assert isinstance(msg2["content"], str)


@pytest.mark.unit
def test_agent_state_can_be_copied():
    """Test that AgentState can be copied."""
    original: AgentState = {
        "messages": [{"role": "user", "content": "Hello"}],
        "user_id": "user123",
    }

    # Create a copy
    copy = original.copy()

    # Modify copy
    copy["user_id"] = "user456"
    copy["messages"].append({"role": "assistant", "content": "Hi"})

    # Original should be unchanged (shallow copy, so messages list is shared)
    assert original["user_id"] == "user123"
    # Note: messages list is shared in shallow copy
    assert len(original["messages"]) == 2


@pytest.mark.unit
def test_agent_state_conversation_tracking():
    """Test using AgentState for multi-turn conversation."""
    state: AgentState = {
        "messages": [],
        "conversation_id": "conv123",
        "user_id": "user456",
        "metadata": {"turn_count": 0},
    }

    # Turn 1
    state["messages"].append({"role": "user", "content": "What is 2+2?"})
    state["metadata"]["turn_count"] = 1

    # Turn 2
    state["messages"].append({"role": "assistant", "content": "2+2 equals 4."})
    state["metadata"]["turn_count"] = 2

    # Turn 3
    state["messages"].append({"role": "user", "content": "Thanks!"})
    state["metadata"]["turn_count"] = 3

    assert len(state["messages"]) == 3
    assert state["metadata"]["turn_count"] == 3
    assert state["conversation_id"] == "conv123"


@pytest.mark.unit
def test_agent_state_with_complex_metadata():
    """Test AgentState with complex nested metadata."""
    state: AgentState = {
        "messages": [],
        "metadata": {
            "files": [
                {"name": "doc1.txt", "size": 1024},
                {"name": "doc2.pdf", "size": 2048},
            ],
            "gathered_info": {
                "topic": "AI",
                "sources": ["wikipedia", "arxiv"],
            },
            "flags": {
                "needs_review": True,
                "is_urgent": False,
            },
        },
    }

    assert len(state["metadata"]["files"]) == 2
    assert state["metadata"]["gathered_info"]["topic"] == "AI"
    assert state["metadata"]["flags"]["needs_review"] is True
