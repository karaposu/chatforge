"""Abstract Profiling Data Repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ProfilingRepository(ABC):
    """Abstract interface for CPDE-7 profiling data extraction."""

    # Extraction Run Management

    @abstractmethod
    async def create_run(
        self, *, user_id: str, chat_id: int | None = None,
        config: dict, model_used: str | None = None,
    ) -> Any: ...

    @abstractmethod
    async def start_run(
        self, *, run_id: int, message_count: int, message_id_range: dict,
    ) -> Any: ...

    @abstractmethod
    async def complete_run(self, *, run_id: int, duration_ms: int) -> Any: ...

    @abstractmethod
    async def fail_run(self, *, run_id: int, error: str) -> Any: ...

    @abstractmethod
    async def get_run(self, *, run_id: int) -> Optional[Any]: ...

    @abstractmethod
    async def get_runs_for_user(self, *, user_id: str, limit: int = 20) -> list: ...

    @abstractmethod
    async def get_active_run(self, *, chat_id: int) -> Optional[Any]: ...

    @abstractmethod
    async def get_latest_completed_run(self, *, chat_id: int) -> Optional[Any]: ...

    # Extracted Data Storage

    @abstractmethod
    async def save_extracted_item(
        self, *, run_id: int, user_id: str, chat_id: int,
        source_message_ids: list[int], source_quotes: list[str], data: dict,
    ) -> Any: ...

    @abstractmethod
    async def save_extracted_items_batch(
        self, *, run_id: int, user_id: str, chat_id: int, items: list[dict],
    ) -> int: ...

    # Extracted Data Retrieval

    @abstractmethod
    async def get_cpde7_data(self, *, user_id: str, limit: int = 100) -> list: ...

    @abstractmethod
    async def get_cpde7_data_by_chat(
        self, *, user_id: str, chat_id: int, limit: int = 100,
    ) -> list: ...

    @abstractmethod
    async def get_cpde7_data_by_dimension(
        self, *, user_id: str, dimension: str, limit: int = 50,
    ) -> list: ...

    @abstractmethod
    async def get_cpde7_data_grouped(
        self, *, user_id: str, limit_per_dimension: int = 20,
    ) -> dict: ...

    @abstractmethod
    async def get_profile_data_for_chat(
        self, *, user_id: str, chat_id: int, limit: int = 100,
    ) -> list[dict]: ...

    @abstractmethod
    async def delete_cpde7_data_for_chat(self, *, user_id: str, chat_id: int) -> int: ...
