"""
Async Message Repository.

CRUD operations for messages using SQLAlchemy AsyncSession.

Usage:
    from chatforge.adapters.storage.repositories.async_ import MessageRepository

    repo = MessageRepository(async_session)
    messages = await repo.fetch_messages(chat_id=1, limit=50)
"""

from datetime import datetime
from typing import Optional
import logging

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from chatforge.adapters.storage.models.models import (
    Message,
    Participant,
    _utc_now,
)

logger = logging.getLogger(__name__)


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_messages(
        self,
        *,
        chat_id: int,
        limit: int = 50,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> list[Message]:
        """
        Return messages for a chat (oldest -> newest).

        Parameters
        ----------
        chat_id : int
            Target chat identifier.
        limit : int
            Max rows to return.
        offset : int
            Skip this many rows.
        since : datetime | None
            If supplied, return only rows with created_at > since.
        """
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.deleted_at.is_(None))
        )

        if since is not None:
            stmt = stmt.where(Message.created_at > since)

        stmt = stmt.order_by(Message.created_at.asc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())

        logger.debug(
            "Fetched %s messages (chat_id=%s, limit=%s, offset=%s)",
            len(messages), chat_id, limit, offset
        )
        return messages

    async def insert_message(
        self,
        *,
        chat_id: int,
        participant_id: int,
        sender_name: str,
        role: str,
        content: str,
        content_format: str = "text",
        message_type: str = "user",
        generation_request_data: dict | None = None,
    ) -> Message:
        """
        Persist a single message row and return the ORM object.

        Parameters
        ----------
        chat_id : int
            Target chat identifier.
        participant_id : int
            FK to participants table.
        sender_name : str
            Display name snapshot at send time.
        role : str
            'user', 'assistant', 'system', or 'tool'.
        content : str
            The message text.
        content_format : str
            'text', 'markdown', 'html', 'json'.
        message_type : str
            'user', 'generated', 'fixed', 'edited'.
        generation_request_data : dict | None
            Full LLM prompt for debug (AI messages only).
        """
        msg_row = Message(
            chat_id=chat_id,
            participant_id=participant_id,
            sender_name=sender_name,
            role=role,
            content=content,
            content_format=content_format,
            message_type=message_type,
            generation_request_data=generation_request_data,
            created_at=_utc_now(),
        )
        self.session.add(msg_row)
        await self.session.commit()
        await self.session.refresh(msg_row)

        logger.debug("Inserted message id=%s (chat_id=%s)", msg_row.id, chat_id)
        return msg_row

    async def insert_user_message(
        self,
        *,
        chat_id: int,
        user_id: int | str,
        user_name: str,
        content: str,
        content_format: str = "text",
    ) -> Message:
        """
        Insert a user message (convenience wrapper).

        Finds the user's participant record and inserts the message.
        """
        stmt = (
            select(Participant)
            .where(Participant.chat_id == chat_id)
            .where(Participant.external_id == str(user_id))
            .where(Participant.participant_type == "user")
        )
        result = await self.session.execute(stmt)
        participant = result.scalar_one_or_none()

        if not participant:
            raise ValueError(f"User {user_id} is not a participant in chat {chat_id}")

        return await self.insert_message(
            chat_id=chat_id,
            participant_id=participant.id,
            sender_name=user_name,
            role="user",
            content=content,
            content_format=content_format,
            message_type="user",
        )

    async def insert_assistant_message(
        self,
        *,
        chat_id: int,
        assistant_participant_id: int,
        assistant_name: str,
        content: str,
        content_format: str = "text",
        generation_request_data: dict | None = None,
    ) -> Message:
        """Insert an assistant message (convenience wrapper)."""
        return await self.insert_message(
            chat_id=chat_id,
            participant_id=assistant_participant_id,
            sender_name=assistant_name,
            role="assistant",
            content=content,
            content_format=content_format,
            message_type="generated",
            generation_request_data=generation_request_data,
        )

    async def fetch_last_n(self, *, chat_id: int, n: int) -> list[Message]:
        """Return the latest n messages for a chat (oldest -> newest)."""
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(n)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        rows.reverse()
        return rows

    async def fetch_messages_after(
        self,
        *,
        chat_id: int,
        after_message_id: int,
        limit: int = 500,
    ) -> list[Message]:
        """
        Fetch messages with ID greater than the specified message ID.

        Used for incremental extraction to get only new messages.
        """
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.id > after_message_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())

        logger.debug(
            "Fetched %s messages after id=%s (chat_id=%s)",
            len(messages), after_message_id, chat_id
        )
        return messages

    async def delete_recent_messages(self, *, chat_id: int, count: int) -> int:
        """
        Soft-delete the most recent N messages from a chat.

        Returns number of messages actually deleted.
        """
        if count <= 0:
            raise ValueError("Count must be positive")

        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(count)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())

        if not messages:
            return 0

        now = _utc_now()
        for msg in messages:
            msg.deleted_at = now

        await self.session.commit()

        logger.debug("Soft-deleted %s recent messages (chat_id=%s)", len(messages), chat_id)
        return len(messages)

    async def count_messages(self, *, chat_id: int) -> int:
        """Count total non-deleted messages in a chat."""
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_messages_for_llm(self, *, chat_id: int, limit: int = 50) -> list[dict]:
        """Get messages in LLM format (role + content dicts)."""
        messages = await self.fetch_last_n(chat_id=chat_id, n=limit)
        return [msg.to_llm_format() for msg in messages]
