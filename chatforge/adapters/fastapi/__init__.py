"""
Chatforge FastAPI Integration.

Provides a router factory for creating REST API endpoints.

Usage:
    from fastapi import FastAPI
    from chatforge.adapters.fastapi import create_chat_router
    from chatforge.services.agent import ReActAgent
    from chatforge.adapters import InMemoryStorageAdapter

    app = FastAPI()
    agent = ReActAgent(tools=[], system_prompt="You are helpful.")
    storage = InMemoryStorageAdapter()

    router = create_chat_router(agent=agent, storage=storage)
    app.include_router(router, prefix="/api/v1")
"""

from chatforge.adapters.fastapi.routes import create_chat_router
from chatforge.adapters.fastapi.schemas import (
    CacheStats,
    ChatRequest,
    ChatResponse,
    CleanupCycleStats,
    CleanupHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    ErrorResponse,
    FileUploadRequest,
    ForceCleanupResponse,
    HealthResponse,
    MemoryStatsResponse,
    ProcessMemoryStats,
    StreamChunk,
)

__all__ = [
    # Router factory
    "create_chat_router",
    # Request schemas
    "ChatRequest",
    "FileUploadRequest",
    # Response schemas
    "ChatResponse",
    "StreamChunk",
    "ConversationResponse",
    "ConversationListResponse",
    "HealthResponse",
    "ErrorResponse",
    # Memory management schemas
    "ProcessMemoryStats",
    "CacheStats",
    "CleanupCycleStats",
    "MemoryStatsResponse",
    "CleanupHistoryResponse",
    "ForceCleanupResponse",
]
