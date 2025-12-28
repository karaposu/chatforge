"""
SQLAlchemy ORM Models for Chatforge (v2 Schema).

This module defines the database schema for chatforge's storage system:
- Chat: Conversation containers with settings
- Participant: Who is in a chat (humans, AIs, bots, etc.)
- Message: Individual messages with sender_name snapshots
- Attachment: File attachments for messages
- ToolCall: Tool invocation tracking for observability
- AgentRun: Complete agent execution sessions

Key Design Decisions:
- No User table: Chatforge doesn't own user management; links via external_id
- Participants: Both humans and AIs are first-class participants
- sender_name: Snapshot field capturing display name at send time (not denormalization)

These models can be:
1. Used directly by chatforge's SQLAlchemy adapter
2. Imported by host apps to query/join with their own tables
3. Extended by host apps for custom fields

Example:
    from chatforge.adapters.storage.models.models import Base, Chat, Participant, Message
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///chatforge.db")
    Base.metadata.create_all(engine)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

# Try to import JSON type, with fallback for older SQLAlchemy
try:
    from sqlalchemy import JSON
except ImportError:
    from sqlalchemy.types import JSON


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


Base = declarative_base()


class Chat(Base):
    """
    Conversation container.

    A chat represents a conversation session and contains multiple messages.
    Ownership is managed through the participants table (no user_id here).

    Attributes:
        id: Primary key
        title: Optional display name for the chat
        system_prompt: Default system prompt for this conversation
        settings: Flexible JSON for model config, temperature, etc.
        metadata_: App-specific extension data
        created_at: When chat was created
        updated_at: Last activity timestamp
        deleted_at: Soft delete timestamp (None = active)
    """

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    system_prompt = Column(Text, nullable=True)
    settings = Column(JSON, default=dict, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    participants = relationship(
        "Participant",
        back_populates="chat",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    agent_runs = relationship(
        "AgentRun",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_chats_created_at", "created_at"),
        Index("idx_chats_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Chat id={self.id} title={self.title!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "system_prompt": self.system_prompt,
            "settings": self.settings,
            "metadata": self.metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Participant(Base):
    """
    Chat participant - can be human, AI, bot, or system.

    This model enables multi-party chats where both humans and AIs are
    first-class participants. Links to external user systems via external_id.

    Attributes:
        id: Primary key
        chat_id: Parent chat (FK with cascade delete)
        participant_type: 'user', 'assistant', 'agent', 'bot', 'system'
        external_id: Reference to host app's user/agent system
        display_name: Human-readable name for this participant
        role_in_chat: 'owner', 'admin', 'member', 'observer'
        metadata_: App-specific data (avatar, preferences, etc.)
        joined_at: When participant joined the chat
        left_at: When participant left (None = still active)
    """

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_type = Column(String(20), nullable=False)  # user, assistant, agent, bot, system
    external_id = Column(String(64), nullable=True)  # Reference to host app's user/agent
    display_name = Column(String(100), nullable=False)
    role_in_chat = Column(String(20), default="member", nullable=False)  # owner, admin, member, observer
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    joined_at = Column(DateTime, default=_utc_now, nullable=False)
    left_at = Column(DateTime, nullable=True)

    # Relationships
    chat = relationship("Chat", back_populates="participants")
    messages = relationship("Message", back_populates="participant")

    __table_args__ = (
        Index("idx_participants_chat_id", "chat_id"),
        Index("idx_participants_external_id", "external_id"),
        Index("idx_participants_type", "participant_type"),
    )

    def __repr__(self) -> str:
        return f"<Participant id={self.id} type={self.participant_type} name={self.display_name!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "participant_type": self.participant_type,
            "external_id": self.external_id,
            "display_name": self.display_name,
            "role_in_chat": self.role_in_chat,
            "metadata": self.metadata_,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }


class Message(Base):
    """
    Individual message in a conversation.

    Supports threading via parent_id for reply chains.
    sender_name is a SNAPSHOT field - captures the participant's display name
    at the time the message was sent, for historical accuracy.

    Attributes:
        id: Primary key
        chat_id: Parent chat (FK with cascade delete)
        participant_id: Who sent this message (FK to participants)
        parent_id: For threaded replies (self-referential FK)
        sender_name: Display name SNAPSHOT at time of message
        role: 'user', 'assistant', 'system', or 'tool'
        content: The message text
        content_format: 'text', 'markdown', 'html', 'json'
        message_type: 'user', 'generated', 'fixed', 'edited'
        transcription: Original voice transcription if applicable
        token_count: Token count for this message
        thumbs_up_count: Number of thumbs up reactions
        thumbs_down_count: Number of thumbs down reactions
        text_feedback: User-provided text feedback
        generation_request_data: For AI messages - the full prompt/request sent to LLM (debug)
        metadata_: App-specific data (attachments, reactions, etc.)
        created_at: When message was sent
        deleted_at: Soft delete timestamp
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id = Column(
        Integer,
        ForeignKey("participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    sender_name = Column(String(100), nullable=True)  # SNAPSHOT at send time
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="text", nullable=False)
    message_type = Column(String(20), default="user", nullable=False)  # user, generated, fixed, edited
    transcription = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=True)
    thumbs_up_count = Column(Integer, default=0, nullable=False)
    thumbs_down_count = Column(Integer, default=0, nullable=False)
    text_feedback = Column(Text, nullable=True)
    generation_request_data = Column(JSON, nullable=True)  # Full LLM prompt for debug (AI messages only)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    participant = relationship("Participant", back_populates="messages")
    parent = relationship("Message", remote_side=[id], backref="replies")
    attachments = relationship(
        "Attachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    tool_calls = relationship(
        "ToolCall",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_messages_chat_id", "chat_id"),
        Index("idx_messages_participant_id", "participant_id"),
        Index("idx_messages_parent_id", "parent_id"),
        Index("idx_messages_created_at", "created_at"),
        Index("idx_messages_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} chat_id={self.chat_id} role={self.role}>"

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
            "generation_request_data": self.generation_request_data,
            "metadata": self.metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def to_llm_format(self) -> dict[str, str]:
        """Convert to format expected by LLM APIs."""
        return {
            "role": self.role,
            "content": self.content,
        }


class Attachment(Base):
    """
    File attachment for a message.

    Stores metadata about attached files (images, documents, audio, etc.).
    Actual file storage is delegated to the host application.

    Attributes:
        id: Primary key
        message_id: Parent message (FK with cascade delete)
        filename: Original filename
        file_type: MIME type (e.g., 'image/png', 'application/pdf')
        file_size: Size in bytes
        storage_path: Path/URL to actual file (host app manages storage)
        transcription: Extracted text (OCR, audio transcription, etc.)
        metadata_: Additional file metadata (dimensions, duration, etc.)
        created_at: When attachment was added
    """

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=True)  # MIME type
    file_size = Column(Integer, nullable=True)  # bytes
    storage_path = Column(Text, nullable=True)  # URL or path
    transcription = Column(Text, nullable=True)  # OCR/audio transcript
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="attachments")

    __table_args__ = (
        Index("idx_attachments_message_id", "message_id"),
        Index("idx_attachments_file_type", "file_type"),
    )

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} filename={self.filename!r}>"

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
            "metadata": self.metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ToolCall(Base):
    """
    Tool/function invocation record.

    Tracks every tool call for observability, debugging, and analytics.
    Links to both the triggering message and optionally an agent run.

    Attributes:
        id: Primary key
        message_id: Which message triggered this tool call
        run_id: Part of which agent run (if any)
        tool_name: Name of the tool called
        tool_version: Version of the tool if tracked
        input_params: Parameters passed to the tool
        output_data: Result returned by the tool
        status: 'pending', 'running', 'success', 'error', 'timeout', 'cancelled'
        error_message: Error details if failed
        execution_time_ms: How long the tool took
        retry_count: Number of retries attempted
        created_at: When tool was called
        completed_at: When tool finished
    """

    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(
        Integer,
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(20), nullable=True)
    input_params = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="tool_calls")
    agent_run = relationship("AgentRun", back_populates="tool_calls")

    __table_args__ = (
        Index("idx_tool_calls_message_id", "message_id"),
        Index("idx_tool_calls_run_id", "run_id"),
        Index("idx_tool_calls_tool_name", "tool_name"),
        Index("idx_tool_calls_status", "status"),
        Index("idx_tool_calls_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ToolCall id={self.id} tool={self.tool_name} status={self.status}>"

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


class AgentRun(Base):
    """
    Agent execution session.

    Tracks complete agent runs for debugging, analytics, and cost tracking.
    One agent run can have many tool calls.

    Attributes:
        id: Primary key
        chat_id: Which chat this run belongs to
        trigger_message_id: Message that triggered this run
        agent_name: Name/type of agent
        agent_version: Version of the agent if tracked
        status: 'running', 'completed', 'failed', 'cancelled'
        input_data: Initial input to the agent
        final_result: Final output from the agent
        error_message: Error details if failed
        total_steps: Number of reasoning steps/iterations
        total_tool_calls: Number of tool calls made
        token_usage: Token consumption breakdown (JSON)
        cost: Total cost in USD
        started_at: When run started
        completed_at: When run finished
        metadata_: App-specific data
    """

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_name = Column(String(100), nullable=False)
    agent_version = Column(String(20), nullable=True)
    status = Column(String(20), default="running", nullable=False)
    input_data = Column(JSON, nullable=True)
    final_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    total_steps = Column(Integer, default=0, nullable=False)
    total_tool_calls = Column(Integer, default=0, nullable=False)
    token_usage = Column(JSON, default=dict, nullable=False)
    cost = Column(Numeric(10, 6), nullable=True)
    started_at = Column(DateTime, default=_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="agent_runs")
    tool_calls = relationship("ToolCall", back_populates="agent_run")

    __table_args__ = (
        Index("idx_agent_runs_chat_id", "chat_id"),
        Index("idx_agent_runs_agent_name", "agent_name"),
        Index("idx_agent_runs_status", "status"),
        Index("idx_agent_runs_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} agent={self.agent_name} status={self.status}>"

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
            "metadata": self.metadata_,
        }
