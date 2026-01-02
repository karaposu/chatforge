# WebSocket Infrastructure: Detailed Design

**Date:** 2025-01-01
**Status:** Design
**Priority:** High (blocks RealtimeVoiceAPIPort, WebRTCAudioAdapter)

---

## Overview

A reusable WebSocket client infrastructure for chatforge adapters. This is **not a port** - it's internal infrastructure that adapters use to communicate over WebSockets.

```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Logic                            │
│                   (VoiceAgent, etc.)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Ports                                │
│         (RealtimeVoiceAPIPort, AudioStreamPort)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Adapters                              │
│    (OpenAIRealtimeAdapter, WebRTCAudioAdapter, etc.)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              WebSocket Infrastructure                        │
│                    (This module)                             │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ WebSocketClient │  │ ReconnectPolicy │  │ MessageQueue │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    [ websockets library ]
```

---

## Use Cases

| Adapter | WebSocket Usage |
|---------|-----------------|
| OpenAIRealtimeAdapter | Bidirectional audio + events with OpenAI |
| WebRTCAudioAdapter | Audio relay to/from browser |
| TwilioAudioAdapter | Twilio Media Streams |
| Future: LiveUpdatesAdapter | Real-time notifications |

### Common Requirements

1. **Connection Management** - Connect, disconnect, reconnect
2. **Message Handling** - Send/receive binary and text
3. **Error Recovery** - Auto-reconnect with backoff
4. **Lifecycle Events** - Callbacks for connect/disconnect/error
5. **Async-First** - Full asyncio support
6. **Heartbeat** - Keep connections alive
7. **Graceful Shutdown** - Clean disconnection

---

## File Structure

```
chatforge/
├── infrastructure/
│   ├── __init__.py
│   └── websocket/
│       ├── __init__.py
│       ├── client.py         # WebSocketClient
│       ├── reconnect.py      # ReconnectPolicy, backoff strategies
│       ├── types.py          # Message types, connection states
│       └── exceptions.py     # WebSocket-specific exceptions
```

---

## API Design

### Types and Enums

```python
# chatforge/infrastructure/websocket/types.py

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union

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

    # Timeouts
    connect_timeout: float = 10.0
    close_timeout: float = 5.0
    ping_interval: float = 20.0  # Seconds between pings
    ping_timeout: float = 10.0   # Seconds to wait for pong

    # Reconnection
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5  # 0 = infinite
    reconnect_backoff_base: float = 1.0
    reconnect_backoff_max: float = 60.0
    reconnect_backoff_factor: float = 2.0

    # Buffer sizes
    max_message_size: int = 10 * 1024 * 1024  # 10MB
    max_queue_size: int = 1000
```

### Exceptions

```python
# chatforge/infrastructure/websocket/exceptions.py

class WebSocketError(Exception):
    """Base exception for WebSocket errors."""
    pass

class WebSocketConnectionError(WebSocketError):
    """Failed to establish connection."""
    pass

class WebSocketClosedError(WebSocketError):
    """Connection was closed unexpectedly."""
    def __init__(self, message: str, code: int = None, reason: str = None):
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
```

### Reconnect Policy

```python
# chatforge/infrastructure/websocket/reconnect.py

from abc import ABC, abstractmethod
import asyncio
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
    """Exponential backoff with jitter."""

    def __init__(
        self,
        base: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 60.0,
        max_attempts: int = 5,  # 0 = infinite
        jitter: float = 0.1,   # ±10% randomization
    ):
        self.base = base
        self.factor = factor
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.jitter = jitter
        self._attempt = 0

    def next_delay(self, attempt: int) -> float | None:
        if self.max_attempts > 0 and attempt > self.max_attempts:
            return None

        delay = min(self.base * (self.factor ** (attempt - 1)), self.max_delay)

        # Add jitter
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def reset(self) -> None:
        self._attempt = 0

class NoReconnect(ReconnectPolicy):
    """Never reconnect."""

    def next_delay(self, attempt: int) -> float | None:
        return None

    def reset(self) -> None:
        pass

class ImmediateReconnect(ReconnectPolicy):
    """Reconnect immediately, limited attempts."""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def next_delay(self, attempt: int) -> float | None:
        if attempt > self.max_attempts:
            return None
        return 0.0

    def reset(self) -> None:
        pass
```

### WebSocket Client

```python
# chatforge/infrastructure/websocket/client.py

import asyncio
import logging
from typing import AsyncGenerator, Callable, Optional, Union
from contextlib import asynccontextmanager

import websockets
from websockets.client import WebSocketClientProtocol

from .types import ConnectionState, WebSocketConfig, WebSocketMessage, MessageType
from .exceptions import (
    WebSocketError,
    WebSocketConnectionError,
    WebSocketClosedError,
    WebSocketTimeoutError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
)
from .reconnect import ReconnectPolicy, ExponentialBackoff

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
    - Thread-safe message queue

    Usage:
        config = WebSocketConfig(url="wss://api.example.com/ws")

        async with WebSocketClient(config) as ws:
            await ws.send("hello")

            async for message in ws.messages():
                print(f"Received: {message.data}")

    Or with callbacks:
        client = WebSocketClient(config)
        client.on_message = lambda msg: print(msg.data)
        client.on_connect = lambda: print("Connected!")

        await client.connect()
        # ... do work ...
        await client.disconnect()
    """

    def __init__(
        self,
        config: WebSocketConfig,
        reconnect_policy: ReconnectPolicy = None,
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

        # Message handling
        self._receive_queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

        # Reconnection
        self._reconnect_attempt = 0
        self._should_reconnect = True
        self._reconnect_task: Optional[asyncio.Task] = None

        # Event callbacks (optional)
        self.on_connect: Optional[Callable[[], None]] = None
        self.on_disconnect: Optional[Callable[[Optional[Exception]], None]] = None
        self.on_message: Optional[Callable[[WebSocketMessage], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_reconnecting: Optional[Callable[[int], None]] = None  # attempt number

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

        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    self.config.url,
                    extra_headers=self.config.headers,
                    subprotocols=self.config.subprotocols,
                    max_size=self.config.max_message_size,
                    ping_interval=None,  # We handle ping ourselves
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

            # Fire callback
            if self.on_connect:
                try:
                    self.on_connect()
                except Exception as e:
                    logger.warning(f"on_connect callback error: {e}")

            logger.info(f"WebSocket connected to {self.config.url}")

        except asyncio.TimeoutError as e:
            async with self._state_lock:
                self._state = ConnectionState.DISCONNECTED
            raise WebSocketTimeoutError(
                f"Connection to {self.config.url} timed out"
            ) from e
        except Exception as e:
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

        # Cancel background tasks
        await self._cancel_tasks()

        # Close WebSocket
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

        # Fire callback
        if self.on_disconnect:
            try:
                self.on_disconnect(None)
            except Exception as e:
                logger.warning(f"on_disconnect callback error: {e}")

        logger.info(f"WebSocket disconnected from {self.config.url}")

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

        Args:
            data: Text string or binary bytes to send

        Raises:
            WebSocketSendError: If send fails
            WebSocketClosedError: If connection is closed
        """
        if not self._ws or not self.is_connected:
            raise WebSocketClosedError("Cannot send: not connected")

        try:
            await self._ws.send(data)
        except websockets.ConnectionClosed as e:
            raise WebSocketClosedError(
                f"Connection closed during send",
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
        """Send a JSON message."""
        import json
        await self.send(json.dumps(obj))

    # =========================================================================
    # Receiving
    # =========================================================================

    async def receive(self, timeout: float = None) -> WebSocketMessage:
        """
        Receive next message from queue.

        Args:
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            WebSocketMessage with data and type

        Raises:
            WebSocketTimeoutError: If timeout expires
            WebSocketClosedError: If connection closes while waiting
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

        Usage:
            async for msg in ws.messages():
                process(msg)

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

                # Fire callback
                if self.on_message:
                    try:
                        self.on_message(ws_msg)
                    except Exception as e:
                        logger.warning(f"on_message callback error: {e}")

                # Queue message
                try:
                    self._receive_queue.put_nowait(ws_msg)
                except asyncio.QueueFull:
                    logger.warning("Receive queue full, dropping message")

        except websockets.ConnectionClosed as e:
            logger.info(f"WebSocket closed: code={e.code} reason={e.reason}")
            await self._handle_disconnect(
                WebSocketClosedError("Connection closed", e.code, e.reason)
            )
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            await self._handle_disconnect(e)

    async def _ping_loop(self) -> None:
        """Background task that sends periodic pings."""
        while self.is_connected:
            try:
                await asyncio.sleep(self.config.ping_interval)
                if self._ws and self.is_connected:
                    pong = await self._ws.ping()
                    await asyncio.wait_for(pong, timeout=self.config.ping_timeout)
            except asyncio.TimeoutError:
                logger.warning("Ping timeout, connection may be dead")
                await self._handle_disconnect(
                    WebSocketTimeoutError("Ping timeout")
                )
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Ping error: {e}")

    async def _handle_disconnect(self, error: Exception) -> None:
        """Handle unexpected disconnection."""
        async with self._state_lock:
            if self._state in (ConnectionState.CLOSING, ConnectionState.CLOSED):
                return
            self._state = ConnectionState.DISCONNECTED

        # Fire callback
        if self.on_disconnect:
            try:
                self.on_disconnect(error)
            except Exception as e:
                logger.warning(f"on_disconnect callback error: {e}")

        # Attempt reconnection
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
                # Exhausted retries
                async with self._state_lock:
                    self._state = ConnectionState.CLOSED

                error = WebSocketReconnectExhausted(
                    f"Failed to reconnect after {self._reconnect_attempt - 1} attempts"
                )
                if self.on_error:
                    self.on_error(error)
                return

            logger.info(
                f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempt})"
            )

            if self.on_reconnecting:
                try:
                    self.on_reconnecting(self._reconnect_attempt)
                except Exception as e:
                    logger.warning(f"on_reconnecting callback error: {e}")

            await asyncio.sleep(delay)

            try:
                await self.connect()
                logger.info("Reconnected successfully")
                return
            except Exception as e:
                logger.warning(f"Reconnection attempt {self._reconnect_attempt} failed: {e}")
                if self.on_error:
                    try:
                        self.on_error(e)
                    except Exception as err:
                        logger.warning(f"on_error callback error: {err}")

    async def _cancel_tasks(self) -> None:
        """Cancel all background tasks."""
        tasks = [self._receive_task, self._ping_task, self._reconnect_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._receive_task = None
        self._ping_task = None
        self._reconnect_task = None
```

---

## Package Init

```python
# chatforge/infrastructure/__init__.py
"""Infrastructure utilities for chatforge adapters."""

# chatforge/infrastructure/websocket/__init__.py
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
    ImmediateReconnect,
)
from .exceptions import (
    WebSocketError,
    WebSocketConnectionError,
    WebSocketClosedError,
    WebSocketTimeoutError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
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
    "ImmediateReconnect",
    # Exceptions
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketClosedError",
    "WebSocketTimeoutError",
    "WebSocketReconnectExhausted",
    "WebSocketSendError",
]
```

---

## Usage Examples

### Basic Usage

```python
from chatforge.infrastructure.websocket import WebSocketClient, WebSocketConfig

async def main():
    config = WebSocketConfig(
        url="wss://api.openai.com/v1/realtime",
        headers={"Authorization": "Bearer sk-..."},
    )

    async with WebSocketClient(config) as ws:
        await ws.send_json({"type": "session.create"})

        async for message in ws.messages():
            print(f"Received: {message.data}")
            if should_stop:
                break
```

### With Callbacks

```python
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    WebSocketMessage,
)

async def main():
    config = WebSocketConfig(url="wss://example.com/ws")
    client = WebSocketClient(config)

    # Set up callbacks
    client.on_connect = lambda: print("Connected!")
    client.on_disconnect = lambda e: print(f"Disconnected: {e}")
    client.on_message = lambda m: handle_message(m)
    client.on_error = lambda e: print(f"Error: {e}")
    client.on_reconnecting = lambda n: print(f"Reconnecting (attempt {n})...")

    await client.connect()

    try:
        # Keep running until interrupted
        while client.is_connected:
            await asyncio.sleep(1)
    finally:
        await client.disconnect()
```

### Custom Reconnect Policy

```python
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    ReconnectPolicy,
)

class CustomReconnect(ReconnectPolicy):
    """Reconnect with fixed delay, max 10 attempts."""

    def next_delay(self, attempt: int) -> float | None:
        if attempt > 10:
            return None
        return 5.0  # Always wait 5 seconds

    def reset(self) -> None:
        pass

config = WebSocketConfig(url="wss://example.com/ws", auto_reconnect=True)
client = WebSocketClient(config, reconnect_policy=CustomReconnect())
```

### Binary Audio Streaming

```python
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    MessageType,
)

async def stream_audio(ws: WebSocketClient, audio_chunks):
    """Stream audio chunks over WebSocket."""
    for chunk in audio_chunks:
        await ws.send_binary(chunk)

async def receive_audio(ws: WebSocketClient):
    """Receive audio chunks from WebSocket."""
    async for message in ws.messages():
        if message.is_binary:
            yield message.as_bytes()
        else:
            # Handle text messages (events, etc.)
            handle_event(message.as_text())
```

---

## Integration with Adapters

### OpenAI Realtime Adapter

```python
# chatforge/adapters/realtime/openai.py

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    WebSocketMessage,
)
from chatforge.ports.realtime import RealtimeVoiceAPIPort

class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """OpenAI Realtime API adapter using WebSocket infrastructure."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._ws: WebSocketClient | None = None

    async def __aenter__(self):
        config = WebSocketConfig(
            url="wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "OpenAI-Beta": "realtime=v1",
            },
            ping_interval=30.0,
            auto_reconnect=False,  # Handle reconnect at higher level
        )

        self._ws = WebSocketClient(config)
        self._ws.on_message = self._handle_message

        await self._ws.connect()
        return self

    async def __aexit__(self, *args):
        if self._ws:
            await self._ws.disconnect()

    async def send_audio(self, chunk: bytes) -> None:
        # Encode as base64 and send as JSON event
        import base64
        await self._ws.send_json({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(chunk).decode(),
        })

    def _handle_message(self, message: WebSocketMessage) -> None:
        import json
        event = json.loads(message.as_text())
        # Process event...
```

### WebRTC Audio Relay

```python
# chatforge/adapters/audio/webrtc.py

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
)
from chatforge.ports.audio_stream import AudioStreamPort

class WebRTCAudioAdapter(AudioStreamPort):
    """Audio streaming via WebSocket relay to browser."""

    def __init__(self, relay_url: str):
        self._relay_url = relay_url
        self._ws: WebSocketClient | None = None

    async def __aenter__(self):
        config = WebSocketConfig(
            url=self._relay_url,
            auto_reconnect=True,
            max_reconnect_attempts=10,
        )

        self._ws = WebSocketClient(config)
        await self._ws.connect()
        return self

    async def play(self, chunk: bytes) -> None:
        """Send audio to browser via WebSocket."""
        await self._ws.send_binary(chunk)

    async def start_capture(self):
        """Receive audio from browser via WebSocket."""
        async for message in self._ws.messages():
            if message.is_binary:
                yield message.as_bytes()
```

---

## Testing

```python
# tests/infrastructure/websocket/test_client.py

import pytest
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    ConnectionState,
)

class TestWebSocketClient:

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, echo_ws_server):
        """Test basic connect/disconnect."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            assert ws.is_connected
            assert ws.state == ConnectionState.CONNECTED

        assert ws.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_send_receive(self, echo_ws_server):
        """Test sending and receiving messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send("hello")
            message = await ws.receive(timeout=5.0)
            assert message.as_text() == "hello"

    @pytest.mark.asyncio
    async def test_callbacks(self, echo_ws_server):
        """Test event callbacks."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        connected = False
        messages = []

        client.on_connect = lambda: nonlocal_set('connected', True)
        client.on_message = lambda m: messages.append(m)

        await client.connect()
        assert connected

        await client.send("test")
        await asyncio.sleep(0.1)
        assert len(messages) == 1

        await client.disconnect()
```

---

## Dependencies

```
# requirements.txt (or pyproject.toml)
websockets>=12.0
```

---

## Implementation Checklist

- [ ] Create `chatforge/infrastructure/` package
- [ ] Create `chatforge/infrastructure/websocket/` package
- [ ] Implement `types.py` - ConnectionState, WebSocketMessage, WebSocketConfig
- [ ] Implement `exceptions.py` - Custom exceptions
- [ ] Implement `reconnect.py` - ReconnectPolicy, ExponentialBackoff
- [ ] Implement `client.py` - WebSocketClient
- [ ] Write unit tests with mock WebSocket server
- [ ] Integration test with real WebSocket endpoint
- [ ] Update exports in `__init__.py`

---

## Design Decisions

### Why Not a Port?

Ports define boundaries for domain logic. WebSocket is a transport mechanism - the domain doesn't care whether we use WebSocket, HTTP, or carrier pigeons. Only adapters care.

### Why Separate from Adapters?

Multiple adapters need WebSocket functionality. Duplicating would violate DRY. Infrastructure code is shared utility code that adapters use.

### Why Custom Client vs Using `websockets` Directly?

- Consistent reconnection behavior across adapters
- Unified error handling
- Callback-based and async generator APIs
- Configured defaults for chatforge use cases

### Why Callbacks AND Async Generators?

Different use cases benefit from different patterns:
- **Callbacks**: Fire-and-forget event handling
- **Async generators**: Pull-based processing with backpressure

---

## Future Enhancements

1. **Connection pooling** - Multiple WebSocket connections managed together
2. **Rate limiting** - Throttle outgoing messages
3. **Compression** - Per-message deflate support
4. **Metrics** - Connection stats, message counts
5. **Circuit breaker** - Stop reconnecting after persistent failures
