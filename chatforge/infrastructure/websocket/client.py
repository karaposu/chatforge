"""Async WebSocket client with automatic reconnection."""

import asyncio
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Callable, Optional, Union

import websockets
from websockets.client import WebSocketClientProtocol

from .exceptions import (
    WebSocketBackpressureError,
    WebSocketClosedError,
    WebSocketConnectionError,
    WebSocketReconnectExhausted,
    WebSocketSendError,
    WebSocketTimeoutError,
)
from .metrics import ConnectionMetrics
from .reconnect import ExponentialBackoff, ReconnectPolicy
from .serializers import MessageSerializer
from .types import ConnectionState, MessageType, WebSocketConfig, WebSocketMessage

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
    - Send queue with background worker
    - Backpressure handling
    - Connection metrics
    - Pluggable serializers
    - Connection ID for logging
    - Manual ping() method

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

        # Connection ID for logging/debugging
        self._connection_id: str = str(uuid.uuid4())[:8]

        # Message handling
        self._receive_queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

        # Send queue (if enabled)
        self._send_queue: Optional[asyncio.Queue] = None
        self._send_task: Optional[asyncio.Task] = None
        if config.enable_send_queue:
            self._send_queue = asyncio.Queue(maxsize=config.send_queue_size)

        # Metrics (if enabled)
        self._metrics: Optional[ConnectionMetrics] = None
        if config.enable_metrics:
            self._metrics = ConnectionMetrics(connection_id=self._connection_id)

        # Serializer
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
        self.on_receive_overflow: Optional[Callable[[WebSocketMessage], None]] = None

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
            # Build connection kwargs, only including non-empty optional params
            connect_kwargs = {
                "max_size": self.config.max_message_size,
                "ping_interval": None,
                "ping_timeout": None,
            }

            if self.config.headers:
                connect_kwargs["additional_headers"] = self.config.headers
            if self.config.subprotocols:
                connect_kwargs["subprotocols"] = self.config.subprotocols
            if self.config.compression:
                connect_kwargs["compression"] = self.config.compression

            ws = await asyncio.wait_for(
                websockets.connect(self.config.url, **connect_kwargs),
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

        # Use send queue if enabled
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
            raise ValueError(
                "No serializer configured - use send_json() or set serializer"
            )
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
                        f"Receive queue full, dropping message "
                        f"[id={self._connection_id}]"
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
                    logger.info(
                        f"Send worker stopping: connection closed "
                        f"[id={self._connection_id}]"
                    )
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
    # Utility Methods
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
