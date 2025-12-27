"""
SQLAlchemy Storage Adapter - Generic database adapter using SQLAlchemy ORM.

Works with any SQLAlchemy-supported database: PostgreSQL, MySQL, SQLite, etc.
Uses the models defined in chatforge.db.models.

Example:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from chatforge.adapters.storage import SQLAlchemyStorageAdapter

    # PostgreSQL
    engine = create_engine("postgresql://user:pass@localhost/chatforge")

    # Or MySQL
    engine = create_engine("mysql+pymysql://user:pass@localhost/chatforge")

    # Or SQLite
    engine = create_engine("sqlite:///chatforge.db")

    Session = sessionmaker(bind=engine)
    adapter = SQLAlchemyStorageAdapter(engine, Session)
    await adapter.setup()  # Creates tables
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import and_, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from chatforge.adapters.storage.models.models import Base, Chat, Participant, Message, Attachment, ToolCall, AgentRun
from chatforge.ports.storage_types import (
    AgentRunRecord,
    AttachmentRecord,
    ChatRecord,
    MessageRecord,
    ParticipantRecord,
    ToolCallRecord,
)
from chatforge.ports.storage import StoragePort

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class SQLAlchemyStorageAdapter(StoragePort):
    """
    Generic SQLAlchemy adapter for any supported database.

    This adapter uses the ORM models from chatforge.adapters.storage.models.models and works
    with any SQLAlchemy engine (PostgreSQL, MySQL, SQLite, etc.).

    Args:
        engine: SQLAlchemy Engine instance
        session_factory: Callable that returns a new Session (e.g., sessionmaker)
    """

    def __init__(
        self,
        engine: Engine,
        session_factory: Callable[[], Session],
    ):
        """Initialize SQLAlchemy storage adapter."""
        self._engine = engine
        self._session_factory = session_factory
        self._initialized = False

    async def setup(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self._engine)
        self._initialized = True
        logger.info("SQLAlchemyStorageAdapter initialized")

    async def close(self) -> None:
        """Dispose of the engine connection pool."""
        self._engine.dispose()
        logger.info("SQLAlchemyStorageAdapter closed")

    async def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self._session_factory() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    # =========================================================================
    # Chat Operations
    # =========================================================================

    async def create_chat(
        self,
        title: str | None = None,
        system_prompt: str | None = None,
        settings: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatRecord:
        """Create a new chat. Add participants separately via add_participant()."""
        with self._session_factory() as session:
            chat = Chat(
                title=title,
                system_prompt=system_prompt,
                settings=settings or {},
                metadata_=metadata or {},
            )
            session.add(chat)
            session.commit()
            session.refresh(chat)

            return self._chat_to_record(chat)

    async def get_chat(self, chat_id: int) -> ChatRecord | None:
        """Get a chat by ID."""
        with self._session_factory() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.deleted_at.is_(None),
            ).first()

            if not chat:
                return None

            return self._chat_to_record(chat)

    async def update_chat(
        self,
        chat_id: int,
        title: str | None = None,
        system_prompt: str | None = None,
        settings: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatRecord | None:
        """Update a chat."""
        with self._session_factory() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.deleted_at.is_(None),
            ).first()

            if not chat:
                return None

            if title is not None:
                chat.title = title
            if system_prompt is not None:
                chat.system_prompt = system_prompt
            if settings is not None:
                chat.settings = settings
            if metadata is not None:
                chat.metadata_ = metadata

            session.commit()
            session.refresh(chat)

            return self._chat_to_record(chat)

    async def delete_chat(self, chat_id: int, soft: bool = True) -> bool:
        """Delete a chat (soft delete by default)."""
        with self._session_factory() as session:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()

            if not chat:
                return False

            if soft:
                chat.deleted_at = _utc_now()
            else:
                session.delete(chat)

            session.commit()
            return True

    async def list_chats(
        self,
        external_user_id: str | None = None,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ChatRecord]:
        """List chats, optionally filtered by participant's external_id."""
        with self._session_factory() as session:
            query = session.query(Chat)

            if external_user_id:
                # Filter by participant's external_id
                query = query.join(Participant).filter(
                    Participant.external_id == external_user_id,
                    Participant.left_at.is_(None),
                )

            if not include_deleted:
                query = query.filter(Chat.deleted_at.is_(None))

            chats = query.order_by(Chat.updated_at.desc()).limit(limit).all()

            return [self._chat_to_record(c) for c in chats]

    # =========================================================================
    # Participant Operations
    # =========================================================================

    async def add_participant(
        self,
        chat_id: int,
        participant_type: str,
        display_name: str,
        external_id: str | None = None,
        role_in_chat: str = "member",
        metadata: dict[str, Any] | None = None,
    ) -> ParticipantRecord:
        """Add a participant to a chat."""
        with self._session_factory() as session:
            participant = Participant(
                chat_id=chat_id,
                participant_type=participant_type,
                display_name=display_name,
                external_id=external_id,
                role_in_chat=role_in_chat,
                metadata_=metadata or {},
            )
            session.add(participant)
            session.commit()
            session.refresh(participant)

            return self._participant_to_record(participant)

    async def get_participant(self, participant_id: int) -> ParticipantRecord | None:
        """Get a participant by ID."""
        with self._session_factory() as session:
            participant = session.query(Participant).filter(
                Participant.id == participant_id
            ).first()

            if not participant:
                return None

            return self._participant_to_record(participant)

    async def get_participants(
        self,
        chat_id: int,
        include_left: bool = False,
    ) -> list[ParticipantRecord]:
        """Get all participants in a chat."""
        with self._session_factory() as session:
            query = session.query(Participant).filter(
                Participant.chat_id == chat_id
            )

            if not include_left:
                query = query.filter(Participant.left_at.is_(None))

            participants = query.order_by(Participant.joined_at).all()

            return [self._participant_to_record(p) for p in participants]

    async def remove_participant(self, participant_id: int) -> bool:
        """Remove a participant from a chat (soft delete via left_at)."""
        with self._session_factory() as session:
            participant = session.query(Participant).filter(
                Participant.id == participant_id
            ).first()

            if not participant:
                return False

            participant.left_at = _utc_now()
            session.commit()
            return True

    # =========================================================================
    # Message Operations
    # =========================================================================

    async def save_message(
        self,
        chat_id: int,
        content: str,
        role: str,
        participant_id: int | None = None,
        sender_name: str | None = None,
        parent_id: int | None = None,
        content_format: str = "text",
        message_type: str = "user",
        transcription: str | None = None,
        token_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MessageRecord:
        """Save a message to a chat.

        Args:
            chat_id: The chat to add the message to
            content: Message content
            role: LLM role (user, assistant, system, tool)
            participant_id: Who sent this (FK to participants)
            sender_name: Snapshot of participant's display name at send time
            parent_id: For threaded replies
            content_format: text, markdown, html, json
            message_type: user, generated, fixed, edited
            transcription: Voice transcription if applicable
            token_count: Token count for this message
            metadata: Additional data
        """
        with self._session_factory() as session:
            # Ensure chat exists and update its timestamp
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                raise ValueError(f"Chat {chat_id} not found")

            chat.updated_at = _utc_now()

            # If participant_id provided but no sender_name, look it up
            if participant_id and not sender_name:
                participant = session.query(Participant).filter(
                    Participant.id == participant_id
                ).first()
                if participant:
                    sender_name = participant.display_name

            message = Message(
                chat_id=chat_id,
                content=content,
                role=role,
                participant_id=participant_id,
                sender_name=sender_name,
                parent_id=parent_id,
                content_format=content_format,
                message_type=message_type,
                transcription=transcription,
                token_count=token_count,
                metadata_=metadata or {},
            )
            session.add(message)
            session.commit()
            session.refresh(message)

            return self._message_to_record(message)

    async def get_messages(
        self,
        chat_id: int,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[MessageRecord]:
        """Get messages for a chat."""
        with self._session_factory() as session:
            query = session.query(Message).filter(Message.chat_id == chat_id)

            if not include_deleted:
                query = query.filter(Message.deleted_at.is_(None))

            messages = query.order_by(Message.created_at.asc()).limit(limit).all()

            return [self._message_to_record(m) for m in messages]

    async def delete_message(self, message_id: int, soft: bool = True) -> bool:
        """Delete a message."""
        with self._session_factory() as session:
            message = session.query(Message).filter(Message.id == message_id).first()

            if not message:
                return False

            if soft:
                message.deleted_at = _utc_now()
            else:
                session.delete(message)

            session.commit()
            return True

    async def add_feedback(
        self,
        message_id: int,
        thumbs_up: bool | None = None,
        thumbs_down: bool | None = None,
        text_feedback: str | None = None,
    ) -> MessageRecord | None:
        """Add feedback to a message."""
        with self._session_factory() as session:
            message = session.query(Message).filter(
                Message.id == message_id
            ).first()

            if not message:
                return None

            if thumbs_up:
                message.thumbs_up_count += 1
            if thumbs_down:
                message.thumbs_down_count += 1
            if text_feedback is not None:
                message.text_feedback = text_feedback

            session.commit()
            session.refresh(message)

            return self._message_to_record(message)

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    async def add_attachment(
        self,
        message_id: int,
        filename: str,
        file_type: str | None = None,
        file_size: int | None = None,
        storage_path: str | None = None,
        transcription: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AttachmentRecord:
        """Add an attachment to a message."""
        with self._session_factory() as session:
            attachment = Attachment(
                message_id=message_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                storage_path=storage_path,
                transcription=transcription,
                metadata_=metadata or {},
            )
            session.add(attachment)
            session.commit()
            session.refresh(attachment)

            return self._attachment_to_record(attachment)

    async def get_attachments(self, message_id: int) -> list[AttachmentRecord]:
        """Get all attachments for a message."""
        with self._session_factory() as session:
            attachments = session.query(Attachment).filter(
                Attachment.message_id == message_id
            ).all()

            return [self._attachment_to_record(a) for a in attachments]

    async def delete_attachment(self, attachment_id: int) -> bool:
        """Delete an attachment."""
        with self._session_factory() as session:
            attachment = session.query(Attachment).filter(
                Attachment.id == attachment_id
            ).first()

            if not attachment:
                return False

            session.delete(attachment)
            session.commit()
            return True

    # =========================================================================
    # Tool Call Operations
    # =========================================================================

    async def log_tool_call(
        self,
        message_id: int,
        tool_name: str,
        input_params: dict[str, Any],
        run_id: int | None = None,
        tool_version: str | None = None,
    ) -> ToolCallRecord:
        """Log a tool call."""
        with self._session_factory() as session:
            tool_call = ToolCall(
                message_id=message_id,
                run_id=run_id,
                tool_name=tool_name,
                tool_version=tool_version,
                input_params=input_params,
                status="pending",
            )
            session.add(tool_call)
            session.commit()
            session.refresh(tool_call)

            return self._tool_call_to_record(tool_call)

    async def update_tool_call(
        self,
        tool_call_id: int,
        status: str,
        output_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        execution_time_ms: int | None = None,
    ) -> ToolCallRecord | None:
        """Update a tool call with results."""
        with self._session_factory() as session:
            tool_call = session.query(ToolCall).filter(
                ToolCall.id == tool_call_id
            ).first()

            if not tool_call:
                return None

            tool_call.status = status
            if output_data is not None:
                tool_call.output_data = output_data
            if error_message is not None:
                tool_call.error_message = error_message
            if execution_time_ms is not None:
                tool_call.execution_time_ms = execution_time_ms
            if status in ("success", "error", "timeout", "cancelled"):
                tool_call.completed_at = _utc_now()

            session.commit()
            session.refresh(tool_call)

            return self._tool_call_to_record(tool_call)

    async def get_tool_calls(
        self,
        message_id: int | None = None,
        run_id: int | None = None,
    ) -> list[ToolCallRecord]:
        """Get tool calls filtered by message or run."""
        with self._session_factory() as session:
            query = session.query(ToolCall)

            if message_id:
                query = query.filter(ToolCall.message_id == message_id)
            if run_id:
                query = query.filter(ToolCall.run_id == run_id)

            tool_calls = query.order_by(ToolCall.created_at.asc()).all()

            return [self._tool_call_to_record(tc) for tc in tool_calls]

    # =========================================================================
    # Agent Run Operations
    # =========================================================================

    async def start_agent_run(
        self,
        chat_id: int,
        agent_name: str,
        trigger_message_id: int | None = None,
        agent_version: str | None = None,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentRunRecord:
        """Start a new agent run."""
        with self._session_factory() as session:
            run = AgentRun(
                chat_id=chat_id,
                agent_name=agent_name,
                trigger_message_id=trigger_message_id,
                agent_version=agent_version,
                input_data=input_data,
                status="running",
                metadata_=metadata or {},
            )
            session.add(run)
            session.commit()
            session.refresh(run)

            return self._agent_run_to_record(run)

    async def complete_agent_run(
        self,
        run_id: int,
        status: str,
        final_result: dict[str, Any] | None = None,
        error_message: str | None = None,
        total_steps: int | None = None,
        total_tool_calls: int | None = None,
        token_usage: dict[str, Any] | None = None,
        cost: float | None = None,
    ) -> AgentRunRecord | None:
        """Complete an agent run with results."""
        with self._session_factory() as session:
            run = session.query(AgentRun).filter(AgentRun.id == run_id).first()

            if not run:
                return None

            run.status = status
            run.completed_at = _utc_now()

            if final_result is not None:
                run.final_result = final_result
            if error_message is not None:
                run.error_message = error_message
            if total_steps is not None:
                run.total_steps = total_steps
            if total_tool_calls is not None:
                run.total_tool_calls = total_tool_calls
            if token_usage is not None:
                run.token_usage = token_usage
            if cost is not None:
                run.cost = cost

            session.commit()
            session.refresh(run)

            return self._agent_run_to_record(run)

    async def get_agent_run(self, run_id: int) -> AgentRunRecord | None:
        """Get an agent run by ID."""
        with self._session_factory() as session:
            run = session.query(AgentRun).filter(AgentRun.id == run_id).first()

            if not run:
                return None

            return self._agent_run_to_record(run)

    async def list_agent_runs(
        self,
        chat_id: int | None = None,
        agent_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[AgentRunRecord]:
        """List agent runs with optional filters."""
        with self._session_factory() as session:
            query = session.query(AgentRun)

            if chat_id:
                query = query.filter(AgentRun.chat_id == chat_id)
            if agent_name:
                query = query.filter(AgentRun.agent_name == agent_name)
            if status:
                query = query.filter(AgentRun.status == status)

            runs = query.order_by(AgentRun.started_at.desc()).limit(limit).all()

            return [self._agent_run_to_record(r) for r in runs]

    # =========================================================================
    # Cleanup Operations
    # =========================================================================

    async def cleanup_expired(self, ttl_minutes: int = 30) -> int:
        """Remove chats older than TTL (hard delete)."""
        cutoff = _utc_now() - timedelta(minutes=ttl_minutes)

        with self._session_factory() as session:
            # Get expired chat IDs
            expired = session.query(Chat.id).filter(
                Chat.updated_at < cutoff
            ).all()

            if not expired:
                return 0

            expired_ids = [c.id for c in expired]

            # Delete chats (cascades to messages, tool_calls, agent_runs)
            session.query(Chat).filter(Chat.id.in_(expired_ids)).delete(
                synchronize_session=False
            )
            session.commit()

            logger.info(f"Cleaned up {len(expired_ids)} expired chats")
            return len(expired_ids)

    async def cleanup_soft_deleted(self, older_than_days: int = 30) -> int:
        """Permanently delete soft-deleted records older than specified days."""
        cutoff = _utc_now() - timedelta(days=older_than_days)

        with self._session_factory() as session:
            # Delete old soft-deleted chats
            deleted_chats = session.query(Chat).filter(
                and_(
                    Chat.deleted_at.isnot(None),
                    Chat.deleted_at < cutoff,
                )
            ).delete(synchronize_session=False)

            # Delete old soft-deleted messages
            deleted_messages = session.query(Message).filter(
                and_(
                    Message.deleted_at.isnot(None),
                    Message.deleted_at < cutoff,
                )
            ).delete(synchronize_session=False)

            session.commit()

            total = deleted_chats + deleted_messages
            if total > 0:
                logger.info(
                    f"Permanently deleted {deleted_chats} chats and "
                    f"{deleted_messages} messages"
                )
            return total

    # =========================================================================
    # Legacy Compatibility (for existing StoragePort interface)
    # =========================================================================

    async def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[MessageRecord]:
        """Legacy method: Get messages by conversation_id (string)."""
        # Try to parse as int, otherwise use string lookup
        try:
            chat_id = int(conversation_id)
        except ValueError:
            # For string IDs, look up in metadata or title
            with self._session_factory() as session:
                chat = session.query(Chat).filter(
                    Chat.title == conversation_id
                ).first()
                if not chat:
                    return []
                chat_id = chat.id

        return await self.get_messages(chat_id, limit=limit)

    async def get_conversation_metadata(
        self,
        conversation_id: str,
    ) -> ChatRecord | None:
        """Legacy method: Get chat by conversation_id (string)."""
        try:
            chat_id = int(conversation_id)
            return await self.get_chat(chat_id)
        except ValueError:
            return None

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Legacy method: Delete by conversation_id (string)."""
        try:
            chat_id = int(conversation_id)
            return await self.delete_chat(chat_id)
        except ValueError:
            return False

    async def list_conversations(
        self,
        external_user_id: str | None = None,
        limit: int = 100,
    ) -> list[ChatRecord]:
        """Legacy method: List chats (alias)."""
        return await self.list_chats(external_user_id=external_user_id, limit=limit)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _chat_to_record(self, chat: Chat) -> ChatRecord:
        """Convert Chat model to ChatRecord dataclass."""
        return ChatRecord(
            id=chat.id,
            title=chat.title,
            system_prompt=chat.system_prompt,
            settings=chat.settings or {},
            metadata=chat.metadata_ or {},
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            deleted_at=chat.deleted_at,
        )

    def _participant_to_record(self, participant: Participant) -> ParticipantRecord:
        """Convert Participant model to ParticipantRecord dataclass."""
        return ParticipantRecord(
            id=participant.id,
            chat_id=participant.chat_id,
            participant_type=participant.participant_type,
            external_id=participant.external_id,
            display_name=participant.display_name,
            role_in_chat=participant.role_in_chat,
            metadata=participant.metadata_ or {},
            joined_at=participant.joined_at,
            left_at=participant.left_at,
        )

    def _message_to_record(self, message: Message) -> MessageRecord:
        """Convert Message model to MessageRecord dataclass."""
        return MessageRecord(
            id=message.id,
            chat_id=message.chat_id,
            participant_id=message.participant_id,
            parent_id=message.parent_id,
            sender_name=message.sender_name,
            role=message.role,
            content=message.content,
            content_format=message.content_format,
            message_type=message.message_type,
            transcription=message.transcription,
            token_count=message.token_count,
            thumbs_up_count=message.thumbs_up_count,
            thumbs_down_count=message.thumbs_down_count,
            text_feedback=message.text_feedback,
            metadata=message.metadata_ or {},
            created_at=message.created_at,
            deleted_at=message.deleted_at,
        )

    def _attachment_to_record(self, attachment: Attachment) -> AttachmentRecord:
        """Convert Attachment model to AttachmentRecord dataclass."""
        return AttachmentRecord(
            id=attachment.id,
            message_id=attachment.message_id,
            filename=attachment.filename,
            file_type=attachment.file_type,
            file_size=attachment.file_size,
            storage_path=attachment.storage_path,
            transcription=attachment.transcription,
            metadata=attachment.metadata_ or {},
            created_at=attachment.created_at,
        )

    def _tool_call_to_record(self, tool_call: ToolCall) -> ToolCallRecord:
        """Convert ToolCall model to ToolCallRecord dataclass."""
        return ToolCallRecord(
            id=tool_call.id,
            message_id=tool_call.message_id,
            run_id=tool_call.run_id,
            tool_name=tool_call.tool_name,
            tool_version=tool_call.tool_version,
            input_params=tool_call.input_params or {},
            output_data=tool_call.output_data,
            status=tool_call.status,
            error_message=tool_call.error_message,
            execution_time_ms=tool_call.execution_time_ms,
            retry_count=tool_call.retry_count,
            created_at=tool_call.created_at,
            completed_at=tool_call.completed_at,
        )

    def _agent_run_to_record(self, run: AgentRun) -> AgentRunRecord:
        """Convert AgentRun model to AgentRunRecord dataclass."""
        return AgentRunRecord(
            id=run.id,
            chat_id=run.chat_id,
            trigger_message_id=run.trigger_message_id,
            agent_name=run.agent_name,
            agent_version=run.agent_version,
            status=run.status,
            input_data=run.input_data,
            final_result=run.final_result,
            error_message=run.error_message,
            total_steps=run.total_steps,
            total_tool_calls=run.total_tool_calls,
            token_usage=run.token_usage or {},
            cost=run.cost,
            started_at=run.started_at,
            completed_at=run.completed_at,
            metadata=run.metadata_ or {},
        )
