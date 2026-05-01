"""Abstract LLMCall Repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMCallRepository(ABC):
    """Abstract interface for LLM call tracking."""

    @abstractmethod
    async def log_llm_call(
        self, *, run_id: int | None = None, agent_name: str = "",
        model_name: str | None = None, call_index: int = 0,
        input_tokens: int = 0, output_tokens: int = 0,
        reasoning_tokens: int = 0, visible_tokens: int = 0,
        elapsed_s: float | None = None, response_text: str | None = None,
        has_tool_calls: bool = False, tool_names: list[str] | None = None,
        tool_call_ids: list[str] | None = None,
    ) -> Any: ...

    @abstractmethod
    async def get_llm_calls_for_run(self, *, run_id: int) -> list: ...

    @abstractmethod
    async def get_llm_calls_for_agent(
        self, *, run_id: int, agent_name: str,
    ) -> list: ...
