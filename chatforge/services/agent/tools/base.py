"""
AsyncAwareTool - Base class eliminating sync/async code duplication in tools.

This module provides a base class that centralizes the sync/async bridging pattern
used across all tools, following DRY principles.

Subclasses implement ONLY _execute_async() with the actual tool logic.
The base class provides _run() and _arun() automatically.

Usage:
    from chatforge.services.agent.tools import AsyncAwareTool
    from pydantic import BaseModel, Field

    class MyToolInput(BaseModel):
        query: str = Field(description="Search query")
        limit: int = Field(default=5, description="Max results")

    class MyTool(AsyncAwareTool):
        name: str = "my_tool"
        description: str = "Does something useful"
        args_schema: type[BaseModel] = MyToolInput

        async def _execute_async(
            self,
            query: str,
            limit: int = 5,
            **kwargs,  # Accept LangGraph config params
        ) -> str:
            # All tool logic goes here (one place only)
            result = await some_async_operation(query, limit)
            return f"Found: {result}"
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel


class AsyncAwareTool(BaseTool):
    """
    Base class for tools that need to work in both sync and async contexts.

    This eliminates the common pattern where tools duplicate logic across:
    - _run(): Sync entry point
    - _arun(): Async entry point
    - _actual_impl(): The real logic

    With AsyncAwareTool, subclasses implement only _execute_async() and
    the base class handles the sync/async bridging automatically.

    Benefits:
    - Single source of truth for tool logic
    - Consistent async bridge usage across all tools
    - Reduced code duplication (~20-40 lines per tool)
    - Type-safe parameter handling

    Note on parameters:
        Subclasses should define their specific parameters in _execute_async().
        The **kwargs catch-all allows LangGraph config parameters to pass through.

    Example:
        class SearchTool(AsyncAwareTool):
            name: str = "search"
            description: str = "Search the knowledge base"
            args_schema: type[BaseModel] = SearchInput

            async def _execute_async(
                self,
                query: str,
                limit: int = 5,
                **kwargs,
            ) -> str:
                results = await self._do_search(query, limit)
                return self._format_results(results)
    """

    @abstractmethod
    async def _execute_async(self, **kwargs: Any) -> str:
        """
        Implement the actual tool logic here.

        This is the single place where all tool logic should live.
        Subclasses override this method with their specific implementation.

        Args:
            **kwargs: Tool-specific arguments. Subclasses should define
                     explicit parameters with types and defaults.

        Returns:
            Tool result as a string.

        Example:
            async def _execute_async(
                self,
                query: str,
                max_results: int = 3,
                **kwargs,  # Accept LangGraph config params
            ) -> str:
                results = await self._search(query, max_results)
                return self._format_results(results)
        """
        ...

    def _run(self, **kwargs: Any) -> str:
        """
        Sync entry point - bridges to async execution.

        This method is called when the tool is invoked from a sync context.
        It uses the centralized async bridge to run the async implementation.

        Args:
            **kwargs: All arguments are forwarded to _execute_async().

        Returns:
            Tool result as a string.
        """
        from chatforge.utils import run_async

        return run_async(self._execute_async(**kwargs))

    async def _arun(self, **kwargs: Any) -> str:
        """
        Async entry point - direct execution.

        This method is called when the tool is invoked from an async context.
        It directly awaits the async implementation.

        Args:
            **kwargs: All arguments are forwarded to _execute_async().

        Returns:
            Tool result as a string.
        """
        return await self._execute_async(**kwargs)


def create_tool(
    name: str,
    description: str,
    func: callable,
    args_schema: Type[BaseModel] | None = None,
) -> AsyncAwareTool:
    """
    Factory function to create a tool from an async function.

    This provides a quick way to create simple tools without defining a class.

    Args:
        name: Tool name (used by agent for selection)
        description: Description for the LLM to understand when to use
        func: Async function to execute (must be async)
        args_schema: Optional Pydantic model for arguments

    Returns:
        AsyncAwareTool instance

    Example:
        async def search_docs(query: str, limit: int = 5) -> str:
            results = await do_search(query, limit)
            return f"Found {len(results)} results"

        tool = create_tool(
            name="search_docs",
            description="Search documentation for answers",
            func=search_docs,
        )
    """

    class DynamicTool(AsyncAwareTool):
        name: str = name  # type: ignore
        description: str = description  # type: ignore

        async def _execute_async(self, **kwargs: Any) -> str:
            return await func(**kwargs)

    # Set args_schema if provided
    if args_schema:
        DynamicTool.args_schema = args_schema  # type: ignore

    return DynamicTool()
