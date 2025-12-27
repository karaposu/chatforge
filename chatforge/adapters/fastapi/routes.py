"""
FastAPI Routes Factory for Chatforge REST API.

Provides a factory function to create API routers with injected dependencies.

Endpoints:
- POST /chat - Synchronous chat
- POST /chat/stream - Streaming chat (SSE)
- GET /conversations/{id} - Get conversation history
- DELETE /conversations/{id} - Delete conversation
- GET /conversations - List conversations
- GET /health - Health check
- GET /memory/stats - Memory statistics
- POST /memory/cleanup - Force cleanup

Usage:
    from chatforge.adapters.fastapi import create_chat_router

    router = create_chat_router(
        agent=my_agent,
        storage=my_storage,
        cleanup_runner=my_cleanup_runner,
    )

    app.include_router(router, prefix="/api/v1")
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from chatforge.adapters.fastapi.schemas import (
    CacheStats,
    ChatRequest,
    ChatResponse,
    CleanupCycleStats,
    CleanupHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    ErrorResponse,
    ForceCleanupResponse,
    HealthResponse,
    MemoryStatsResponse,
    ProcessMemoryStats,
    StreamChunk,
)
from chatforge.ports import MessageRecord, StoragePort


if TYPE_CHECKING:
    from chatforge.services.agent import ReActAgent
    from chatforge.services import AsyncCleanupRunner


logger = logging.getLogger(__name__)


def create_chat_router(
    agent: ReActAgent,
    storage: StoragePort | None = None,
    cleanup_runner: AsyncCleanupRunner | None = None,
    version: str = "1.0.0",
    prefix: str = "",
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create a FastAPI router with chat endpoints.

    This factory function creates a router with all necessary dependencies
    injected, avoiding global state.

    Args:
        agent: ReActAgent instance for processing messages.
        storage: Optional StoragePort for conversation persistence.
        cleanup_runner: Optional cleanup runner for memory management.
        version: API version string for health endpoint.
        prefix: Optional URL prefix for all routes.
        tags: Optional OpenAPI tags.

    Returns:
        Configured APIRouter with all chat endpoints.

    Example:
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
    router = APIRouter(prefix=prefix, tags=tags or ["chat"])

    # =========================================================================
    # CHAT ENDPOINTS
    # =========================================================================

    @router.post(
        "/chat",
        response_model=ChatResponse,
        responses={
            400: {"model": ErrorResponse, "description": "Invalid request"},
            503: {"model": ErrorResponse, "description": "Service unavailable"},
        },
        summary="Send a chat message",
        description="Send a message to the agent and receive a response.",
    )
    async def chat(request: ChatRequest):
        """Process a chat message synchronously."""
        session_id = request.session_id or str(uuid4())
        user_id = request.user_id or "anonymous"

        try:
            # Get conversation history if storage available
            history: list[dict[str, str]] = []
            if storage:
                conv = await storage.get_conversation(session_id, limit=50)
                if conv:
                    history = [{"role": m.role, "content": m.content} for m in conv.messages]

            # Build context
            context: dict[str, Any] = {
                "user_id": user_id,
                "session_id": session_id,
            }
            if request.user_email:
                context["user_email"] = request.user_email
            if request.metadata:
                context.update(request.metadata)

            # Process with agent
            response, trace_id = agent.process_message(
                request.message,
                history,
                context=context,
            )

            # Save messages if storage available
            if storage:
                # Save user message
                await storage.save_message(
                    conversation_id=session_id,
                    message=MessageRecord(content=request.message, role="user"),
                )
                # Save assistant response
                await storage.save_message(
                    conversation_id=session_id,
                    message=MessageRecord(content=response, role="assistant"),
                )

            logger.info(f"Chat processed: session={session_id}, trace_id={trace_id}")

            return ChatResponse(
                response=response,
                session_id=session_id,
                trace_id=trace_id,
            )

        except Exception as e:
            logger.error(f"Error processing chat: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing request: {e!s}",
            ) from e

    @router.post(
        "/chat/stream",
        responses={
            400: {"model": ErrorResponse, "description": "Invalid request"},
            503: {"model": ErrorResponse, "description": "Service unavailable"},
        },
        summary="Stream a chat response",
        description="Send a message and receive streaming response via Server-Sent Events.",
    )
    async def chat_stream(request: ChatRequest):
        """Process a chat message with streaming response (SSE)."""
        session_id = request.session_id or str(uuid4())
        user_id = request.user_id or "anonymous"

        async def generate() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                # Get history if storage available
                history: list[dict[str, str]] = []
                if storage:
                    conv = await storage.get_conversation(session_id, limit=50)
                    if conv:
                        history = [
                            {"role": m.role, "content": m.content} for m in conv.messages
                        ]

                # Build context
                context: dict[str, Any] = {
                    "user_id": user_id,
                    "session_id": session_id,
                }
                if request.user_email:
                    context["user_email"] = request.user_email

                # Process with agent (non-streaming for now)
                # TODO: Implement true streaming when agent supports astream_events
                response, trace_id = agent.process_message(
                    request.message,
                    history,
                    context=context,
                )

                # Stream the response in chunks (simulated)
                chunk_size = 50
                for i in range(0, len(response), chunk_size):
                    chunk = response[i : i + chunk_size]
                    event = StreamChunk(type="token", content=chunk)
                    yield f"data: {json.dumps(event.model_dump())}\n\n"

                # Save messages if storage available
                if storage:
                    await storage.save_message(
                        conversation_id=session_id,
                        message=MessageRecord(content=request.message, role="user"),
                    )
                    await storage.save_message(
                        conversation_id=session_id,
                        message=MessageRecord(content=response, role="assistant"),
                    )

                # Send done event
                done_event = StreamChunk(
                    type="done",
                    session_id=session_id,
                    trace_id=trace_id,
                )
                yield f"data: {json.dumps(done_event.model_dump())}\n\n"

            except Exception as e:
                logger.error(f"Error in stream: {e}", exc_info=True)
                error_event = StreamChunk(type="error", error=str(e))
                yield f"data: {json.dumps(error_event.model_dump())}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # =========================================================================
    # CONVERSATION ENDPOINTS
    # =========================================================================

    @router.get(
        "/conversations/{conversation_id}",
        response_model=ConversationResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Conversation not found"},
            501: {"model": ErrorResponse, "description": "Storage not configured"},
        },
        summary="Get conversation history",
        description="Retrieve the message history for a specific conversation.",
    )
    async def get_conversation(
        conversation_id: str,
        limit: int = 50,
    ):
        """Get conversation history."""
        if not storage:
            raise HTTPException(status_code=501, detail="Storage not configured")

        conv = await storage.get_conversation(conversation_id, limit=limit)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationResponse(
            conversation_id=conversation_id,
            messages=[{"role": m.role, "content": m.content} for m in conv.messages],
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    @router.delete(
        "/conversations/{conversation_id}",
        responses={
            404: {"model": ErrorResponse, "description": "Conversation not found"},
            501: {"model": ErrorResponse, "description": "Storage not configured"},
        },
        summary="Delete a conversation",
        description="Delete a conversation and all its messages.",
    )
    async def delete_conversation(conversation_id: str):
        """Delete a conversation."""
        if not storage:
            raise HTTPException(status_code=501, detail="Storage not configured")

        deleted = await storage.delete_conversation(conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"message": "Conversation deleted", "conversation_id": conversation_id}

    @router.get(
        "/conversations",
        response_model=ConversationListResponse,
        responses={
            501: {"model": ErrorResponse, "description": "Storage not configured"},
        },
        summary="List conversations",
        description="List all conversations, optionally filtered by user.",
    )
    async def list_conversations(
        user_id: str | None = None,
        limit: int = 100,
    ):
        """List conversations."""
        if not storage:
            raise HTTPException(status_code=501, detail="Storage not configured")

        conversations = await storage.list_conversations(user_id=user_id, limit=limit)

        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    conversation_id=c.conversation_id,
                    messages=[],  # Don't include messages in list view
                    user_id=c.user_id,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
                for c in conversations
            ],
            total=len(conversations),
        )

    # =========================================================================
    # HEALTH ENDPOINT
    # =========================================================================

    @router.get(
        "/health",
        response_model=HealthResponse,
        summary="Health check",
        description="Check the health status of the API and its dependencies.",
    )
    async def health_check():
        """Health check endpoint."""
        components: dict[str, bool] = {}

        # Check storage if available
        if storage and hasattr(storage, "health_check"):
            components["storage"] = await storage.health_check()

        all_healthy = all(components.values()) if components else True

        return HealthResponse(
            status="healthy" if all_healthy else "unhealthy",
            version=version,
            timestamp=datetime.now(tz=timezone.utc),
            components=components,
        )

    # =========================================================================
    # MEMORY MANAGEMENT ENDPOINTS
    # =========================================================================

    @router.get(
        "/memory/stats",
        response_model=MemoryStatsResponse,
        summary="Memory statistics",
        description="Get current memory usage statistics.",
        tags=["monitoring"],
    )
    async def get_memory_stats():
        """Get memory statistics."""
        process_stats = None

        try:
            import psutil

            process = psutil.Process()
            mem_info = process.memory_info()

            process_stats = ProcessMemoryStats(
                rss_mb=round(mem_info.rss / (1024 * 1024), 2),
                vms_mb=round(mem_info.vms / (1024 * 1024), 2),
                percent=round(process.memory_percent(), 2),
            )
        except ImportError:
            logger.debug("psutil not available for memory stats")

        # Get cleanup service status
        cleanup_running = cleanup_runner is not None and cleanup_runner.is_running

        # Get last cleanup stats
        last_cleanup = None
        if cleanup_runner and hasattr(cleanup_runner, "get_last_cleanup_stats"):
            stats = cleanup_runner.get_last_cleanup_stats()
            if stats:
                last_cleanup = CleanupCycleStats(
                    timestamp=stats["timestamp"],
                    duration_ms=stats["duration_ms"],
                    items_cleaned=stats.get("items_cleaned", {}),
                    total_cleaned=stats.get("total_cleaned", 0),
                )

        return MemoryStatsResponse(
            timestamp=datetime.now(tz=timezone.utc),
            process=process_stats,
            caches=[],  # Applications can extend this
            cleanup_running=cleanup_running,
            last_cleanup=last_cleanup,
        )

    @router.get(
        "/memory/cleanup-history",
        response_model=CleanupHistoryResponse,
        summary="Cleanup history",
        description="Get recent cleanup cycle history and statistics.",
        tags=["monitoring"],
    )
    async def get_cleanup_history_endpoint(limit: int = 50):
        """Get cleanup cycle history."""
        if not cleanup_runner or not hasattr(cleanup_runner, "get_cleanup_history"):
            return CleanupHistoryResponse(
                cycles=[],
                total_cycles=0,
                avg_items_per_cycle=0.0,
                last_24h_total_cleaned=0,
            )

        history = cleanup_runner.get_cleanup_history(limit=limit)
        cycles = [
            CleanupCycleStats(
                timestamp=datetime.fromisoformat(c["timestamp"])
                if isinstance(c["timestamp"], str)
                else c["timestamp"],
                duration_ms=c["duration_ms"],
                items_cleaned=c.get("items_cleaned", {}),
                total_cleaned=c.get("total_cleaned", 0),
            )
            for c in history.get("cycles", [])
        ]

        return CleanupHistoryResponse(
            cycles=cycles,
            total_cycles=history.get("total_cycles", 0),
            avg_items_per_cycle=history.get("avg_items_per_cycle", 0.0),
            last_24h_total_cleaned=history.get("last_24h_total_cleaned", 0),
        )

    @router.post(
        "/memory/cleanup",
        response_model=ForceCleanupResponse,
        summary="Force cleanup",
        description="Force immediate cleanup. Use sparingly.",
        tags=["monitoring"],
    )
    async def force_cleanup_endpoint():
        """Force immediate cleanup."""
        start_time = time.time()

        if not cleanup_runner:
            return ForceCleanupResponse(
                success=False,
                items_cleaned={},
                duration_ms=0.0,
                message="Cleanup service not configured",
            )

        try:
            metrics = await cleanup_runner.run_cleanup_cycle()
            duration_ms = (time.time() - start_time) * 1000

            return ForceCleanupResponse(
                success=metrics.error is None,
                items_cleaned=metrics.items_cleaned,
                duration_ms=round(duration_ms, 2),
                message="Cleanup completed successfully"
                if metrics.error is None
                else f"Cleanup completed with errors: {metrics.error}",
            )
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}", exc_info=True)
            duration_ms = (time.time() - start_time) * 1000
            return ForceCleanupResponse(
                success=False,
                items_cleaned={},
                duration_ms=round(duration_ms, 2),
                message=f"Cleanup failed: {e!s}",
            )

    return router
