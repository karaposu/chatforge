"""Abstract Message Repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Any


class MessageRepository(ABC):
    """Abstract interface for message operations."""

    @abstractmethod
    async def fetch_messages(
        self, *, chat_id: int, limit: int = 50, offset: int = 0,
        since: Optional[datetime] = None,
    ) -> list: ...

    @abstractmethod
    async def insert_message(
        self, *, chat_id: int, participant_id: int, sender_name: str,
        role: str, content: str, content_format: str = "text",
        message_type: str = "user", generation_request_data: dict | None = None,
    ) -> Any: ...

    @abstractmethod
    async def insert_user_message(
        self, *, chat_id: int, user_id: int | str, user_name: str,
        content: str, content_format: str = "text",
    ) -> Any: ...

    @abstractmethod
    async def insert_assistant_message(
        self, *, chat_id: int, assistant_participant_id: int,
        assistant_name: str, content: str, content_format: str = "text",
        generation_request_data: dict | None = None,
    ) -> Any: ...

    @abstractmethod
    async def fetch_last_n(self, *, chat_id: int, n: int) -> list: ...

    @abstractmethod
    async def fetch_messages_after(
        self, *, chat_id: int, after_message_id: int, limit: int = 500,
    ) -> list: ...

    @abstractmethod
    async def delete_recent_messages(self, *, chat_id: int, count: int) -> int: ...

    @abstractmethod
    async def count_messages(self, *, chat_id: int) -> int: ...

    @abstractmethod
    async def get_messages_for_llm(self, *, chat_id: int, limit: int = 50) -> list[dict]: ...
