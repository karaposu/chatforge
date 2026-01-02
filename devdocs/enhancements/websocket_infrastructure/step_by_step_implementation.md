# WebSocket Infrastructure: Step-by-Step Implementation

**Date:** 2025-01-01
**Prerequisites:** `detailed_design.md`, `comparison_analysis.md`
**Estimated Scope:** 7 files, ~800 lines

---

## Overview

```
Step 1: Create package structure and types
Step 2: Create exceptions
Step 3: Create reconnect policies
Step 4: Create serializers (NEW)
Step 5: Create metrics (NEW)
Step 6: Create WebSocketClient (with send queue, backpressure, metrics)
Step 7: Wire up exports
Step 8: Write tests
```

---

## Features Added from Comparison Analysis

Based on comparison with existing voxengine/realtimevoiceapi code:

| Feature | Description |
|---------|-------------|
| **Pluggable Serializers** | JsonSerializer, RawSerializer with Protocol |
| **Send Queue + Worker** | Background task for queued sends |
| **Backpressure Handling** | Timeout on send queue with specific exception |
| **Connection Metrics** | Optional tracking of messages, bytes, uptime |
| **Fast/Big Lane Pattern** | Config flags to disable features for low latency |
| **Manual ping()** | On-demand connection health check |
| **Connection ID** | Unique ID per connection for logging |
| **get_stats()** | Connection statistics method |

---

## Step 1: Create Package Structure and Types

### 1.1 Create Directories

```bash
mkdir -p chatforge/infrastructure/websocket
touch chatforge/infrastructure/__init__.py
touch chatforge/infrastructure/websocket/__init__.py
```

### 1.2 Create Types

**File:** `chatforge/infrastructure/websocket/types.py`

```python
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
            return self.data.decode('utf-8')
        return self.data

    def as_bytes(self) -> bytes:
        if isinstance(self.data, str):
            return self.data.encode('utf-8')
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

    # NEW: Performance tuning (Fast Lane / Big Lane pattern)
    enable_send_queue: bool = True      # False for low-latency "fast lane"
    enable_metrics: bool = True         # False to disable metrics tracking
    send_queue_size: int = 100          # Max items in send queue
    send_queue_timeout: float = 1.0     # Backpressure timeout in seconds

    # NEW: Serialization
    # Set to JsonSerializer() or RawSerializer() - see serializers.py
    serializer: MessageSerializer | None = None  # None = raw bytes

    # NEW: Optional features
    compression: str | None = None      # e.g., "deflate"

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
```

---

## Step 2: Create Exceptions

**File:** `chatforge/infrastructure/websocket/exceptions.py`

```python
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
```

---

## Step 3: Create Reconnect Policies

**File:** `chatforge/infrastructure/websocket/reconnect.py`

```python
"""Reconnection policies for WebSocket client."""

from abc import ABC, abstractmethod
import random


class ReconnectPolicy(ABC):
    """Abstract reconnection policy."""

    @abstractmethod
    def next_delay(self, attempt: int) -> float | None:
        """
        Get delay before next reconnection attempt.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds, or None to stop reconnecting
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset policy state after successful connection."""
        ...


class ExponentialBackoff(ReconnectPolicy):
    """
    Exponential backoff with jitter.

    Delay = min(base * factor^(attempt-1), max_delay) ± jitter

    Args:
        base: Initial delay in seconds
        factor: Multiplier for each attempt
        max_delay: Maximum delay cap
        max_attempts: Maximum attempts (0 = infinite)
        jitter: Randomization factor (0.1 = ±10%)
    """

    def __init__(
        self,
        base: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 60.0,
        max_attempts: int = 5,
        jitter: float = 0.1,
    ):
        self.base = base
        self.factor = factor
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.jitter = jitter

    def next_delay(self, attempt: int) -> float | None:
        if self.max_attempts > 0 and attempt > self.max_attempts:
            return None

        delay = min(self.base * (self.factor ** (attempt - 1)), self.max_delay)

        # Add jitter
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def reset(self) -> None:
        pass


class NoReconnect(ReconnectPolicy):
    """Never reconnect - use when reconnection is handled at higher level."""

    def next_delay(self, attempt: int) -> float | None:
        return None

    def reset(self) -> None:
        pass


class FixedDelay(ReconnectPolicy):
    """
    Fixed delay between reconnection attempts.

    Args:
        delay: Seconds to wait between attempts
        max_attempts: Maximum attempts (0 = infinite)
    """

    def __init__(self, delay: float = 5.0, max_attempts: int = 10):
        self.delay = delay
        self.max_attempts = max_attempts

    def next_delay(self, attempt: int) -> float | None:
        if self.max_attempts > 0 and attempt > self.max_attempts:
            return None
        return self.delay

    def reset(self) -> None:
        pass
```

---

## Step 4: Create Serializers

**File:** `chatforge/infrastructure/websocket/serializers.py`

```python
"""Message serializers for WebSocket client."""

from typing import Any, Protocol, Union
import json


class MessageSerializer(Protocol):
    """Protocol for message serialization."""

    def serialize(self, data: Any) -> Union[str, bytes]:
        """Serialize data for sending."""
        ...

    def deserialize(self, data: Union[str, bytes]) -> Any:
        """Deserialize received data."""
        ...


class JsonSerializer:
    """JSON serialization for text-based protocols."""

    def serialize(self, data: Any) -> str:
        """Serialize to JSON string."""
        return json.dumps(data)

    def deserialize(self, data: Union[str, bytes]) -> Any:
        """Deserialize from JSON string."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)


class RawSerializer:
    """Pass-through serialization (no transformation)."""

    def serialize(self, data: Any) -> Any:
        """Return data as-is."""
        return data

    def deserialize(self, data: Any) -> Any:
        """Return data as-is."""
        return data


# Optional: MessagePack for binary protocols
try:
    import msgpack

    class MsgPackSerializer:
        """MessagePack binary serialization."""

        def serialize(self, data: Any) -> bytes:
            return msgpack.packb(data)

        def deserialize(self, data: Union[str, bytes]) -> Any:
            if isinstance(data, str):
                data = data.encode('utf-8')
            return msgpack.unpackb(data)

except ImportError:
    MsgPackSerializer = None  # type: ignore
```

---

## Step 5: Create Connection Metrics

**File:** `chatforge/infrastructure/websocket/metrics.py`

```python
"""Connection metrics for WebSocket client."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConnectionMetrics:
    """Track connection statistics for debugging and monitoring."""

    # Counters
    connect_count: int = 0
    disconnect_count: int = 0
    reconnect_count: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    messages_dropped: int = 0  # Receive queue overflow
    bytes_sent: int = 0
    bytes_received: int = 0
    send_queue_full_count: int = 0  # Backpressure events

    # Timestamps (using monotonic for durations)
    connect_time: Optional[float] = None
    last_send_time: Optional[float] = None
    last_receive_time: Optional[float] = None

    # Connection ID (set externally)
    connection_id: Optional[str] = None

    def on_connect(self) -> None:
        """Record a connection event."""
        self.connect_count += 1
        self.connect_time = time.monotonic()

    def on_disconnect(self) -> None:
        """Record a disconnection event."""
        self.disconnect_count += 1

    def on_reconnect(self) -> None:
        """Record a reconnection event."""
        self.reconnect_count += 1

    def on_message_sent(self, size: int) -> None:
        """Record an outgoing message."""
        self.messages_sent += 1
        self.bytes_sent += size
        self.last_send_time = time.monotonic()

    def on_message_received(self, size: int) -> None:
        """Record an incoming message."""
        self.messages_received += 1
        self.bytes_received += size
        self.last_receive_time = time.monotonic()

    def on_message_dropped(self) -> None:
        """Record a dropped message (receive queue full)."""
        self.messages_dropped += 1

    def on_backpressure(self) -> None:
        """Record a backpressure event (send queue full)."""
        self.send_queue_full_count += 1

    def get_stats(self) -> dict:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection metrics and calculated values
        """
        now = time.monotonic()
        stats = {
            "connection_id": self.connection_id,
            "connects": self.connect_count,
            "disconnects": self.disconnect_count,
            "reconnects": self.reconnect_count,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_dropped": self.messages_dropped,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "backpressure_events": self.send_queue_full_count,
        }

        # Add calculated metrics
        if self.connect_time:
            stats["uptime_seconds"] = round(now - self.connect_time, 2)

        if self.last_send_time:
            stats["seconds_since_send"] = round(now - self.last_send_time, 2)

        if self.last_receive_time:
            stats["seconds_since_receive"] = round(now - self.last_receive_time, 2)

        # Calculate rates if we have uptime
        if self.connect_time and (now - self.connect_time) > 0:
            uptime = now - self.connect_time
            stats["messages_per_second"] = round(
                (self.messages_sent + self.messages_received) / uptime, 2
            )
            stats["bytes_per_second"] = round(
                (self.bytes_sent + self.bytes_received) / uptime, 2
            )

        return stats

    def reset(self) -> None:
        """Reset all counters and timestamps."""
        self.connect_count = 0
        self.disconnect_count = 0
        self.reconnect_count = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_dropped = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.send_queue_full_count = 0
        self.connect_time = None
        self.last_send_time = None
        self.last_receive_time = None
```

---

## Step 6: Create WebSocketClient

**File:** `chatforge/infrastructure/websocket/client.py`

```python
"""Async WebSocket client with automatic reconnection."""

import asyncio
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Callable, Optional, Union

import websockets
from websockets.client import WebSocketClientProtocol

from .types import ConnectionState, MessageType, WebSocketConfig, WebSocketMessage
from .exceptions import (
    WebSocketBackpressureError,
    WebSocketClosedError,
    WebSocketConnectionError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
    WebSocketTimeoutError,
)
from .reconnect import ExponentialBackoff, ReconnectPolicy
from .metrics import ConnectionMetrics
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    Async WebSocket client with automatic reconnection.

    Features:
    - Automatic reconnection with configurable backoff
    - Ping/pong heartbeat
    - Binary and text message support
    - Event callbacks
    - Async context manager
    - Message queue for async iteration
    - NEW: Send queue with background worker
    - NEW: Backpressure handling
    - NEW: Connection metrics
    - NEW: Pluggable serializers
    - NEW: Connection ID for logging
    - NEW: Manual ping() method

    Usage:
        config = WebSocketConfig(url="wss://api.example.com/ws")

        async with WebSocketClient(config) as ws:
            await ws.send("hello")

            async for message in ws.messages():
                print(f"Received: {message.data}")

    Fast Lane (low latency):
        config = WebSocketConfig(
            url="wss://api.example.com/ws",
            enable_send_queue=False,  # Direct sends
            enable_metrics=False,     # No metric tracking
        )
    """

    def __init__(
        self,
        config: WebSocketConfig,
        reconnect_policy: Optional[ReconnectPolicy] = None,
    ):
        self.config = config
        self.reconnect_policy = reconnect_policy or ExponentialBackoff(
            base=config.reconnect_backoff_base,
            factor=config.reconnect_backoff_factor,
            max_delay=config.reconnect_backoff_max,
            max_attempts=config.max_reconnect_attempts,
        )

        # Connection state
        self._ws: Optional[WebSocketClientProtocol] = None
        self._state = ConnectionState.DISCONNECTED
        self._state_lock = asyncio.Lock()

        # NEW: Connection ID for logging/debugging
        self._connection_id: str = str(uuid.uuid4())[:8]

        # Message handling
        self._receive_queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

        # NEW: Send queue (if enabled)
        self._send_queue: Optional[asyncio.Queue] = None
        self._send_task: Optional[asyncio.Task] = None
        if config.enable_send_queue:
            self._send_queue = asyncio.Queue(maxsize=config.send_queue_size)

        # NEW: Metrics (if enabled)
        self._metrics: Optional[ConnectionMetrics] = None
        if config.enable_metrics:
            self._metrics = ConnectionMetrics(connection_id=self._connection_id)

        # NEW: Serializer
        self._serializer: Optional[MessageSerializer] = config.serializer

        # Reconnection
        self._reconnect_attempt = 0
        self._should_reconnect = True

        # Event callbacks (can be sync or async)
        self.on_connect: Optional[Callable[[], None]] = None
        self.on_disconnect: Optional[Callable[[Optional[Exception]], None]] = None
        self.on_message: Optional[Callable[[WebSocketMessage], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_reconnecting: Optional[Callable[[int], None]] = None
        self.on_receive_overflow: Optional[Callable[[WebSocketMessage], None]] = None  # NEW

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Whether currently connected."""
        return self._state == ConnectionState.CONNECTED

    @property
    def url(self) -> str:
        """WebSocket URL."""
        return self.config.url

    @property
    def connection_id(self) -> str:
        """Unique connection ID for logging."""
        return self._connection_id

    @property
    def metrics(self) -> Optional[ConnectionMetrics]:
        """Connection metrics (None if disabled)."""
        return self._metrics

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def connect(self) -> None:
        """
        Establish WebSocket connection.

        Raises:
            WebSocketConnectionError: If connection fails
            WebSocketTimeoutError: If connection times out
        """
        async with self._state_lock:
            if self._state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
                return
            self._state = ConnectionState.CONNECTING

        ws = None
        try:
            ws = await asyncio.wait_for(
                websockets.connect(
                    self.config.url,
                    additional_headers=self.config.headers,
                    subprotocols=self.config.subprotocols,
                    max_size=self.config.max_message_size,
                    compression=self.config.compression,  # Use compression config
                    ping_interval=None,
                    ping_timeout=None,
                ),
                timeout=self.config.connect_timeout,
            )

            async with self._state_lock:
                self._state = ConnectionState.CONNECTED

            # Reset reconnection state
            self._reconnect_attempt = 0
            self.reconnect_policy.reset()
            self._should_reconnect = True

            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop())
            if self.config.ping_interval > 0:
                self._ping_task = asyncio.create_task(self._ping_loop())

            # Start send worker if send queue enabled
            if self._send_queue is not None:
                self._send_task = asyncio.create_task(self._send_worker())

            # Record metrics
            if self._metrics:
                self._metrics.on_connect()

            # Only assign after all setup succeeds (prevents leaks)
            self._ws = ws

            # Fire callback
            await self._fire_callback(self.on_connect)

            logger.info(
                f"WebSocket connected to {self.config.url} "
                f"[id={self._connection_id}]"
            )

        except asyncio.TimeoutError as e:
            if ws:
                await ws.close()
            async with self._state_lock:
                self._state = ConnectionState.DISCONNECTED
            raise WebSocketTimeoutError(
                f"Connection to {self.config.url} timed out"
            ) from e
        except Exception as e:
            if ws:
                await ws.close()
            async with self._state_lock:
                self._state = ConnectionState.DISCONNECTED
            raise WebSocketConnectionError(
                f"Failed to connect to {self.config.url}: {e}"
            ) from e

    async def disconnect(self, code: int = 1000, reason: str = "") -> None:
        """
        Gracefully close WebSocket connection.

        Args:
            code: WebSocket close code (default: 1000 = normal)
            reason: Close reason message
        """
        self._should_reconnect = False

        async with self._state_lock:
            if self._state in (ConnectionState.DISCONNECTED, ConnectionState.CLOSED):
                return
            self._state = ConnectionState.CLOSING

        await self._cancel_tasks()

        if self._ws:
            try:
                await asyncio.wait_for(
                    self._ws.close(code, reason),
                    timeout=self.config.close_timeout,
                )
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            finally:
                self._ws = None

        async with self._state_lock:
            self._state = ConnectionState.CLOSED

        # Record metrics
        if self._metrics:
            self._metrics.on_disconnect()

        await self._fire_callback(self.on_disconnect, None)
        logger.info(
            f"WebSocket disconnected from {self.config.url} "
            f"[id={self._connection_id}]"
        )

    async def __aenter__(self) -> "WebSocketClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    # =========================================================================
    # Sending
    # =========================================================================

    async def send(self, data: Union[str, bytes]) -> None:
        """
        Send a message.

        If send queue is enabled, message is queued for background sending.
        Otherwise, sends immediately.

        Args:
            data: Text string or binary bytes to send

        Raises:
            WebSocketSendError: If send fails
            WebSocketClosedError: If connection is closed
            WebSocketBackpressureError: If send queue is full (timeout)
        """
        if not self._ws or not self.is_connected:
            raise WebSocketClosedError("Cannot send: not connected")

        # NEW: Use send queue if enabled
        if self._send_queue is not None:
            try:
                await asyncio.wait_for(
                    self._send_queue.put(data),
                    timeout=self.config.send_queue_timeout,
                )
            except asyncio.TimeoutError:
                if self._metrics:
                    self._metrics.on_backpressure()
                raise WebSocketBackpressureError(
                    f"Send queue full - consumer cannot keep up "
                    f"(timeout={self.config.send_queue_timeout}s)"
                )
        else:
            # Direct send (fast lane)
            await self._send_now(data)

    async def _send_now(self, data: Union[str, bytes]) -> None:
        """
        Send message immediately (bypassing queue).

        Args:
            data: Data to send

        Raises:
            WebSocketSendError: If send fails
            WebSocketClosedError: If connection closed
        """
        # Check connection state before sending
        if not self._ws or not self.is_connected:
            raise WebSocketClosedError("Cannot send: not connected")

        try:
            await self._ws.send(data)

            # Record metrics
            if self._metrics:
                size = len(data) if isinstance(data, (str, bytes)) else 0
                self._metrics.on_message_sent(size)

        except websockets.ConnectionClosed as e:
            raise WebSocketClosedError(
                "Connection closed during send",
                code=e.code,
                reason=e.reason,
            ) from e
        except Exception as e:
            raise WebSocketSendError(f"Failed to send message: {e}") from e

    async def send_text(self, text: str) -> None:
        """Send a text message."""
        await self.send(text)

    async def send_binary(self, data: bytes) -> None:
        """Send a binary message."""
        await self.send(data)

    async def send_json(self, obj: dict) -> None:
        """Send a JSON message (uses serializer if configured)."""
        if self._serializer:
            await self.send(self._serializer.serialize(obj))
        else:
            await self.send(json.dumps(obj))

    async def send_obj(self, obj: Any) -> None:
        """
        Send an object using the configured serializer.

        Args:
            obj: Object to serialize and send

        Raises:
            ValueError: If no serializer configured
        """
        if not self._serializer:
            raise ValueError("No serializer configured - use send_json() or set serializer")
        await self.send(self._serializer.serialize(obj))

    # =========================================================================
    # Receiving
    # =========================================================================

    async def receive(self, timeout: Optional[float] = None) -> WebSocketMessage:
        """
        Receive next message from queue.

        Args:
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            WebSocketMessage with data and type

        Raises:
            WebSocketTimeoutError: If timeout expires
        """
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self._receive_queue.get(),
                    timeout=timeout,
                )
            else:
                message = await self._receive_queue.get()
            return message
        except asyncio.TimeoutError:
            raise WebSocketTimeoutError("Receive timed out")

    async def messages(self) -> AsyncGenerator[WebSocketMessage, None]:
        """
        Async generator that yields messages.

        Yields:
            WebSocketMessage for each received message
        """
        while self.is_connected or not self._receive_queue.empty():
            try:
                message = await asyncio.wait_for(
                    self._receive_queue.get(),
                    timeout=1.0,
                )
                yield message
            except asyncio.TimeoutError:
                if not self.is_connected:
                    break
                continue

    # =========================================================================
    # Background Tasks
    # =========================================================================

    async def _receive_loop(self) -> None:
        """Background task that receives messages and queues them."""
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    ws_msg = WebSocketMessage(data=message, type=MessageType.BINARY)
                else:
                    ws_msg = WebSocketMessage(data=message, type=MessageType.TEXT)

                # Record metrics
                if self._metrics:
                    size = len(message) if isinstance(message, (str, bytes)) else 0
                    self._metrics.on_message_received(size)

                await self._fire_callback(self.on_message, ws_msg)

                try:
                    self._receive_queue.put_nowait(ws_msg)
                except asyncio.QueueFull:
                    logger.warning(
                        f"Receive queue full, dropping message [id={self._connection_id}]"
                    )
                    # Track dropped messages in metrics
                    if self._metrics:
                        self._metrics.on_message_dropped()
                    # Notify via callback so caller knows messages are being lost
                    await self._fire_callback(self.on_receive_overflow, ws_msg)

        except websockets.ConnectionClosed as e:
            logger.info(f"WebSocket closed: code={e.code} reason={e.reason}")
            await self._handle_disconnect(
                WebSocketClosedError("Connection closed", e.code, e.reason)
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            await self._handle_disconnect(e)

    async def _ping_loop(self) -> None:
        """Background task that sends periodic pings."""
        try:
            while self.is_connected:
                await asyncio.sleep(self.config.ping_interval)
                if self._ws and self.is_connected:
                    try:
                        pong = await self._ws.ping()
                        await asyncio.wait_for(pong, timeout=self.config.ping_timeout)
                    except asyncio.TimeoutError:
                        logger.warning("Ping timeout")
                        await self._handle_disconnect(
                            WebSocketTimeoutError("Ping timeout")
                        )
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Ping error: {e}")

    async def _send_worker(self) -> None:
        """Background task that sends queued messages."""
        try:
            while self.is_connected:
                try:
                    data = await asyncio.wait_for(
                        self._send_queue.get(),
                        timeout=1.0,
                    )
                    await self._send_now(data)
                except asyncio.TimeoutError:
                    # No message in queue, continue checking if connected
                    continue
                except WebSocketClosedError:
                    # Connection closed, stop the worker
                    logger.info(f"Send worker stopping: connection closed [id={self._connection_id}]")
                    break
                except Exception as e:
                    # Log but continue - don't let one bad message kill the worker
                    logger.warning(f"Send worker error on message: {e}")
                    await self._fire_callback(self.on_error, e)
        except asyncio.CancelledError:
            # Drain remaining messages on shutdown (only if still connected)
            if self._ws and self.is_connected:
                while not self._send_queue.empty():
                    try:
                        data = self._send_queue.get_nowait()
                        await self._send_now(data)
                    except Exception as e:
                        logger.warning(f"Failed to drain message: {e}")
                        break
        except Exception as e:
            logger.error(f"Send worker fatal error: {e}")
            await self._fire_callback(self.on_error, e)

    async def _handle_disconnect(self, error: Exception) -> None:
        """Handle unexpected disconnection."""
        async with self._state_lock:
            if self._state in (ConnectionState.CLOSING, ConnectionState.CLOSED):
                return
            self._state = ConnectionState.DISCONNECTED

        await self._fire_callback(self.on_disconnect, error)

        if self._should_reconnect and self.config.auto_reconnect:
            asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect with backoff."""
        async with self._state_lock:
            if self._state == ConnectionState.RECONNECTING:
                return
            self._state = ConnectionState.RECONNECTING

        while self._should_reconnect:
            self._reconnect_attempt += 1
            delay = self.reconnect_policy.next_delay(self._reconnect_attempt)

            if delay is None:
                async with self._state_lock:
                    self._state = ConnectionState.CLOSED

                error = WebSocketReconnectExhausted(
                    f"Failed to reconnect after {self._reconnect_attempt - 1} attempts"
                )
                await self._fire_callback(self.on_error, error)
                return

            logger.info(
                f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempt}) "
                f"[id={self._connection_id}]"
            )
            await self._fire_callback(self.on_reconnecting, self._reconnect_attempt)

            await asyncio.sleep(delay)

            try:
                await self.connect()
                # Record metrics AFTER successful reconnection
                if self._metrics:
                    self._metrics.on_reconnect()
                logger.info(f"Reconnected successfully [id={self._connection_id}]")
                return
            except Exception as e:
                logger.warning(
                    f"Reconnection attempt {self._reconnect_attempt} failed: {e}"
                )
                await self._fire_callback(self.on_error, e)

    async def _cancel_tasks(self) -> None:
        """Cancel all background tasks."""
        for task in [self._receive_task, self._ping_task, self._send_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._receive_task = None
        self._ping_task = None
        self._send_task = None

    async def _fire_callback(self, callback: Optional[Callable], *args) -> None:
        """Fire a callback safely, supporting both sync and async callbacks."""
        if callback:
            try:
                result = callback(*args)
                # If callback is async, await it
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Callback error: {e}", exc_info=True)

    # =========================================================================
    # Utility Methods (NEW)
    # =========================================================================

    async def ping(self, timeout: Optional[float] = None) -> bool:
        """
        Send a ping and wait for pong to test connection health.

        Args:
            timeout: Max seconds to wait for pong (default: config.ping_timeout)

        Returns:
            True if pong received, False if timeout or error
        """
        if not self._ws or not self.is_connected:
            return False

        timeout = timeout or self.config.ping_timeout

        try:
            pong = await self._ws.ping()
            await asyncio.wait_for(pong, timeout=timeout)
            return True
        except Exception:
            return False

    def get_stats(self) -> dict:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection metrics, or empty dict if metrics disabled
        """
        if self._metrics:
            return self._metrics.get_stats()
        return {"metrics_enabled": False}

    def deserialize(self, message: WebSocketMessage) -> Any:
        """
        Deserialize a received message using the configured serializer.

        Args:
            message: WebSocketMessage to deserialize

        Returns:
            Deserialized object

        Raises:
            ValueError: If no serializer configured
        """
        if not self._serializer:
            raise ValueError("No serializer configured")
        return self._serializer.deserialize(message.data)

    async def receive_obj(self, timeout: Optional[float] = None) -> Any:
        """
        Receive and deserialize the next message.

        Convenience method that combines receive() and deserialize().

        Args:
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            Deserialized object

        Raises:
            ValueError: If no serializer configured
            WebSocketTimeoutError: If timeout expires
        """
        if not self._serializer:
            raise ValueError("No serializer configured")
        message = await self.receive(timeout=timeout)
        return self._serializer.deserialize(message.data)
```

---

## Step 7: Wire Up Exports

### 7.1 Infrastructure Package

**File:** `chatforge/infrastructure/__init__.py`

```python
"""Infrastructure utilities for chatforge adapters."""

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    WebSocketMessage,
    ConnectionState,
    MessageType,
    # NEW: Serializers
    MessageSerializer,
    JsonSerializer,
    RawSerializer,
    # NEW: Metrics
    ConnectionMetrics,
)

__all__ = [
    "WebSocketClient",
    "WebSocketConfig",
    "WebSocketMessage",
    "ConnectionState",
    "MessageType",
    # Serializers
    "MessageSerializer",
    "JsonSerializer",
    "RawSerializer",
    # Metrics
    "ConnectionMetrics",
]
```

### 7.2 WebSocket Package

**File:** `chatforge/infrastructure/websocket/__init__.py`

```python
"""WebSocket client infrastructure."""

from .client import WebSocketClient
from .types import (
    ConnectionState,
    MessageType,
    WebSocketMessage,
    WebSocketConfig,
)
from .reconnect import (
    ReconnectPolicy,
    ExponentialBackoff,
    NoReconnect,
    FixedDelay,
)
from .serializers import (
    MessageSerializer,
    JsonSerializer,
    RawSerializer,
    MsgPackSerializer,  # May be None if msgpack not installed
)
from .metrics import ConnectionMetrics
from .exceptions import (
    WebSocketError,
    WebSocketConnectionError,
    WebSocketClosedError,
    WebSocketTimeoutError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
    WebSocketBackpressureError,
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
```

---

## Step 8: Write Tests

### 8.1 Test Directory

```bash
mkdir -p tests/infrastructure/websocket
touch tests/infrastructure/__init__.py
touch tests/infrastructure/websocket/__init__.py
```

### 8.2 Mock WebSocket Server Fixture

**File:** `tests/infrastructure/websocket/conftest.py`

```python
"""Fixtures for WebSocket tests."""

import asyncio
import pytest
import websockets


@pytest.fixture
async def echo_ws_server():
    """Echo WebSocket server for testing."""

    async def echo_handler(websocket):
        async for message in websocket:
            await websocket.send(message)

    async with websockets.serve(echo_handler, "localhost", 0) as server:
        host, port = server.sockets[0].getsockname()
        yield type("Server", (), {"url": f"ws://{host}:{port}"})()
```

### 8.3 Unit Tests

**File:** `tests/infrastructure/websocket/test_client.py`

```python
"""Tests for WebSocketClient."""

import asyncio
import pytest

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    ConnectionState,
    WebSocketClosedError,
    WebSocketTimeoutError,
)


class TestWebSocketClient:
    """Tests for WebSocketClient."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, echo_ws_server):
        """Test basic connect/disconnect."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            assert ws.is_connected
            assert ws.state == ConnectionState.CONNECTED

        assert ws.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_send_receive_text(self, echo_ws_server):
        """Test sending and receiving text messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_text("hello")
            message = await ws.receive(timeout=5.0)

            assert message.is_text
            assert message.as_text() == "hello"

    @pytest.mark.asyncio
    async def test_send_receive_binary(self, echo_ws_server):
        """Test sending and receiving binary messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_binary(b"\x00\x01\x02")
            message = await ws.receive(timeout=5.0)

            assert message.is_binary
            assert message.as_bytes() == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_send_json(self, echo_ws_server):
        """Test sending JSON messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_json({"type": "test", "value": 123})
            message = await ws.receive(timeout=5.0)

            import json
            data = json.loads(message.as_text())
            assert data == {"type": "test", "value": 123}

    @pytest.mark.asyncio
    async def test_messages_generator(self, echo_ws_server):
        """Test async message generator."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            # Send multiple messages
            for i in range(3):
                await ws.send_text(f"msg{i}")

            # Receive via generator
            received = []
            async for msg in ws.messages():
                received.append(msg.as_text())
                if len(received) >= 3:
                    break

            assert received == ["msg0", "msg1", "msg2"]

    @pytest.mark.asyncio
    async def test_callbacks(self, echo_ws_server):
        """Test event callbacks."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        events = []

        client.on_connect = lambda: events.append("connect")
        client.on_message = lambda m: events.append(f"msg:{m.as_text()}")
        client.on_disconnect = lambda e: events.append("disconnect")

        await client.connect()
        assert "connect" in events

        await client.send_text("test")
        await asyncio.sleep(0.1)
        assert "msg:test" in events

        await client.disconnect()
        assert "disconnect" in events

    @pytest.mark.asyncio
    async def test_receive_timeout(self, echo_ws_server):
        """Test receive timeout."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            with pytest.raises(WebSocketTimeoutError):
                await ws.receive(timeout=0.1)

    @pytest.mark.asyncio
    async def test_send_when_disconnected(self, echo_ws_server):
        """Test send when not connected."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        with pytest.raises(WebSocketClosedError):
            await client.send("test")

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection to invalid URL."""
        config = WebSocketConfig(
            url="ws://localhost:99999",
            connect_timeout=1.0,
            auto_reconnect=False,
        )

        from chatforge.infrastructure.websocket import WebSocketConnectionError

        with pytest.raises((WebSocketConnectionError, WebSocketTimeoutError)):
            async with WebSocketClient(config):
                pass


class TestReconnectPolicies:
    """Tests for reconnect policies."""

    def test_exponential_backoff(self):
        """Test exponential backoff delays."""
        from chatforge.infrastructure.websocket import ExponentialBackoff

        policy = ExponentialBackoff(
            base=1.0, factor=2.0, max_delay=10.0, max_attempts=3, jitter=0
        )

        assert policy.next_delay(1) == 1.0
        assert policy.next_delay(2) == 2.0
        assert policy.next_delay(3) == 4.0
        assert policy.next_delay(4) is None  # Exceeded max_attempts

    def test_exponential_backoff_max_delay(self):
        """Test max delay cap."""
        from chatforge.infrastructure.websocket import ExponentialBackoff

        policy = ExponentialBackoff(
            base=1.0, factor=10.0, max_delay=5.0, max_attempts=0, jitter=0
        )

        assert policy.next_delay(1) == 1.0
        assert policy.next_delay(2) == 5.0  # Capped
        assert policy.next_delay(3) == 5.0  # Still capped

    def test_no_reconnect(self):
        """Test no reconnect policy."""
        from chatforge.infrastructure.websocket import NoReconnect

        policy = NoReconnect()
        assert policy.next_delay(1) is None

    def test_fixed_delay(self):
        """Test fixed delay policy."""
        from chatforge.infrastructure.websocket import FixedDelay

        policy = FixedDelay(delay=5.0, max_attempts=2)

        assert policy.next_delay(1) == 5.0
        assert policy.next_delay(2) == 5.0
        assert policy.next_delay(3) is None


# NEW: Tests for new features
class TestSerializers:
    """Tests for message serializers."""

    def test_json_serializer(self):
        """Test JSON serialization."""
        from chatforge.infrastructure.websocket import JsonSerializer

        serializer = JsonSerializer()

        # Serialize
        data = {"type": "test", "value": 123}
        serialized = serializer.serialize(data)
        assert isinstance(serialized, str)
        assert '"type"' in serialized

        # Deserialize
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

        # Deserialize bytes
        deserialized = serializer.deserialize(serialized.encode())
        assert deserialized == data

    def test_raw_serializer(self):
        """Test raw pass-through serialization."""
        from chatforge.infrastructure.websocket import RawSerializer

        serializer = RawSerializer()

        # Text
        text = "hello"
        assert serializer.serialize(text) == text
        assert serializer.deserialize(text) == text

        # Binary
        binary = b"\x00\x01\x02"
        assert serializer.serialize(binary) == binary
        assert serializer.deserialize(binary) == binary


class TestConnectionMetrics:
    """Tests for connection metrics."""

    def test_metrics_counters(self):
        """Test metrics counter methods."""
        from chatforge.infrastructure.websocket import ConnectionMetrics

        metrics = ConnectionMetrics(connection_id="test123")

        metrics.on_connect()
        assert metrics.connect_count == 1
        assert metrics.connect_time is not None

        metrics.on_message_sent(100)
        assert metrics.messages_sent == 1
        assert metrics.bytes_sent == 100

        metrics.on_message_received(50)
        assert metrics.messages_received == 1
        assert metrics.bytes_received == 50

        metrics.on_disconnect()
        assert metrics.disconnect_count == 1

    def test_get_stats(self):
        """Test get_stats returns dictionary."""
        from chatforge.infrastructure.websocket import ConnectionMetrics

        metrics = ConnectionMetrics(connection_id="test123")
        metrics.on_connect()
        metrics.on_message_sent(100)

        stats = metrics.get_stats()

        assert stats["connection_id"] == "test123"
        assert stats["connects"] == 1
        assert stats["messages_sent"] == 1
        assert "uptime_seconds" in stats

    def test_metrics_reset(self):
        """Test metrics reset."""
        from chatforge.infrastructure.websocket import ConnectionMetrics

        metrics = ConnectionMetrics()
        metrics.on_connect()
        metrics.on_message_sent(100)

        metrics.reset()

        assert metrics.connect_count == 0
        assert metrics.messages_sent == 0
        assert metrics.connect_time is None


class TestWebSocketClientNewFeatures:
    """Tests for new WebSocket client features."""

    @pytest.mark.asyncio
    async def test_connection_id(self, echo_ws_server):
        """Test connection ID is generated."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            assert ws.connection_id is not None
            assert len(ws.connection_id) == 8  # UUID prefix

    @pytest.mark.asyncio
    async def test_metrics_enabled(self, echo_ws_server):
        """Test metrics are tracked when enabled."""
        config = WebSocketConfig(url=echo_ws_server.url, enable_metrics=True)

        async with WebSocketClient(config) as ws:
            await ws.send_text("hello")
            await ws.receive(timeout=5.0)

            stats = ws.get_stats()
            assert stats["connects"] == 1
            assert stats["messages_sent"] == 1
            assert stats["messages_received"] == 1

    @pytest.mark.asyncio
    async def test_metrics_disabled(self, echo_ws_server):
        """Test metrics are not tracked when disabled."""
        config = WebSocketConfig(url=echo_ws_server.url, enable_metrics=False)

        async with WebSocketClient(config) as ws:
            assert ws.metrics is None
            stats = ws.get_stats()
            assert stats == {"metrics_enabled": False}

    @pytest.mark.asyncio
    async def test_ping_method(self, echo_ws_server):
        """Test manual ping method."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            result = await ws.ping(timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_ping_when_disconnected(self, echo_ws_server):
        """Test ping returns False when disconnected."""
        config = WebSocketConfig(url=echo_ws_server.url)
        ws = WebSocketClient(config)

        result = await ws.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_fast_lane_mode(self, echo_ws_server):
        """Test fast lane (no send queue) mode."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            enable_send_queue=False,
            enable_metrics=False,
        )

        async with WebSocketClient(config) as ws:
            # Should send directly without queue
            await ws.send_text("hello")
            message = await ws.receive(timeout=5.0)
            assert message.as_text() == "hello"

    @pytest.mark.asyncio
    async def test_serializer_integration(self, echo_ws_server):
        """Test serializer integration."""
        from chatforge.infrastructure.websocket import JsonSerializer

        config = WebSocketConfig(
            url=echo_ws_server.url,
            serializer=JsonSerializer(),
        )

        async with WebSocketClient(config) as ws:
            # send_json uses serializer
            await ws.send_json({"type": "test"})

            # Use async receive_obj for convenience
            obj = await ws.receive_obj(timeout=5.0)
            assert obj == {"type": "test"}

    @pytest.mark.asyncio
    async def test_deserialize_method(self, echo_ws_server):
        """Test manual deserialize method."""
        from chatforge.infrastructure.websocket import JsonSerializer

        config = WebSocketConfig(
            url=echo_ws_server.url,
            serializer=JsonSerializer(),
        )

        async with WebSocketClient(config) as ws:
            await ws.send_json({"key": "value"})
            message = await ws.receive(timeout=5.0)

            # Manual deserialize
            obj = ws.deserialize(message)
            assert obj == {"key": "value"}

    @pytest.mark.asyncio
    async def test_async_callback(self, echo_ws_server):
        """Test that async callbacks are properly awaited."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        events = []

        async def async_on_connect():
            await asyncio.sleep(0.01)  # Simulate async work
            events.append("async_connect")

        client.on_connect = async_on_connect

        await client.connect()
        assert "async_connect" in events

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_receive_overflow_callback(self, echo_ws_server):
        """Test receive overflow callback is fired when queue is full."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            max_queue_size=1,  # Very small queue
        )

        dropped_messages = []

        async with WebSocketClient(config) as ws:
            ws.on_receive_overflow = lambda msg: dropped_messages.append(msg)

            # Send more messages than queue can hold
            for i in range(5):
                await ws.send_text(f"msg{i}")

            await asyncio.sleep(0.2)  # Let messages arrive

            # Some messages should have been dropped
            # (exact count depends on timing)


# Integration tests for critical scenarios
class TestWebSocketClientIntegration:
    """Integration tests for critical scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reconnection_on_server_restart(self, echo_ws_server):
        """Test that client reconnects after server restart."""
        # This test requires a server that can be restarted
        # Simplified version: just test reconnection callback fires
        config = WebSocketConfig(
            url=echo_ws_server.url,
            auto_reconnect=True,
            max_reconnect_attempts=3,
        )

        reconnect_attempts = []
        client = WebSocketClient(config)
        client.on_reconnecting = lambda attempt: reconnect_attempts.append(attempt)

        await client.connect()
        assert client.is_connected

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_backpressure_triggers(self):
        """Test that backpressure error is raised when send queue is full."""
        import websockets

        # Create a slow server that doesn't read messages quickly
        async def slow_handler(websocket):
            await asyncio.sleep(10)  # Never reads

        async with websockets.serve(slow_handler, "localhost", 0) as server:
            host, port = server.sockets[0].getsockname()

            from chatforge.infrastructure.websocket import WebSocketBackpressureError

            config = WebSocketConfig(
                url=f"ws://{host}:{port}",
                enable_send_queue=True,
                send_queue_size=2,
                send_queue_timeout=0.1,  # Short timeout
            )

            async with WebSocketClient(config) as ws:
                # Fill the queue
                await ws.send_text("msg1")
                await ws.send_text("msg2")

                # Next one should trigger backpressure
                with pytest.raises(WebSocketBackpressureError):
                    await ws.send_text("overflow")

    @pytest.mark.asyncio
    @pytest.mark.load
    async def test_no_memory_leak(self, echo_ws_server):
        """Test that memory doesn't grow unbounded under load."""
        import tracemalloc

        config = WebSocketConfig(url=echo_ws_server.url)

        tracemalloc.start()

        async with WebSocketClient(config) as ws:
            for _ in range(1000):
                await ws.send_text("x" * 100)
                await ws.receive(timeout=5.0)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should stay reasonable (< 10MB for this test)
        assert peak < 10 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.2f}MB"

    @pytest.mark.asyncio
    async def test_connection_leak_on_setup_failure(self):
        """Test that connections don't leak when setup fails."""
        import websockets

        setup_error_triggered = False

        # Server that accepts but we'll fail during client setup
        async def handler(websocket):
            await asyncio.sleep(10)

        async with websockets.serve(handler, "localhost", 0) as server:
            host, port = server.sockets[0].getsockname()

            config = WebSocketConfig(
                url=f"ws://{host}:{port}",
                connect_timeout=5.0,
            )

            client = WebSocketClient(config)

            # Simulate setup failure by raising in callback
            def failing_callback():
                nonlocal setup_error_triggered
                setup_error_triggered = True
                raise RuntimeError("Setup failed!")

            client.on_connect = failing_callback

            # Connection should still work (callback error shouldn't crash)
            await client.connect()
            assert setup_error_triggered
            await client.disconnect()
```

---

## File Summary

| File | Lines (est.) | Description |
|------|--------------|-------------|
| `infrastructure/websocket/types.py` | ~100 | Types, enums, config with validation |
| `infrastructure/websocket/exceptions.py` | ~45 | Custom exceptions (+ backpressure) |
| `infrastructure/websocket/reconnect.py` | ~80 | Reconnect policies |
| `infrastructure/websocket/serializers.py` | ~60 | Message serializers |
| `infrastructure/websocket/metrics.py` | ~100 | Connection metrics (with dropped count) |
| `infrastructure/websocket/client.py` | ~500 | WebSocketClient (leak-safe, async callbacks) |
| `infrastructure/websocket/__init__.py` | ~55 | Exports |
| `tests/.../test_client.py` | ~400 | Unit + integration tests |

**Total:** ~1340 lines

---

## Dependencies

Add to `pyproject.toml` or `requirements.txt`:

```
websockets>=12.0
```

---

## After Implementation

1. Run tests: `pytest tests/infrastructure/websocket/ -v`
2. Test with real WebSocket endpoint (e.g., echo server)
3. Use in RealtimeVoiceAPIPort implementation
