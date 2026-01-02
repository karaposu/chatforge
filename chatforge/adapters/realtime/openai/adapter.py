"""OpenAI Realtime API adapter using shared WebSocket infrastructure."""

import asyncio
import json
import logging
from typing import AsyncGenerator

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    JsonSerializer,
    ExponentialBackoff,
    WebSocketConnectionError,
    WebSocketClosedError,
    WebSocketBackpressureError,
)
from chatforge.ports.realtime_voice import (
    RealtimeVoiceAPIPort,
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    ProviderCapabilities,
    RealtimeConnectionError,
    RealtimeAuthenticationError,
    RealtimeSessionError,
    RealtimeRateLimitError,
)

from . import messages
from .translator import translate_event


logger = logging.getLogger(__name__)


# OpenAI Realtime API constants
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
DEFAULT_MODEL = "gpt-4o-realtime-preview-2025-06-03"

# Sentinel value for stopping the event generator
_STOP_SENTINEL = object()

# Event queue size limit to prevent unbounded memory growth
_EVENT_QUEUE_MAX_SIZE = 1000


class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    OpenAI Realtime API adapter.

    Uses shared WebSocket infrastructure for:
    - Automatic reconnection with exponential backoff
    - Ping/pong heartbeat
    - Send queue with backpressure handling
    - Connection metrics

    Thread Safety:
        This adapter is thread-safe. All public methods can be called
        concurrently from different coroutines.

    Example:
        async with OpenAIRealtimeAdapter(api_key=key) as realtime:
            await realtime.connect(VoiceSessionConfig(voice="alloy"))

            async for event in realtime.events():
                if event.type == VoiceEventType.AUDIO_CHUNK:
                    await audio.play(event.data)
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        *,
        connect_timeout: float = 30.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        enable_metrics: bool = True,
    ):
        """
        Initialize OpenAI Realtime adapter.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-realtime-preview)
            connect_timeout: Connection timeout in seconds
            auto_reconnect: Whether to auto-reconnect on disconnect
            max_reconnect_attempts: Max reconnect attempts
            enable_metrics: Whether to track connection metrics
        """
        self._api_key = api_key
        self._model = model
        self._connect_timeout = connect_timeout
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._enable_metrics = enable_metrics

        self._ws: WebSocketClient | None = None
        self._config: VoiceSessionConfig | None = None
        self._session_ready = asyncio.Event()
        # Bounded queue to prevent unbounded memory growth
        self._event_queue: asyncio.Queue[VoiceEvent | object] = asyncio.Queue(
            maxsize=_EVENT_QUEUE_MAX_SIZE
        )
        self._receive_task: asyncio.Task | None = None
        # Lock for thread safety on shared state
        self._lock = asyncio.Lock()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def provider_name(self) -> str:
        return "openai"

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "OpenAIRealtimeAdapter":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and cleanup."""
        await self.disconnect()

    async def connect(self, config: VoiceSessionConfig) -> None:
        """Connect to OpenAI Realtime API."""
        async with self._lock:
            if self._ws is not None and self._ws.is_connected:
                raise RealtimeSessionError("Already connected")

            self._config = config
            self._session_ready.clear()

            # Resolve model
            model = self._model if config.model == "default" else config.model

            # Configure WebSocket with OpenAI settings
            ws_config = WebSocketConfig(
                url=f"{OPENAI_REALTIME_URL}?model={model}",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
                serializer=JsonSerializer(),
                connect_timeout=self._connect_timeout,
                auto_reconnect=self._auto_reconnect,
                ping_interval=20.0,
                enable_metrics=self._enable_metrics,
                enable_send_queue=True,
            )

            # Create reconnect policy if auto-reconnect enabled
            reconnect_policy = None
            if self._auto_reconnect:
                reconnect_policy = ExponentialBackoff(
                    base=1.0,
                    factor=2.0,
                    max_delay=30.0,
                    max_attempts=self._max_reconnect_attempts,
                )

            self._ws = WebSocketClient(ws_config, reconnect_policy=reconnect_policy)

            # Wire up callbacks for reconnection handling
            self._ws.on_disconnect = self._on_disconnect
            self._ws.on_connect = self._on_reconnect_success
            self._ws.on_reconnecting = self._on_reconnecting

            try:
                await self._ws.connect()
            except WebSocketConnectionError as e:
                self._ws = None
                # Check for authentication errors
                if "401" in str(e) or "Unauthorized" in str(e):
                    raise RealtimeAuthenticationError("Invalid API key") from e
                raise RealtimeConnectionError(str(e)) from e

            # Start receive loop BEFORE sending session update
            # to avoid race condition where session.created arrives before we listen
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Send session configuration
            try:
                await self._ws.send_json(messages.session_update(config))
            except WebSocketBackpressureError:
                await self.disconnect()
                raise RealtimeConnectionError("Send queue full during setup")

            # Wait for session.created or session.updated
            try:
                await asyncio.wait_for(self._session_ready.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                await self.disconnect()
                raise RealtimeConnectionError("Session initialization timeout")

            # Emit CONNECTED event after successful session setup
            self._queue_event_nowait(VoiceEvent(type=VoiceEventType.CONNECTED))

    async def disconnect(self) -> None:
        """Disconnect from OpenAI."""
        async with self._lock:
            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None

            if self._ws:
                await self._ws.disconnect()
                self._ws = None

            self._config = None
            self._session_ready.clear()

            # Signal event generator to stop
            self._queue_event_nowait(_STOP_SENTINEL)

    def is_connected(self) -> bool:
        """Check if connected (thread-safe)."""
        # Use local reference to avoid race with disconnect()
        ws = self._ws
        return ws is not None and ws.is_connected

    # =========================================================================
    # Audio Streaming
    # =========================================================================

    async def send_audio(self, chunk: bytes) -> None:
        """Send audio chunk to OpenAI."""
        await self._send_message(messages.input_audio_buffer_append(chunk))

    async def commit_audio(self) -> None:
        """Commit audio buffer."""
        await self._send_message(messages.input_audio_buffer_commit())

    async def clear_audio(self) -> None:
        """Clear audio buffer."""
        await self._send_message(messages.input_audio_buffer_clear())

    # =========================================================================
    # Text Input
    # =========================================================================

    async def add_text_item(self, text: str) -> None:
        """
        Add text to conversation without triggering response.

        Use this when you want to send multiple text items before
        triggering a response with create_response().
        """
        await self._send_message(messages.conversation_item_create_message(text))

    async def send_text(self, text: str, *, trigger_response: bool = True) -> None:
        """
        Send text message.

        Args:
            text: Text message content
            trigger_response: If True (default), automatically trigger AI response.
                             Set to False to send multiple texts before responding.
        """
        await self.add_text_item(text)
        if trigger_response:
            await self.create_response()

    # =========================================================================
    # Response Control
    # =========================================================================

    async def create_response(self, instructions: str | None = None) -> None:
        """Trigger AI response."""
        await self._send_message(messages.response_create(instructions))

    async def interrupt(self) -> None:
        """
        Interrupt current response (barge-in).

        This cancels the current AI response. Use for barge-in scenarios
        where the user starts speaking while AI is responding.
        """
        await self._send_message(messages.response_cancel())

    async def cancel_response(self, response_id: str | None = None) -> None:
        """Cancel specific or current response."""
        await self._send_message(messages.response_cancel(response_id))

    # =========================================================================
    # Tool Calling
    # =========================================================================

    async def send_tool_result(
        self,
        call_id: str,
        result: str,
        is_error: bool = False,
    ) -> None:
        """Send tool result back to AI."""
        await self._send_message(
            messages.conversation_item_create_tool_result(call_id, result, is_error)
        )

    # =========================================================================
    # Session Updates
    # =========================================================================

    async def update_session(self, config: VoiceSessionConfig) -> None:
        """Update session configuration."""
        async with self._lock:
            self._ensure_connected()

            # OpenAI doesn't allow updating model or audio formats mid-session
            if self._config:
                if config.model != "default" and config.model != self._config.model:
                    raise RealtimeSessionError("Cannot change model mid-session")
                if config.input_format != self._config.input_format:
                    raise RealtimeSessionError("Cannot change input format mid-session")
                if config.output_format != self._config.output_format:
                    raise RealtimeSessionError("Cannot change output format mid-session")

            await self._ws.send_json(messages.session_update(config))
            self._config = config

    # =========================================================================
    # Event Stream
    # =========================================================================

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """
        Stream normalized events.

        Note: Only one consumer should iterate events(). Multiple consumers
        will compete for events (each event goes to only one consumer).
        """
        while True:
            try:
                event = await self._event_queue.get()
                # Check for stop sentinel
                if event is _STOP_SENTINEL:
                    return
                yield event
            except asyncio.CancelledError:
                return

    # =========================================================================
    # Capabilities
    # =========================================================================

    def get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI capabilities."""
        return ProviderCapabilities(
            provider_name="openai",
            supports_server_vad=True,
            supports_function_calling=True,
            supports_interruption=True,
            supports_transcription=True,
            supports_input_transcription=True,
            available_voices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            available_models=[
                # GA models
                "gpt-realtime",
                "gpt-realtime-2025-08-28",
                # Mini (cost-efficient)
                "gpt-realtime-mini",
                "gpt-realtime-mini-2025-12-15",
                # Preview
                "gpt-4o-realtime-preview",
                "gpt-4o-realtime-preview-2025-06-03",
                "gpt-4o-realtime-preview-2024-12-17",
            ],
        )

    # =========================================================================
    # Metrics
    # =========================================================================

    def get_stats(self) -> dict:
        """Get connection statistics."""
        ws = self._ws
        if ws:
            return ws.get_stats()
        return {}

    # =========================================================================
    # Internal
    # =========================================================================

    def _ensure_connected(self) -> None:
        """Raise if not connected."""
        if not self.is_connected():
            raise RealtimeSessionError("Not connected")

    async def _send_message(self, msg: dict) -> None:
        """Send message with backpressure handling."""
        self._ensure_connected()
        try:
            await self._ws.send_json(msg)
        except WebSocketBackpressureError:
            raise RealtimeRateLimitError("Send queue full - backpressure")

    def _queue_event_nowait(self, event: VoiceEvent | object) -> None:
        """Queue event without blocking, dropping if full."""
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            if event is not _STOP_SENTINEL and isinstance(event, VoiceEvent):
                logger.warning("Event queue full, dropping event: %s", event.type)

    async def _receive_loop(self) -> None:
        """Background task to receive and translate events."""
        try:
            async for msg in self._ws.messages():
                try:
                    raw = json.loads(msg.as_text())
                    event = translate_event(raw)

                    if event:
                        # Handle session ready
                        if event.type in (
                            VoiceEventType.SESSION_CREATED,
                            VoiceEventType.SESSION_UPDATED,
                        ):
                            self._session_ready.set()

                        # Handle errors specially
                        if event.type == VoiceEventType.ERROR:
                            logger.warning(
                                "OpenAI error: %s - %s",
                                event.data.get("code") if event.data else None,
                                event.data.get("message") if event.data else None,
                            )

                        self._queue_event_nowait(event)

                except Exception as e:
                    logger.exception("Error processing message: %s", e)
                    # Emit error event so caller knows something went wrong
                    self._queue_event_nowait(VoiceEvent(
                        type=VoiceEventType.ERROR,
                        data={"code": "message_processing_error", "message": str(e)},
                    ))

        except asyncio.CancelledError:
            pass
        except WebSocketClosedError:
            # Connection closed, emit disconnect event
            self._queue_event_nowait(VoiceEvent(type=VoiceEventType.DISCONNECTED))

    def _on_disconnect(self, error: Exception | None) -> None:
        """Handle WebSocket disconnect callback."""
        self._queue_event_nowait(VoiceEvent(
            type=VoiceEventType.DISCONNECTED,
            data={"error": str(error)} if error else None,
        ))

    def _on_reconnecting(self, attempt: int) -> None:
        """Handle reconnection attempt callback."""
        self._queue_event_nowait(VoiceEvent(
            type=VoiceEventType.RECONNECTING,
            metadata={"attempt": attempt},
        ))

    def _on_reconnect_success(self) -> None:
        """Handle successful reconnection - re-send session config."""
        if self._config:
            # Re-send session configuration after reconnect
            asyncio.create_task(self._resend_session_config())

    async def _resend_session_config(self) -> None:
        """Re-send session config after reconnection."""
        try:
            if self._config and self._ws and self._ws.is_connected:
                await self._ws.send_json(messages.session_update(self._config))
                self._queue_event_nowait(VoiceEvent(
                    type=VoiceEventType.CONNECTED,
                    metadata={"reconnected": True},
                ))
        except Exception as e:
            logger.error("Failed to re-send session config after reconnect: %s", e)
