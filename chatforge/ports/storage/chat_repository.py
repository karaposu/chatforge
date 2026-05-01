"""Abstract Chat Repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ChatRepository(ABC):
    """Abstract interface for chat and participant operations."""

    @abstractmethod
    async def create_chat(
        self, *, user_id: int | str, display_name: str = "User",
        settings: dict | None = None, title: str | None = None,
        system_prompt: str | None = None, metadata: dict | None = None,
    ) -> Any: ...

    @abstractmethod
    async def get_chat_by_id(self, chat_id: int) -> Optional[Any]: ...

    @abstractmethod
    async def get_chats_by_user(self, user_id: int | str) -> list: ...

    @abstractmethod
    async def delete_chat(self, chat_id: int, user_id: int | str) -> bool: ...

    @abstractmethod
    async def user_owns_chat(self, chat_id: int, user_id: int | str) -> bool: ...

    @abstractmethod
    async def get_or_create_assistant_participant(
        self, chat_id: int, assistant_name: str = "Assistant",
    ) -> Any: ...

    @abstractmethod
    async def get_user_participant(
        self, chat_id: int, user_id: int | str,
    ) -> Optional[Any]: ...
