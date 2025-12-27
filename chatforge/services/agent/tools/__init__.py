"""
Chatforge Tools - Base classes for building agent tools.

This module provides base classes for creating tools that work
seamlessly in both sync and async contexts.

Usage:
    from chatforge.services.agent.tools import AsyncAwareTool, create_tool
    from pydantic import BaseModel, Field

    # Method 1: Class-based tool
    class MyToolInput(BaseModel):
        query: str = Field(description="Search query")

    class MyTool(AsyncAwareTool):
        name: str = "my_tool"
        description: str = "Does something useful"
        args_schema: type[BaseModel] = MyToolInput

        async def _execute_async(self, query: str, **kwargs) -> str:
            return f"Result for: {query}"

    # Method 2: Function-based tool
    async def search_docs(query: str) -> str:
        return f"Found results for: {query}"

    tool = create_tool(
        name="search_docs",
        description="Search documentation",
        func=search_docs,
    )

Applications create domain-specific tools by extending AsyncAwareTool
or using create_tool() for simple cases.
"""

from chatforge.services.agent.tools.base import AsyncAwareTool, create_tool

__all__ = [
    "AsyncAwareTool",
    "create_tool",
]
