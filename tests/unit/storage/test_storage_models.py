"""
Test storage domain records.

Pure dataclass behavior — creation, defaults, to_dict serialization,
and to_llm_format conversion. No I/O.
"""

from datetime import datetime, timezone

import pytest

from chatforge.domain.storage import (
    ChatMetadata,
    ChatRecord,
    LLMCallRecord,
    MessageMetadata,
    MessageRecord,
    ParticipantRecord,
    ToolCallRecord,
    AgentRunRecord,
)


# =============================================================================
# MessageRecord
# =============================================================================


@pytest.mark.unit
def test_message_record_creation():
    msg = MessageRecord(content="Hello, world!", role="user")
    assert msg.content == "Hello, world!"
    assert msg.role == "user"
    assert msg.id is None
    assert msg.chat_id is None
    assert msg.metadata == {}
    assert msg.created_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_message_record_with_metadata():
    metadata: MessageMetadata = {
        "tool_calls": [{"name": "search", "args": {"query": "test"}}],
        "model": "gpt-4o-mini",
        "tokens_used": 150,
    }
    msg = MessageRecord(content="Search result", role="assistant", metadata=metadata)
    assert msg.metadata["model"] == "gpt-4o-mini"
    assert msg.metadata["tokens_used"] == 150


@pytest.mark.unit
def test_message_record_to_dict_full_serialization():
    msg = MessageRecord(content="Test", role="user", metadata={"trace_id": "abc123"})
    d = msg.to_dict()
    # Full serialization includes all fields
    assert d["role"] == "user"
    assert d["content"] == "Test"
    assert d["metadata"] == {"trace_id": "abc123"}
    assert "created_at" in d
    assert d["id"] is None
    assert d["chat_id"] is None


@pytest.mark.unit
def test_message_record_to_llm_format():
    msg = MessageRecord(content="Test", role="user", metadata={"trace_id": "abc"})
    assert msg.to_llm_format() == {"role": "user", "content": "Test"}


@pytest.mark.unit
def test_message_record_custom_timestamp():
    custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    msg = MessageRecord(content="Old", role="user", created_at=custom_time)
    assert msg.created_at == custom_time


@pytest.mark.unit
def test_message_record_for_agent_consumption():
    msgs = [
        MessageRecord(content="What's the weather?", role="user"),
        MessageRecord(content="It's sunny today", role="assistant"),
    ]
    assert [m.to_llm_format() for m in msgs] == [
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "It's sunny today"},
    ]


# =============================================================================
# ChatRecord
# =============================================================================


@pytest.mark.unit
def test_chat_record_creation_defaults():
    chat = ChatRecord()
    assert chat.id is None
    assert chat.title is None
    assert chat.system_prompt is None
    assert chat.settings == {}
    assert chat.metadata == {}
    assert chat.deleted_at is None
    assert chat.created_at.tzinfo == timezone.utc


@pytest.mark.unit
def test_chat_record_with_fields():
    chat = ChatRecord(
        id=1,
        title="Support Conversation",
        system_prompt="You are helpful.",
        settings={"temperature": 0.7},
    )
    assert chat.id == 1
    assert chat.title == "Support Conversation"
    assert chat.settings["temperature"] == 0.7


@pytest.mark.unit
def test_chat_record_with_metadata():
    metadata: ChatMetadata = {
        "source": "web-chat",
        "tags": ["support", "billing"],
        "resolved": False,
    }
    chat = ChatRecord(metadata=metadata)
    assert chat.metadata["source"] == "web-chat"
    assert chat.metadata["resolved"] is False


@pytest.mark.unit
def test_chat_record_to_dict():
    chat = ChatRecord(id=42, title="Demo")
    d = chat.to_dict()
    assert d["id"] == 42
    assert d["title"] == "Demo"
    assert "created_at" in d
    assert d["deleted_at"] is None


# =============================================================================
# ParticipantRecord
# =============================================================================


@pytest.mark.unit
def test_participant_record_creation():
    p = ParticipantRecord(
        chat_id=1, participant_type="user", display_name="Alice",
    )
    assert p.chat_id == 1
    assert p.participant_type == "user"
    assert p.display_name == "Alice"
    assert p.role_in_chat == "member"
    assert p.left_at is None


@pytest.mark.unit
def test_participant_record_owner_with_external_id():
    p = ParticipantRecord(
        chat_id=1, participant_type="user", display_name="Alice",
        external_id="user-123", role_in_chat="owner",
    )
    assert p.external_id == "user-123"
    assert p.role_in_chat == "owner"


# =============================================================================
# ToolCallRecord — fields added during refactor (tool_call_id, agent_name)
# =============================================================================


@pytest.mark.unit
def test_tool_call_record_with_correlation_fields():
    tc = ToolCallRecord(
        tool_name="search",
        input_params={"q": "test"},
        tool_call_id="lg_abc123",
        agent_name="orchestrator",
    )
    assert tc.tool_call_id == "lg_abc123"
    assert tc.agent_name == "orchestrator"
    assert tc.status == "pending"
    d = tc.to_dict()
    assert d["tool_call_id"] == "lg_abc123"
    assert d["agent_name"] == "orchestrator"


# =============================================================================
# AgentRunRecord — model_name field added during refactor
# =============================================================================


@pytest.mark.unit
def test_agent_run_record_with_model_name():
    run = AgentRunRecord(
        agent_name="orchestrator",
        chat_id=1,
        model_name="gpt-5",
    )
    assert run.model_name == "gpt-5"
    assert run.status == "running"
    assert run.to_dict()["model_name"] == "gpt-5"


# =============================================================================
# LLMCallRecord — new record added during refactor
# =============================================================================


@pytest.mark.unit
def test_llm_call_record_creation():
    call = LLMCallRecord(
        run_id=42,
        agent_name="content-filler",
        model_name="gpt-5",
        call_index=3,
        input_tokens=1500,
        output_tokens=200,
        elapsed_s=2.5,
        has_tool_calls=True,
        tool_names=["search", "fetch"],
        tool_call_ids=["lg_1", "lg_2"],
    )
    assert call.run_id == 42
    assert call.agent_name == "content-filler"
    assert call.input_tokens == 1500
    assert call.output_tokens == 200
    assert call.has_tool_calls is True
    assert call.tool_names == ["search", "fetch"]


@pytest.mark.unit
def test_llm_call_record_to_dict():
    call = LLMCallRecord(run_id=1, agent_name="orchestrator", model_name="gpt-5")
    d = call.to_dict()
    assert d["run_id"] == 1
    assert d["agent_name"] == "orchestrator"
    assert d["model_name"] == "gpt-5"
    assert d["input_tokens"] == 0
    assert d["has_tool_calls"] is False


# =============================================================================
# Metadata TypedDicts (total=False — all fields optional)
# =============================================================================


@pytest.mark.unit
def test_message_metadata_partial():
    metadata: MessageMetadata = {"model": "gpt-4o", "tokens_used": 100}
    assert metadata["model"] == "gpt-4o"
    assert "tool_calls" not in metadata


@pytest.mark.unit
def test_chat_metadata_partial():
    metadata: ChatMetadata = {"source": "api", "tags": ["general"]}
    assert metadata["source"] == "api"
    assert "resolved" not in metadata


# =============================================================================
# Timestamp behavior
# =============================================================================


@pytest.mark.unit
def test_default_timestamps_are_recent():
    before = datetime.now(timezone.utc)
    msg = MessageRecord(content="Test", role="user")
    after = datetime.now(timezone.utc)
    assert before <= msg.created_at <= after


@pytest.mark.unit
def test_records_share_utc_timezone():
    chat = ChatRecord()
    msg = MessageRecord(content="Test", role="user")
    assert chat.created_at.tzinfo == msg.created_at.tzinfo == timezone.utc
