"""
Pydantic Schemas for Chatforge REST API.

Defines request and response models for the chat API endpoints.
All models include validation and OpenAPI documentation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class ChatRequest(BaseModel):
    """
    Request schema for chat endpoint.

    Example:
        {
            "message": "Hello, I need help",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user-123",
            "user_email": "user@example.com"
        }
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message to send to the agent",
        examples=["Hello, I need help", "What can you do?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Conversation session ID. Auto-generated if not provided.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_id: str | None = Field(
        default=None,
        description="User identifier for conversation history",
        examples=["user-123"],
    )
    user_email: str | None = Field(
        default=None,
        description="User email for context",
        examples=["user@example.com"],
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata to include with the request",
    )


class FileUploadRequest(BaseModel):
    """Schema for file upload information."""

    filename: str = Field(..., description="Original filename")
    mimetype: str = Field(..., description="MIME type of the file")
    content_base64: str = Field(..., description="Base64-encoded file content")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class ChatResponse(BaseModel):
    """
    Response schema for chat endpoint.

    Example:
        {
            "response": "Here's the information you requested...",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "trace_id": "abc123"
        }
    """

    response: str = Field(
        ...,
        description="Agent's response message",
    )
    session_id: str = Field(
        ...,
        description="Conversation session ID",
    )
    trace_id: str | None = Field(
        default=None,
        description="Trace ID for feedback linking",
    )
    tool_calls: list[str] | None = Field(
        default=None,
        description="List of tools invoked during processing",
    )


class StreamChunk(BaseModel):
    """
    Schema for SSE stream chunks.

    Used for streaming responses via Server-Sent Events.
    """

    type: str = Field(
        ...,
        description="Chunk type: 'token', 'tool_call', 'done', 'error'",
    )
    content: str | None = Field(
        default=None,
        description="Text content for token chunks",
    )
    tool_name: str | None = Field(
        default=None,
        description="Tool name for tool_call chunks",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID (included in 'done' chunk)",
    )
    trace_id: str | None = Field(
        default=None,
        description="Trace ID (included in 'done' chunk)",
    )
    error: str | None = Field(
        default=None,
        description="Error message for error chunks",
    )


class ConversationResponse(BaseModel):
    """Response schema for conversation retrieval."""

    conversation_id: str
    messages: list[dict[str, str]]
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Response schema for listing conversations."""

    conversations: list[ConversationResponse]
    total: int


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current server timestamp",
    )
    components: dict[str, bool] = Field(
        default_factory=dict,
        description="Health status of individual components",
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    detail: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )


# =============================================================================
# MEMORY MANAGEMENT SCHEMAS
# =============================================================================


class ProcessMemoryStats(BaseModel):
    """Process memory statistics."""

    rss_mb: float = Field(..., description="Resident Set Size in MB")
    vms_mb: float | None = Field(default=None, description="Virtual Memory Size in MB")
    percent: float | None = Field(
        default=None, description="Memory usage as percentage of total"
    )


class CacheStats(BaseModel):
    """Cache statistics."""

    name: str = Field(..., description="Cache name")
    size: int = Field(default=0, description="Current cache size")
    max_size: int | None = Field(default=None, description="Maximum cache size")
    ttl_seconds: int | None = Field(default=None, description="Cache TTL in seconds")


class CleanupCycleStats(BaseModel):
    """Statistics for a single cleanup cycle."""

    timestamp: datetime = Field(..., description="When the cleanup occurred")
    duration_ms: float = Field(..., description="Duration of cleanup in milliseconds")
    items_cleaned: dict[str, int] = Field(
        default_factory=dict, description="Items cleaned per component"
    )
    total_cleaned: int = Field(default=0, description="Total items cleaned")


class MemoryStatsResponse(BaseModel):
    """Response schema for memory statistics endpoint."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    process: ProcessMemoryStats | None = Field(
        default=None, description="Process memory stats"
    )
    caches: list[CacheStats] = Field(default_factory=list, description="Cache statistics")
    cleanup_running: bool = Field(..., description="Is cleanup service active")
    last_cleanup: CleanupCycleStats | None = Field(
        default=None, description="Last cleanup cycle stats"
    )


class CleanupHistoryResponse(BaseModel):
    """Response schema for cleanup history endpoint."""

    cycles: list[CleanupCycleStats] = Field(default_factory=list)
    total_cycles: int = Field(default=0)
    avg_items_per_cycle: float = Field(default=0.0)
    last_24h_total_cleaned: int = Field(default=0)


class ForceCleanupResponse(BaseModel):
    """Response schema for force cleanup endpoint."""

    success: bool = Field(..., description="Whether cleanup completed successfully")
    items_cleaned: dict[str, int] = Field(
        default_factory=dict, description="Items cleaned per component"
    )
    duration_ms: float = Field(..., description="Cleanup duration in milliseconds")
    message: str = Field(..., description="Status message")
