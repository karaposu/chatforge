"""
Chatforge Exception Hierarchy.

This module provides a structured exception hierarchy for Chatforge applications:
- Clear distinction between different error types
- Proper error propagation from adapters to tools to handlers
- User-friendly error messages separate from internal details
- Better error recovery and handling strategies

Exception Hierarchy:
    ChatforgeError (base)
    ├── AdapterError (external service failures)
    ├── ToolExecutionError (agent tool failures)
    ├── ConfigurationError (settings/config issues)
    └── ValidationError (input validation failures)

Usage:
    from chatforge.exceptions import AdapterError, ToolExecutionError

    # In an adapter
    class MyServiceAdapter:
        def call_api(self):
            try:
                result = self._client.request(...)
            except ServiceError as e:
                raise AdapterError(
                    f"Service call failed: {e}",
                    original_error=e,
                ) from e

    # In a tool
    class MyTool:
        def run(self, input):
            try:
                result = adapter.call_api()
            except AdapterError as e:
                raise ToolExecutionError(
                    user_message="Could not complete the request. Please try again.",
                    internal_message=str(e),
                )

Extending for your application:
    from chatforge.exceptions import AdapterError

    class JiraAdapterError(AdapterError):
        '''Jira-specific adapter error.'''

    class NotionAdapterError(AdapterError):
        '''Notion-specific adapter error.'''
"""

from __future__ import annotations


class ChatforgeError(Exception):
    """
    Base exception for all Chatforge errors.

    All custom exceptions in Chatforge applications should inherit from this
    class to enable catching all application-specific errors.

    Example:
        try:
            agent.process_message(...)
        except ChatforgeError as e:
            logger.error(f"Chatforge error: {e}")
    """


# =============================================================================
# Adapter Errors
# =============================================================================


class AdapterError(ChatforgeError):
    """
    Base exception for adapter/integration failures.

    Raised when external services fail or return errors. Adapters should
    wrap third-party exceptions in these for consistent handling.

    Attributes:
        message: Human-readable error description.
        original_error: The underlying exception from the third-party library.
        service_name: Optional name of the service that failed.

    Example:
        try:
            response = self._client.create_resource(data)
        except ClientError as e:
            raise AdapterError(
                message=f"Failed to create resource: {e}",
                original_error=e,
                service_name="MyService",
            ) from e
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        service_name: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.original_error = original_error
        self.service_name = service_name

    def __str__(self) -> str:
        parts = [self.message]
        if self.service_name:
            parts.insert(0, f"[{self.service_name}]")
        if self.original_error:
            parts.append(f"(caused by: {type(self.original_error).__name__})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"service_name={self.service_name!r}, "
            f"original_error={self.original_error!r})"
        )


# =============================================================================
# Tool Errors
# =============================================================================


class ToolExecutionError(ChatforgeError):
    """
    Exception for agent tool execution failures.

    This exception separates user-facing messages from internal details,
    allowing tools to provide helpful feedback to users while logging
    technical details for debugging.

    Attributes:
        user_message: Safe message to show to the user.
        internal_message: Detailed message for logging/debugging.
        tool_name: Optional name of the tool that failed.

    Example:
        raise ToolExecutionError(
            user_message="Could not find relevant documentation.",
            internal_message=f"Search API failed after 3 retries: {e}",
            tool_name="search_docs",
        )
    """

    def __init__(
        self,
        user_message: str,
        internal_message: str | None = None,
        tool_name: str | None = None,
    ):
        self.user_message = user_message
        self.internal_message = internal_message or user_message
        self.tool_name = tool_name
        super().__init__(self.internal_message)

    def __str__(self) -> str:
        if self.tool_name:
            return f"[{self.tool_name}] {self.internal_message}"
        return self.internal_message

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"user_message={self.user_message!r}, "
            f"internal_message={self.internal_message!r}, "
            f"tool_name={self.tool_name!r})"
        )


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(ChatforgeError):
    """
    Exception for configuration/settings errors.

    Raised when required configuration is missing or invalid.
    Typically caught at application startup.

    Attributes:
        message: Description of the configuration problem.
        config_key: Optional key/name of the problematic configuration.

    Example:
        if not settings.api_key:
            raise ConfigurationError(
                "API key is required",
                config_key="API_KEY",
            )
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.config_key = config_key

    def __str__(self) -> str:
        if self.config_key:
            return f"Configuration error [{self.config_key}]: {self.message}"
        return f"Configuration error: {self.message}"


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(ChatforgeError):
    """
    Exception for input validation failures.

    Raised when user input or data doesn't meet requirements.
    Should include helpful information about what's wrong.

    Attributes:
        message: Description of the validation failure.
        field: Optional field/parameter that failed validation.
        value: Optional invalid value (be careful with sensitive data).

    Example:
        if not title.strip():
            raise ValidationError(
                "Title cannot be empty",
                field="title",
            )

        if priority not in ["low", "medium", "high"]:
            raise ValidationError(
                "Priority must be one of: low, medium, high",
                field="priority",
                value=priority,
            )
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.insert(0, f"[{self.field}]")
        if self.value is not None:
            parts.append(f"(got: {self.value!r})")
        return " ".join(parts)


# =============================================================================
# Middleware Errors
# =============================================================================


class MiddlewareError(ChatforgeError):
    """
    Exception for middleware processing failures.

    Raised when middleware (PII detection, safety checks, etc.) encounters
    an error during processing.

    Attributes:
        message: Description of the middleware failure.
        middleware_name: Name of the middleware that failed.
        blocked: Whether the request was intentionally blocked (not an error).

    Example:
        raise MiddlewareError(
            "Safety check failed",
            middleware_name="SafetyGuardrail",
            blocked=True,
        )
    """

    def __init__(
        self,
        message: str,
        middleware_name: str | None = None,
        blocked: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.middleware_name = middleware_name
        self.blocked = blocked

    def __str__(self) -> str:
        prefix = f"[{self.middleware_name}] " if self.middleware_name else ""
        suffix = " (blocked)" if self.blocked else ""
        return f"{prefix}{self.message}{suffix}"


# =============================================================================
# Agent Errors
# =============================================================================


class AgentError(ChatforgeError):
    """
    Exception for agent execution failures.

    Raised when the ReACT agent encounters an unrecoverable error
    during message processing.

    Attributes:
        message: Description of the agent failure.
        trace_id: Optional trace ID for debugging.

    Example:
        raise AgentError(
            "Agent exceeded maximum iterations",
            trace_id="abc123",
        )
    """

    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id

    def __str__(self) -> str:
        if self.trace_id:
            return f"{self.message} (trace_id: {self.trace_id})"
        return self.message
