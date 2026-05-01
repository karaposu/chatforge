"""Abstract ToolCall Repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ToolCallRepository(ABC):
    """Abstract interface for tool call tracking."""

    @abstractmethod
    async def log_tool_call(
        self, *, message_id: int, tool_name: str, input_params: dict,
        run_id: int | None = None, tool_call_id: str | None = None,
        agent_name: str | None = None, tool_version: str | None = None,
    ) -> Any: ...

    @abstractmethod
    async def update_tool_call(
        self, *, tool_call_id: int, status: str,
        output_data: dict | None = None, error_message: str | None = None,
        execution_time_ms: int | None = None,
    ) -> Optional[Any]: ...

    @abstractmethod
    async def get_tool_calls(
        self, *, message_id: int | None = None, run_id: int | None = None,
    ) -> list: ...
