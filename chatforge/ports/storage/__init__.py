"""
Storage Port — per-entity repository interfaces + Storage facade.

Usage:
    from chatforge.ports.storage import Storage, ChatRepository, MessageRepository

    # App code uses the facade:
    storage = Storage(chats=..., messages=..., ...)
    chat = await storage.chats.create_chat(user_id=1)
    msgs = await storage.messages.fetch_messages(chat_id=chat.id)
"""

from dataclasses import dataclass, field
from typing import Optional

from chatforge.ports.storage.chat_repository import ChatRepository
from chatforge.ports.storage.message_repository import MessageRepository
from chatforge.ports.storage.tool_call_repository import ToolCallRepository
from chatforge.ports.storage.agent_run_repository import AgentRunRepository
from chatforge.ports.storage.llm_call_repository import LLMCallRepository
from chatforge.ports.storage.profiling_repository import ProfilingRepository


@dataclass
class Storage:
    """
    Facade grouping all storage repositories.

    App code accesses storage through this:
        storage.chats.create_chat(...)
        storage.messages.fetch_messages(...)
        storage.profiling.get_cpde7_data(...)

    Backends are injected at construction:
        storage = Storage(
            chats=SQLAlchemyChatRepo(session_factory),
            messages=SQLAlchemyMessageRepo(session_factory),
            ...
        )
    """
    chats: ChatRepository
    messages: MessageRepository
    tool_calls: Optional[ToolCallRepository] = None
    agent_runs: Optional[AgentRunRepository] = None
    llm_calls: Optional[LLMCallRepository] = None
    profiling: Optional[ProfilingRepository] = None

    async def setup(self) -> None:
        """Initialize all backends. Override in factory if needed."""
        pass

    async def close(self) -> None:
        """Clean up all backends."""
        pass

    async def health_check(self) -> bool:
        """Check all backends are healthy."""
        return True


__all__ = [
    "Storage",
    "ChatRepository",
    "MessageRepository",
    "ToolCallRepository",
    "AgentRunRepository",
    "LLMCallRepository",
    "ProfilingRepository",
]
