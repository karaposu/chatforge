"""SQLAlchemy async implementation of ChatRepository."""

from typing import Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatforge.ports.storage import ChatRepository
from chatforge.adapters.storage.models.models import Chat, Participant, _utc_now

logger = logging.getLogger(__name__)


class SQLAlchemyChatRepo(ChatRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(
        self, *, user_id: int | str, display_name: str = "User",
        settings: dict | None = None, title: str | None = None,
        system_prompt: str | None = None, metadata: dict | None = None,
    ) -> Chat:
        chat_row = Chat(
            title=title, system_prompt=system_prompt,
            settings=settings or {}, metadata_=metadata or {},
            created_at=_utc_now(),
        )
        self.session.add(chat_row)
        await self.session.flush()

        owner = Participant(
            chat_id=chat_row.id, participant_type="user",
            external_id=str(user_id), display_name=display_name,
            role_in_chat="owner", joined_at=_utc_now(),
        )
        self.session.add(owner)
        await self.session.commit()
        await self.session.refresh(chat_row)

        logger.debug("Chat created (id=%s user=%s)", chat_row.id, user_id)
        return chat_row

    async def get_chat_by_id(self, chat_id: int) -> Optional[Chat]:
        stmt = select(Chat).where(Chat.id == chat_id, Chat.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chats_by_user(self, user_id: int | str) -> list[Chat]:
        stmt = (
            select(Chat)
            .join(Participant, Chat.id == Participant.chat_id)
            .where(Participant.external_id == str(user_id))
            .where(Participant.participant_type == "user")
            .where(Chat.deleted_at.is_(None))
            .order_by(Chat.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_chat(self, chat_id: int, user_id: int | str) -> bool:
        stmt = (
            select(Chat)
            .join(Participant, Chat.id == Participant.chat_id)
            .where(Chat.id == chat_id)
            .where(Participant.external_id == str(user_id))
            .where(Participant.role_in_chat == "owner")
            .where(Chat.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()
        if not chat:
            return False
        chat.deleted_at = _utc_now()
        await self.session.commit()
        return True

    async def user_owns_chat(self, chat_id: int, user_id: int | str) -> bool:
        stmt = (
            select(Participant)
            .where(Participant.chat_id == chat_id)
            .where(Participant.external_id == str(user_id))
            .where(Participant.role_in_chat == "owner")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_or_create_assistant_participant(
        self, chat_id: int, assistant_name: str = "Assistant",
    ) -> Participant:
        stmt = (
            select(Participant)
            .where(Participant.chat_id == chat_id)
            .where(Participant.participant_type == "assistant")
        )
        result = await self.session.execute(stmt)
        participant = result.scalar_one_or_none()
        if participant:
            return participant

        participant = Participant(
            chat_id=chat_id, participant_type="assistant",
            external_id=None, display_name=assistant_name,
            role_in_chat="member", joined_at=_utc_now(),
        )
        self.session.add(participant)
        await self.session.flush()
        return participant

    async def get_user_participant(
        self, chat_id: int, user_id: int | str,
    ) -> Optional[Participant]:
        stmt = (
            select(Participant)
            .where(Participant.chat_id == chat_id)
            .where(Participant.external_id == str(user_id))
            .where(Participant.participant_type == "user")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
