"""WebSocket-specific exceptions."""

from typing import Optional


class WebSocketError(Exception):
    """Base exception for WebSocket errors."""

    pass


class WebSocketConnectionError(WebSocketError):
    """Failed to establish connection."""

    pass


class WebSocketClosedError(WebSocketError):
    """Connection was closed unexpectedly."""

    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        reason: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.reason = reason


class WebSocketTimeoutError(WebSocketError):
    """Operation timed out."""

    pass


class WebSocketReconnectExhausted(WebSocketError):
    """All reconnection attempts failed."""

    pass


class WebSocketSendError(WebSocketError):
    """Failed to send message."""

    pass


class WebSocketBackpressureError(WebSocketError):
    """Send queue is full - consumer cannot keep up."""

    pass
