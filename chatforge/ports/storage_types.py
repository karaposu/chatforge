"""
Dataclass Types for Chatforge Storage Port Interface.

These types define the data structures used in the StoragePort interface.
They are decoupled from SQLAlchemy models to allow:
- In-memory adapters that don't use SQLAlchemy
- Custom adapters that map to different schemas
- Type-safe interfaces without ORM dependencies

Example:
    from chatforge.ports.storage_types import (
        MessageRecord,
        ChatRecord,
        ProfilingDataExtractionRun,
        ExtractedProfilingData,
    )

    message = MessageRecord(
        content="Hello, world!",
        role="user",
    )

    extraction_run = ProfilingDataExtractionRun(
        user_id="user-123",
        scope_type="single_chat",
        chat_id="chat-456",
    )
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
    """
    Type-safe metadata for messages.

    All fields are optional (total=False) to maintain flexibility.
    """
    tool_calls: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    reactions: dict[str, int]
    edit_history: list[dict[str, Any]]
    model: str
    tokens_used: int
    trace_id: str


class ChatMetadata(TypedDict, total=False):
    """
    Type-safe metadata for chats.

    All fields are optional (total=False) to maintain flexibility.
    """
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
# Dataclass Records
# =============================================================================


@dataclass
class ChatRecord:
    """
    Record of a chat session.

    Used in the StoragePort interface for chat operations.
    Ownership is managed through participants, not a user_id field.

    Attributes:
        id: Unique identifier (can be int or string depending on adapter)
        title: Optional display name
        system_prompt: Default system prompt
        settings: Model configuration, temperature, etc.
        metadata: App-specific extension data
        created_at: When chat was created
        updated_at: Last activity timestamp
        deleted_at: Soft delete timestamp (None = active)
    """
    id: int | str | None = None
    title: str | None = None
    system_prompt: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: ChatMetadata = field(default_factory=dict)  # type: ignore[assignment]
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
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
    """
    Record of a chat participant.

    Represents an entity (human, AI, bot, system) in a chat.
    Links to external user/agent systems via external_id.

    Attributes:
        chat_id: Parent chat identifier
        participant_type: 'user', 'assistant', 'agent', 'bot', 'system'
        display_name: Human-readable name for this participant
        id: Unique identifier
        external_id: Reference to host app's user/agent system
        role_in_chat: 'owner', 'admin', 'member', 'observer'
        metadata: App-specific data
        joined_at: When participant joined the chat
        left_at: When participant left (None = still active)
    """
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
        """Convert to dictionary."""
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


@dataclass
class MessageRecord:
    """
    Record of a single message in a conversation.

    Used in the StoragePort interface for message operations.
    sender_name is a SNAPSHOT field capturing display name at send time.

    Attributes:
        content: The message text content
        role: Message role ('user', 'assistant', 'system', 'tool')
        id: Unique identifier
        chat_id: Parent chat identifier
        participant_id: Who sent this message
        parent_id: For threaded replies
        sender_name: Display name SNAPSHOT at send time
        content_format: 'text', 'markdown', 'html', 'json'
        message_type: 'user', 'generated', 'fixed', 'edited'
        transcription: Voice transcription if applicable
        token_count: Token count for this message
        thumbs_up_count: Number of thumbs up reactions
        thumbs_down_count: Number of thumbs down reactions
        text_feedback: User-provided text feedback
        metadata: Additional data (tool calls, attachments, etc.)
        created_at: When message was sent
        deleted_at: Soft delete timestamp
    """
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
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "participant_id": self.participant_id,
            "parent_id": self.parent_id,
            "sender_name": self.sender_name,
            "role": self.role,
            "content": self.content,
            "content_format": self.content_format,
            "message_type": self.message_type,
            "transcription": self.transcription,
            "token_count": self.token_count,
            "thumbs_up_count": self.thumbs_up_count,
            "thumbs_down_count": self.thumbs_down_count,
            "text_feedback": self.text_feedback,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def to_llm_format(self) -> dict[str, str]:
        """Convert to format expected by LLM APIs."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class AttachmentRecord:
    """
    Record of a file attachment.

    Stores metadata about attached files. Actual storage is delegated to host app.

    Attributes:
        message_id: Parent message identifier
        filename: Original filename
        id: Unique identifier
        file_type: MIME type (e.g., 'image/png')
        file_size: Size in bytes
        storage_path: Path/URL to actual file
        transcription: Extracted text (OCR, audio transcription)
        metadata: Additional file metadata
        created_at: When attachment was added
    """
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
        """Convert to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "storage_path": self.storage_path,
            "transcription": self.transcription,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ToolCallRecord:
    """
    Record of a tool/function invocation.

    Used for tracking tool calls for observability and debugging.

    Attributes:
        tool_name: Name of the tool called
        input_params: Parameters passed to the tool
        id: Unique identifier
        message_id: Which message triggered this
        run_id: Part of which agent run
        tool_version: Version if tracked
        output_data: Result from the tool
        status: 'pending', 'running', 'success', 'error', 'timeout', 'cancelled'
        error_message: Error details if failed
        execution_time_ms: Duration in milliseconds
        retry_count: Number of retries
        created_at: When tool was called
        completed_at: When tool finished
    """
    tool_name: str
    input_params: dict[str, Any]
    id: int | str | None = None
    message_id: int | str | None = None
    run_id: int | str | None = None
    tool_version: str | None = None
    output_data: dict[str, Any] | None = None
    status: str = "pending"
    error_message: str | None = None
    execution_time_ms: int | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "run_id": self.run_id,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "input_params": self.input_params,
            "output_data": self.output_data,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class AgentRunRecord:
    """
    Record of an agent execution session.

    Used for tracking complete agent runs for debugging and analytics.

    Attributes:
        agent_name: Name/type of agent
        chat_id: Which chat this run belongs to
        id: Unique identifier
        trigger_message_id: Message that triggered this run
        agent_version: Version if tracked
        status: 'running', 'completed', 'failed', 'cancelled'
        input_data: Initial input to the agent
        final_result: Final output from the agent
        error_message: Error details if failed
        total_steps: Number of reasoning steps
        total_tool_calls: Number of tool calls made
        token_usage: Token consumption breakdown
        cost: Total cost in USD
        started_at: When run started
        completed_at: When run finished
        metadata: App-specific data
    """
    agent_name: str
    chat_id: int | str
    id: int | str | None = None
    trigger_message_id: int | str | None = None
    agent_version: str | None = None
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
        """Convert to dictionary."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "trigger_message_id": self.trigger_message_id,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "status": self.status,
            "input_data": self.input_data,
            "final_result": self.final_result,
            "error_message": self.error_message,
            "total_steps": self.total_steps,
            "total_tool_calls": self.total_tool_calls,
            "token_usage": self.token_usage,
            "cost": float(self.cost) if self.cost else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


# =============================================================================
# Profiling Data Extraction Records
# =============================================================================


@dataclass
class ProfilingDataExtractionRun:
    """
    Record of a profiling data extraction operation.

    Tracks each run of the extraction service, including scope,
    status, and metrics.

    Attributes:
        id: Unique identifier
        user_id: User being profiled
        chat_id: Which chat (None = all user's chats)
        status: 'pending', 'running', 'completed', 'failed'
        error: Error message if failed
        config: Extraction configuration (dimensions, thresholds)
        model_used: LLM model used for extraction
        message_count: Total messages processed
        message_id_range: Range of message IDs processed
        duration_ms: Extraction duration in milliseconds
        started_at: When extraction started
        completed_at: When extraction finished
        created_at: When record was created
    """
    id: int | str | None = None
    user_id: str = ""

    # Scope (chat_id=None means all user's chats)
    chat_id: int | str | None = None

    # Status
    status: str = "pending"
    error: str | None = None

    # Config
    config: dict[str, Any] = field(default_factory=dict)
    model_used: str | None = None

    # Metrics
    message_count: int = 0
    message_id_range: dict[str, Any] | None = None
    duration_ms: int | None = None

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "status": self.status,
            "error": self.error,
            "config": self.config,
            "model_used": self.model_used,
            "message_count": self.message_count,
            "message_id_range": self.message_id_range,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ExtractedProfilingData:
    """
    Record of extracted profiling data with full traceability.

    Each record represents a piece of profiling data extracted from
    user messages, with links back to source messages and quotes.

    The `data` field is format-agnostic - stores CPF-7 dimensions,
    confidence scores, etc. as JSON. Schema doesn't change if
    extraction format evolves.

    Attributes:
        id: Unique identifier
        extraction_run_id: Which run produced this
        user_id: User this data is about
        chat_id: Which chat this came from
        source_message_ids: Message IDs this was extracted from
        source_quotes: Exact quotes from messages
        data: Extracted profiling data (format-agnostic JSON)
        created_at: When extracted
    """
    id: int | str | None = None
    extraction_run_id: int | str | None = None
    user_id: str = ""

    # Source traceability
    chat_id: int | str | None = None
    source_message_ids: list[int | str] = field(default_factory=list)
    source_quotes: list[str] = field(default_factory=list)

    # Extracted content (format-agnostic)
    data: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "extraction_run_id": self.extraction_run_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "source_message_ids": self.source_message_ids,
            "source_quotes": self.source_quotes,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Legacy Compatibility
# =============================================================================

# For backward compatibility with existing code using ports/storage.py types
ConversationRecord = ChatRecord
ConversationMetadata = ChatMetadata
