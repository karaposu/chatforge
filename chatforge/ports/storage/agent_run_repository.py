"""Abstract AgentRun Repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AgentRunRepository(ABC):
    """Abstract interface for agent run tracking."""

    @abstractmethod
    async def start_agent_run(
        self, *, chat_id: int, agent_name: str,
        trigger_message_id: int | None = None,
        agent_version: str | None = None, model_name: str | None = None,
        input_data: dict | None = None, metadata: dict | None = None,
    ) -> Any: ...

    @abstractmethod
    async def complete_agent_run(
        self, *, run_id: int, status: str,
        final_result: dict | None = None, error_message: str | None = None,
        total_steps: int | None = None, total_tool_calls: int | None = None,
        token_usage: dict | None = None, cost: float | None = None,
    ) -> Optional[Any]: ...

    @abstractmethod
    async def get_agent_run(self, *, run_id: int) -> Optional[Any]: ...

    @abstractmethod
    async def list_agent_runs(
        self, *, chat_id: int | None = None, agent_name: str | None = None,
        status: str | None = None, limit: int = 100,
    ) -> list: ...
