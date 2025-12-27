"""
Tracing Port - Interface for observability and tracing operations.

This port defines the contract for tracing implementations, enabling:
- MLflow tracing
- Langsmith tracing
- OpenTelemetry tracing
- Mock implementation for testing

The port abstracts tracing operations so the core domain doesn't depend
on specific tracing infrastructure.
"""

from __future__ import annotations

from abc import abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Generator


@runtime_checkable
class TracingPort(Protocol):
    """
    Port for tracing and observability operations.

    This protocol defines the interface that all tracing adapters must implement.
    It provides methods for:
    - Checking if tracing is enabled
    - Creating and managing trace spans
    - Setting trace metadata and context
    - Logging user feedback on traces
    - Linking platform messages to traces
    """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Check if tracing is enabled.

        Returns:
            True if tracing is active and should be used, False otherwise.
        """
        ...

    @abstractmethod
    def invoke_with_span(
        self,
        llm: Any,
        messages: list,
        span_name: str,
        inputs: dict[str, Any] | None = None,
        output_key: str = "response_length",
        capture_messages: bool = False,
        capture_response: bool = False,
    ) -> Any:
        """
        Invoke an LLM with automatic span tracing.

        If tracing is disabled, invokes the LLM directly without overhead.
        If enabled, creates a child span with inputs/outputs recorded.

        Args:
            llm: The LLM instance to invoke
            messages: Messages to send to the LLM
            span_name: Name for the tracing span
            inputs: Optional dict of inputs to record on the span
            output_key: Key name for the output length metric
            capture_messages: If True, capture message contents in span inputs
            capture_response: If True, capture full response in span outputs

        Returns:
            The LLM response object
        """
        ...

    @abstractmethod
    @contextmanager
    def span(
        self,
        name: str,
        inputs: dict[str, Any] | None = None,
    ) -> Generator[Any, None, None]:
        """
        Context manager for creating a tracing span.

        If tracing is disabled, yields None and does nothing.
        If enabled, creates a span and yields the span object.

        Args:
            name: Name for the span
            inputs: Optional inputs to set on the span

        Yields:
            The span object (implementation-specific), or None if disabled
        """
        ...

    @abstractmethod
    def get_active_trace_id(self) -> str | None:
        """
        Get the current active trace ID.

        Returns:
            The trace ID string, or None if no active trace or tracing disabled
        """
        ...

    @abstractmethod
    def set_trace_metadata(self, metadata: dict[str, str]) -> bool:
        """
        Set metadata on the current trace.

        Args:
            metadata: Dict of metadata key-value pairs

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def log_feedback(
        self,
        context_id: str,
        is_positive: bool,
        user_id: str,
        rationale: str | None = None,
    ) -> bool:
        """
        Log user feedback by finding the trace associated with a context.

        Args:
            context_id: Context identifier (message ID, thread ID, etc.)
            is_positive: True for positive feedback, False for negative
            user_id: ID of the user who provided feedback
            rationale: Optional text explanation for the feedback

        Returns:
            True if feedback was logged successfully, False otherwise
        """
        ...

    @abstractmethod
    def set_platform_context_on_trace(
        self,
        trace_id: str,
        platform_context: dict[str, Any],
    ) -> bool:
        """
        Set platform context metadata on a completed trace.

        This links the trace to a platform message for feedback tracking.

        Args:
            trace_id: The trace ID to update
            platform_context: Dict containing platform-specific context

        Returns:
            True if context was set successfully, False otherwise
        """
        ...


class NullTracingAdapter:
    """
    Null implementation of TracingPort that does nothing.

    Use this when tracing is disabled or for testing without tracing.
    All operations are no-ops that return sensible defaults.
    """

    @property
    def enabled(self) -> bool:
        """Always returns False - tracing is disabled."""
        return False

    def invoke_with_span(
        self,
        llm: Any,
        messages: list,
        span_name: str,
        inputs: dict[str, Any] | None = None,
        output_key: str = "response_length",
        capture_messages: bool = False,
        capture_response: bool = False,
    ) -> Any:
        """Invoke LLM directly without tracing."""
        return llm.invoke(messages)

    @contextmanager
    def span(
        self,
        name: str,
        inputs: dict[str, Any] | None = None,
    ) -> Generator[None, None, None]:
        """Yield None - no span created."""
        yield None

    def get_active_trace_id(self) -> str | None:
        """Return None - no active trace."""
        return None

    def set_trace_metadata(
        self,
        metadata: dict[str, str],
    ) -> bool:
        """No-op, return False."""
        return False

    def log_feedback(
        self,
        context_id: str,
        is_positive: bool,
        user_id: str,
        rationale: str | None = None,
    ) -> bool:
        """No-op, return False."""
        return False

    def set_platform_context_on_trace(
        self,
        trace_id: str,
        platform_context: dict[str, Any],
    ) -> bool:
        """No-op, return False."""
        return False
