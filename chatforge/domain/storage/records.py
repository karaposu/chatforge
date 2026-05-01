"""
Domain Records for Chatforge Storage.

Pure dataclass types with no I/O dependencies. Used by:
- Port interfaces (abstract repository contracts)
- Adapter implementations (mapped to/from ORM models)
- Services (business logic operates on these)

Example:
    from chatforge.domain.storage import ChatRecord, MessageRecord

    chat = ChatRecord(title="My Chat")
    message = MessageRecord(content="Hello!", role="user")
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, TypedDict


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime for dataclass defaults."""
    return datetime.now(timezone.utc)


# =============================================================================
# TypedDict Metadata Types
# =============================================================================


class MessageMetadata(TypedDict, total=False):
    """Type-safe metadata for messages. All fields optional."""
    tool_calls: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    reactions: dict[str, int]
    edit_history: list[dict[str, Any]]
    model: str
    tokens_used: int
    trace_id: str


class ChatMetadata(TypedDict, total=False):
    """Type-safe metadata for chats. All fields optional."""
    source: str
    tags: list[str]
    resolved: bool
    custom: dict[str, Any]


class TokenUsage(TypedDict, total=False):
    """Token usage breakdown."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    by_model: dict[str, dict[str, int]]


# =============================================================================
# Chat & Participant Records
# =============================================================================


@dataclass
class ChatRecord:
    """Record of a chat session. Ownership via participants, not user_id."""
    id: int | str | None = None
    title: str | None = None
    system_prompt: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: ChatMetadata = field(default_factory=dict)  # type: ignore[assignment]
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "system_prompt": self.system_prompt,
            "settings": self.settings,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


@dataclass
class ParticipantRecord:
    """Record of a chat participant (human, AI, bot, system)."""
    chat_id: int | str
    participant_type: str
    display_name: str
    id: int | str | None = None
    external_id: str | None = None
    role_in_chat: str = "member"
    metadata: dict[str, Any] = field(default_factory=dict)
    joined_at: datetime = field(default_factory=_utc_now)
    left_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "participant_type": self.participant_type,
            "external_id": self.external_id,
            "display_name": self.display_name,
            "role_in_chat": self.role_in_chat,
            "metadata": self.metadata,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }


# =============================================================================
# Message Records
# =============================================================================


@dataclass
class MessageRecord:
    """Record of a single message. sender_name is a SNAPSHOT at send time."""
    content: str
    role: str
    id: int | str | None = None
    chat_id: int | str | None = None
    participant_id: int | str | None = None
    parent_id: int | str | None = None
    sender_name: str | None = None
    content_format: str = "text"
    message_type: str = "user"
    transcription: str | None = None
    token_count: int | None = None
    thumbs_up_count: int = 0
    thumbs_down_count: int = 0
    text_feedback: str | None = None
    metadata: MessageMetadata = field(default_factory=dict)  # type: ignore[assignment]
    created_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "chat_id": self.chat_id,
            "participant_id": self.participant_id, "parent_id": self.parent_id,
            "sender_name": self.sender_name, "role": self.role,
            "content": self.content, "content_format": self.content_format,
            "message_type": self.message_type, "transcription": self.transcription,
            "token_count": self.token_count,
            "thumbs_up_count": self.thumbs_up_count,
            "thumbs_down_count": self.thumbs_down_count,
            "text_feedback": self.text_feedback, "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def to_llm_format(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class AttachmentRecord:
    """Record of a file attachment."""
    message_id: int | str
    filename: str
    id: int | str | None = None
    file_type: str | None = None
    file_size: int | None = None
    storage_path: str | None = None
    transcription: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "message_id": self.message_id,
            "filename": self.filename, "file_type": self.file_type,
            "file_size": self.file_size, "storage_path": self.storage_path,
            "transcription": self.transcription, "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Tool Call Records
# =============================================================================


@dataclass
class ToolCallRecord:
    """Record of a tool/function invocation."""
    tool_name: str
    input_params: dict[str, Any]
    id: int | str | None = None
    message_id: int | str | None = None
    run_id: int | str | None = None
    tool_call_id: str | None = None
    agent_name: str | None = None
    tool_version: str | None = None
    output_data: dict[str, Any] | None = None
    status: str = "pending"
    error_message: str | None = None
    execution_time_ms: int | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "message_id": self.message_id,
            "run_id": self.run_id, "tool_call_id": self.tool_call_id,
            "agent_name": self.agent_name, "tool_name": self.tool_name,
            "tool_version": self.tool_version, "input_params": self.input_params,
            "output_data": self.output_data, "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# =============================================================================
# Agent Run Records
# =============================================================================


@dataclass
class AgentRunRecord:
    """Record of an agent execution session."""
    agent_name: str
    chat_id: int | str
    id: int | str | None = None
    trigger_message_id: int | str | None = None
    agent_version: str | None = None
    model_name: str | None = None
    status: str = "running"
    input_data: dict[str, Any] | None = None
    final_result: dict[str, Any] | None = None
    error_message: str | None = None
    total_steps: int = 0
    total_tool_calls: int = 0
    token_usage: TokenUsage = field(default_factory=dict)  # type: ignore[assignment]
    cost: Decimal | None = None
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "chat_id": self.chat_id,
            "trigger_message_id": self.trigger_message_id,
            "agent_name": self.agent_name, "agent_version": self.agent_version,
            "model_name": self.model_name, "status": self.status,
            "input_data": self.input_data, "final_result": self.final_result,
            "error_message": self.error_message, "total_steps": self.total_steps,
            "total_tool_calls": self.total_tool_calls,
            "token_usage": self.token_usage,
            "cost": float(self.cost) if self.cost else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


# =============================================================================
# LLM Call Records
# =============================================================================


@dataclass
class LLMCallRecord:
    """A single LLM model invocation within an agent run."""
    id: int | str | None = None
    run_id: int | str | None = None
    agent_name: str = ""
    model_name: str | None = None
    call_index: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    visible_tokens: int = 0
    elapsed_s: float | None = None
    response_text: str | None = None
    has_tool_calls: bool = False
    tool_names: list[str] | None = None
    tool_call_ids: list[str] | None = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "run_id": self.run_id,
            "agent_name": self.agent_name, "model_name": self.model_name,
            "call_index": self.call_index,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "visible_tokens": self.visible_tokens,
            "elapsed_s": self.elapsed_s, "response_text": self.response_text,
            "has_tool_calls": self.has_tool_calls,
            "tool_names": self.tool_names,
            "tool_call_ids": self.tool_call_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Profiling Data Extraction Records
# =============================================================================


@dataclass
class ProfilingDataExtractionRun:
    """Record of a profiling data extraction operation."""
    id: int | str | None = None
    user_id: str = ""
    chat_id: int | str | None = None
    status: str = "pending"
    error: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    model_used: str | None = None
    message_count: int = 0
    message_id_range: dict[str, Any] | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "user_id": self.user_id, "chat_id": self.chat_id,
            "status": self.status, "error": self.error, "config": self.config,
            "model_used": self.model_used, "message_count": self.message_count,
            "message_id_range": self.message_id_range,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ExtractedProfilingData:
    """Extracted profiling data with full traceability."""
    id: int | str | None = None
    extraction_run_id: int | str | None = None
    user_id: str = ""
    chat_id: int | str | None = None
    source_message_ids: list[int | str] = field(default_factory=list)
    source_quotes: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "extraction_run_id": self.extraction_run_id,
            "user_id": self.user_id, "chat_id": self.chat_id,
            "source_message_ids": self.source_message_ids,
            "source_quotes": self.source_quotes, "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Legacy Compatibility
# =============================================================================

ConversationRecord = ChatRecord
ConversationMetadata = ChatMetadata
