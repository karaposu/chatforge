"""WebSocket types and configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from .serializers import MessageSerializer


class ConnectionState(Enum):
    """WebSocket connection states."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    CLOSING = auto()
    CLOSED = auto()


class MessageType(Enum):
    """WebSocket message types."""

    TEXT = auto()
    BINARY = auto()


@dataclass
class WebSocketMessage:
    """A WebSocket message with type information."""

    data: Union[str, bytes]
    type: MessageType

    @property
    def is_text(self) -> bool:
        return self.type == MessageType.TEXT

    @property
    def is_binary(self) -> bool:
        return self.type == MessageType.BINARY

    def as_text(self) -> str:
        if isinstance(self.data, bytes):
            return self.data.decode("utf-8")
        return self.data

    def as_bytes(self) -> bytes:
        if isinstance(self.data, str):
            return self.data.encode("utf-8")
        return self.data


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket client."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    subprotocols: list[str] = field(default_factory=list)

    # Timeouts (seconds)
    connect_timeout: float = 10.0
    close_timeout: float = 5.0
    ping_interval: float = 20.0
    ping_timeout: float = 10.0

    # Reconnection
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5  # 0 = infinite
    reconnect_backoff_base: float = 1.0
    reconnect_backoff_max: float = 60.0
    reconnect_backoff_factor: float = 2.0

    # Limits
    max_message_size: int = 10 * 1024 * 1024  # 10MB
    max_queue_size: int = 1000

    # Performance tuning (Fast Lane / Big Lane pattern)
    enable_send_queue: bool = True  # False for low-latency "fast lane"
    enable_metrics: bool = True  # False to disable metrics tracking
    send_queue_size: int = 100  # Max items in send queue
    send_queue_timeout: float = 1.0  # Backpressure timeout in seconds

    # Serialization
    # Set to JsonSerializer() or RawSerializer() - see serializers.py
    serializer: MessageSerializer | None = None  # None = raw bytes

    # Optional features
    compression: str | None = None  # e.g., "deflate"

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if self.ping_interval < 0:
            raise ValueError("ping_interval must be non-negative")
        if self.ping_timeout <= 0:
            raise ValueError("ping_timeout must be positive")
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        if self.send_queue_size <= 0:
            raise ValueError("send_queue_size must be positive")
        if self.send_queue_timeout <= 0:
            raise ValueError("send_queue_timeout must be positive")
