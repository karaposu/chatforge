"""WebSocket client infrastructure."""

from .client import WebSocketClient
from .exceptions import (
    WebSocketBackpressureError,
    WebSocketClosedError,
    WebSocketConnectionError,
    WebSocketError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
    WebSocketTimeoutError,
)
from .metrics import ConnectionMetrics
from .reconnect import (
    ExponentialBackoff,
    FixedDelay,
    NoReconnect,
    ReconnectPolicy,
)
from .serializers import (
    JsonSerializer,
    MessageSerializer,
    MsgPackSerializer,
    RawSerializer,
)
from .types import (
    ConnectionState,
    MessageType,
    WebSocketConfig,
    WebSocketMessage,
)

__all__ = [
    # Client
    "WebSocketClient",
    # Types
    "ConnectionState",
    "MessageType",
    "WebSocketMessage",
    "WebSocketConfig",
    # Reconnect policies
    "ReconnectPolicy",
    "ExponentialBackoff",
    "NoReconnect",
    "FixedDelay",
    # Serializers
    "MessageSerializer",
    "JsonSerializer",
    "RawSerializer",
    "MsgPackSerializer",
    # Metrics
    "ConnectionMetrics",
    # Exceptions
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketClosedError",
    "WebSocketTimeoutError",
    "WebSocketReconnectExhausted",
    "WebSocketSendError",
    "WebSocketBackpressureError",
]
