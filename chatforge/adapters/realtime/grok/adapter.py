# chatforge/adapters/realtime/grok/adapter.py
"""Grok (xAI) Realtime API adapter using shared WebSocket infrastructure."""

import asyncio
import json
import logging
import os
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

# Grok Realtime API constants
GROK_REALTIME_URL = "wss://api.x.ai/v1/realtime"
GROK_EPHEMERAL_TOKEN_URL = "https://api.x.ai/v1/realtime/client_secrets"

# Sentinel value for stopping the event generator
_STOP_SENTINEL = object()

# Event queue size limit
_EVENT_QUEUE_MAX_SIZE = 1000


@RealtimeVoiceAPIPort.register("grok")
class GrokRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    Grok (xAI) Realtime API adapter.

    Uses shared WebSocket infrastructure for:
    - Automatic reconnection with exponential backoff
    - Ping/pong heartbeat
    - Send queue with backpressure handling
    - Connection metrics

    Example:
        async with GrokRealtimeAdapter(api_key=key) as realtime:
            await realtime.connect(VoiceSessionConfig(voice="Ara"))

            async for event in realtime.events():
                if event.type == VoiceEventType.AUDIO_CHUNK:
                    await audio.play(event.data)

    For browser/client-side use, use ephemeral tokens:
        adapter = await GrokRealtimeAdapter.with_ephemeral_token(api_key)
    """

    def __init__(
        self,
        api_key: str | None = None,
        ephemeral_token: str | None = None,
        *,
        connect_timeout: float = 30.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        enable_metrics: bool = True,
    ):
        """
        Initialize Grok Realtime adapter.

        Args:
            api_key: xAI API key (for server-side use)
            ephemeral_token: Ephemeral token (for client-side use)
            connect_timeout: Connection timeout in seconds
            auto_reconnect: Whether to auto-reconnect on disconnect
            max_reconnect_attempts: Max reconnect attempts
            enable_metrics: Whether to track connection metrics
        """
        # Auto-read from env if not provided
        resolved_api_key = api_key or os.getenv("XAI_API_KEY")
        if not resolved_api_key and not ephemeral_token:
            raise ValueError(
                "XAI_API_KEY env var not set and no ephemeral_token provided"
            )

        self._auth_token = ephemeral_token or resolved_api_key
        self._api_key = resolved_api_key  # Keep for ephemeral token refresh
        self._connect_timeout = connect_timeout
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._enable_metrics = enable_metrics

        self._ws: WebSocketClient | None = None
        self._config: VoiceSessionConfig | None = None
        self._session_ready = asyncio.Event()
        self._session_configured = asyncio.Event()  # Wait for session.updated
        self._event_queue: asyncio.Queue[VoiceEvent | object] = asyncio.Queue(
            maxsize=_EVENT_QUEUE_MAX_SIZE
        )
        self._receive_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._conversation_item_ids: list[str] = []

    @classmethod
    async def with_ephemeral_token(
        cls,
        api_key: str,
        expires_seconds: int = 300,
        **kwargs,
    ) -> "GrokRealtimeAdapter":
        """
        Create adapter with ephemeral token (for client-side use).

        Args:
            api_key: xAI API key (only used to generate token, not stored)
            expires_seconds: Token expiration time (default 5 minutes)
            **kwargs: Additional arguments passed to constructor

        Returns:
            GrokRealtimeAdapter configured with ephemeral token
        """
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROK_EPHEMERAL_TOKEN_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"expires_after": {"seconds": expires_seconds}},
            )
            response.raise_for_status()
            data = response.json()

        return cls(ephemeral_token=data["value"], **kwargs)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def provider_name(self) -> str:
        return "grok"

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "GrokRealtimeAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def connect(self, config: VoiceSessionConfig) -> None:
        """Connect to Grok Realtime API."""
        async with self._lock:
            if self._ws is not None and self._ws.is_connected:
                raise RealtimeSessionError("Already connected")

            self._config = config
            self._session_ready.clear()
            self._session_configured.clear()
            self._conversation_item_ids.clear()

            # Configure WebSocket
            ws_config = WebSocketConfig(
                url=GROK_REALTIME_URL,
                headers={
                    "Authorization": f"Bearer {self._auth_token}",
                },
                serializer=JsonSerializer(),
                connect_timeout=self._connect_timeout,
                auto_reconnect=self._auto_reconnect,
                ping_interval=20.0,
                enable_metrics=self._enable_metrics,
                enable_send_queue=True,
            )

            reconnect_policy = None
            if self._auto_reconnect:
                reconnect_policy = ExponentialBackoff(
                    base=1.0,
                    factor=2.0,
                    max_delay=30.0,
                    max_attempts=self._max_reconnect_attempts,
                )

            self._ws = WebSocketClient(ws_config, reconnect_policy=reconnect_policy)
            self._ws.on_disconnect = self._on_disconnect
            self._ws.on_connect = self._on_reconnect_success
            self._ws.on_reconnecting = self._on_reconnecting

            try:
                await self._ws.connect()
            except WebSocketConnectionError as e:
                self._ws = None
                if "401" in str(e) or "Unauthorized" in str(e):
                    raise RealtimeAuthenticationError("Invalid API key") from e
                raise RealtimeConnectionError(str(e)) from e

            # Start receive loop BEFORE sending session update
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Wait for conversation.created (Grok's initial handshake)
            try:
                await asyncio.wait_for(self._session_ready.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.debug("Timeout waiting for conversation.created, proceeding anyway")

            # NOW send session configuration
            try:
                await self._ws.send_json(messages.session_update(config))
            except WebSocketBackpressureError:
                await self.disconnect()
                raise RealtimeConnectionError("Send queue full during setup")

            # Wait for session.updated (confirms our config was applied)
            try:
                await asyncio.wait_for(self._session_configured.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                await self.disconnect()
                raise RealtimeConnectionError("Session configuration timeout")

            self._queue_event_nowait(VoiceEvent(type=VoiceEventType.CONNECTED))

    async def disconnect(self) -> None:
        """Disconnect from Grok."""
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
            self._session_configured.clear()
            self._conversation_item_ids.clear()
            self._queue_event_nowait(_STOP_SENTINEL)

    def is_connected(self) -> bool:
        ws = self._ws
        return ws is not None and ws.is_connected

    # =========================================================================
    # Audio Streaming
    # =========================================================================

    async def send_audio(self, chunk: bytes) -> None:
        await self._send_message(messages.input_audio_buffer_append(chunk))

    async def commit_audio(self) -> None:
        """Commit audio buffer."""
        # Use correct commit message based on VAD mode
        vad_mode = self._config.vad_mode if self._config else "server"
        await self._send_message(messages.input_audio_buffer_commit(vad_mode))

    async def clear_audio(self) -> None:
        await self._send_message(messages.input_audio_buffer_clear())

    # =========================================================================
    # Text Input
    # =========================================================================

    async def add_text_item(self, text: str) -> None:
        await self._send_message(messages.conversation_item_create_message(text))

    async def send_text(self, text: str, *, trigger_response: bool = True) -> None:
        await self.add_text_item(text)
        if trigger_response:
            await self.create_response()

    # =========================================================================
    # Response Control
    # =========================================================================

    async def create_response(self, instructions: str | None = None) -> None:
        """Trigger AI response."""
        # Pass modalities from config
        modalities = self._config.modalities if self._config else ["text", "audio"]
        await self._send_message(messages.response_create(instructions, modalities))

    async def interrupt(self) -> None:
        """
        Interrupt current response.

        WARNING: May not be supported by Grok API.
        """
        logger.warning("interrupt() may not be supported by Grok API")
        await self._send_message(messages.response_cancel())

    async def cancel_response(self, response_id: str | None = None) -> None:
        """Cancel response - may not be supported."""
        logger.warning("cancel_response() may not be supported by Grok API")
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
        await self._send_message(
            messages.conversation_item_create_tool_result(call_id, result, is_error)
        )

    # =========================================================================
    # Session Updates
    # =========================================================================

    async def update_session(self, config: VoiceSessionConfig) -> None:
        async with self._lock:
            self._ensure_connected()
            await self._ws.send_json(messages.session_update(config))
            self._config = config

    # =========================================================================
    # Conversation Management
    # =========================================================================

    async def reset_conversation(self) -> None:
        """
        Reset conversation.

        WARNING: Grok API does not document conversation.item.delete.
        This is not supported.
        """
        raise NotImplementedError(
            "Grok API does not support conversation reset. "
            "Disconnect and reconnect to start fresh."
        )

    # =========================================================================
    # Event Stream
    # =========================================================================

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        while True:
            try:
                event = await self._event_queue.get()
                if event is _STOP_SENTINEL:
                    return
                yield event
            except asyncio.CancelledError:
                return

    # =========================================================================
    # Capabilities
    # =========================================================================

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="grok",
            supports_server_vad=True,
            supports_function_calling=True,
            supports_interruption=False,  # Not documented
            supports_transcription=True,
            supports_input_transcription=True,
            supports_conversation_reset=False,  # Not documented
            available_voices=["Ara", "Rex", "Sal", "Eve", "Leo"],
            available_models=[],  # Grok has single implicit model
        )

    # =========================================================================
    # Metrics
    # =========================================================================

    def get_stats(self) -> dict:
        ws = self._ws
        if ws:
            return ws.get_stats()
        return {}

    # =========================================================================
    # Internal
    # =========================================================================

    def _ensure_connected(self) -> None:
        if not self.is_connected():
            raise RealtimeSessionError("Not connected")

    async def _send_message(self, msg: dict) -> None:
        self._ensure_connected()
        try:
            await self._ws.send_json(msg)
        except WebSocketBackpressureError:
            raise RealtimeRateLimitError("Send queue full - backpressure")

    def _queue_event_nowait(self, event: VoiceEvent | object) -> None:
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            if event is not _STOP_SENTINEL and isinstance(event, VoiceEvent):
                logger.warning("Event queue full, dropping event: %s", event.type)

    def _track_conversation_item(self, raw_event: dict) -> None:
        if raw_event.get("type") != "conversation.item.added":
            return
        item = raw_event.get("item", {})
        item_id = item.get("id")
        if item_id and item_id not in self._conversation_item_ids:
            self._conversation_item_ids.append(item_id)

    async def _receive_loop(self) -> None:
        try:
            async for msg in self._ws.messages():
                try:
                    raw = json.loads(msg.as_text())
                    self._track_conversation_item(raw)
                    event = translate_event(raw)

                    if event:
                        # Handle session lifecycle events
                        if event.type == VoiceEventType.SESSION_CREATED:
                            # conversation.created - initial handshake
                            self._session_ready.set()
                        elif event.type == VoiceEventType.SESSION_UPDATED:
                            # session.updated - our config was applied
                            self._session_configured.set()

                        if event.type == VoiceEventType.ERROR:
                            logger.warning(
                                "Grok error: %s - %s",
                                event.data.get("code") if event.data else None,
                                event.data.get("message") if event.data else None,
                            )

                        self._queue_event_nowait(event)

                except Exception as e:
                    logger.exception("Error processing message: %s", e)
                    self._queue_event_nowait(VoiceEvent(
                        type=VoiceEventType.ERROR,
                        data={"code": "message_processing_error", "message": str(e)},
                    ))

        except asyncio.CancelledError:
            pass
        except WebSocketClosedError:
            self._queue_event_nowait(VoiceEvent(type=VoiceEventType.DISCONNECTED))

    def _on_disconnect(self, error: Exception | None) -> None:
        self._queue_event_nowait(VoiceEvent(
            type=VoiceEventType.DISCONNECTED,
            data={"error": str(error)} if error else None,
        ))

    def _on_reconnecting(self, attempt: int) -> None:
        self._queue_event_nowait(VoiceEvent(
            type=VoiceEventType.RECONNECTING,
            metadata={"attempt": attempt},
        ))

    def _on_reconnect_success(self) -> None:
        if self._config:
            asyncio.create_task(self._resend_session_config())

    async def _resend_session_config(self) -> None:
        try:
            if self._config and self._ws and self._ws.is_connected:
                await self._ws.send_json(messages.session_update(self._config))
                self._queue_event_nowait(VoiceEvent(
                    type=VoiceEventType.CONNECTED,
                    metadata={"reconnected": True},
                ))
        except Exception as e:
            logger.error("Failed to re-send session config after reconnect: %s", e)
