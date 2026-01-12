"""Mock RealtimeVoiceAPIPort for testing without real API."""

import asyncio
from typing import AsyncGenerator

from chatforge.ports.realtime_voice import (
    RealtimeVoiceAPIPort,
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    ProviderCapabilities,
    RealtimeSessionError,
)


# Sentinel value for stopping the event generator
_STOP_SENTINEL = object()


@RealtimeVoiceAPIPort.register("mock")
class MockRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    Mock RealtimeVoiceAPIPort for testing.

    Provides controllable real-time AI simulation for unit tests
    without requiring actual API connections.

    Example:
        mock = MockRealtimeAdapter()
        mock.queue_audio_response(b"hello audio", chunk_size=4800)

        async with mock:
            await mock.connect(VoiceSessionConfig())

            async for event in mock.events():
                if event.type == VoiceEventType.AUDIO_CHUNK:
                    audio_chunks.append(event.data)
                if event.type == VoiceEventType.RESPONSE_DONE:
                    break

        assert len(mock.sent_audio) > 0
    """

    def __init__(self, *, simulate_latency_ms: int = 0):
        """
        Initialize mock adapter.

        Args:
            simulate_latency_ms: Optional latency to simulate on operations
        """
        self._connected = False
        self._config: VoiceSessionConfig | None = None
        # Bounded queue to match real adapter behavior
        self._event_queue: asyncio.Queue[VoiceEvent | object] = asyncio.Queue(
            maxsize=1000
        )
        self._latency = simulate_latency_ms / 1000.0

        # Test state for assertions
        self.sent_audio: list[bytes] = []
        self.sent_text: list[str] = []
        self.tool_results: list[tuple[str, str, bool]] = []
        self.committed_count: int = 0
        self.cleared_count: int = 0
        self.interrupt_count: int = 0
        self.reset_count: int = 0
        self.response_requests: list[str | None] = []
        # Track conversation item IDs (for testing)
        self._conversation_item_ids: list[str] = []

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def provider_name(self) -> str:
        return "mock"

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "MockRealtimeAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def connect(self, config: VoiceSessionConfig) -> None:
        if self._connected:
            raise RealtimeSessionError("Already connected")

        if self._latency:
            await asyncio.sleep(self._latency)

        self._config = config
        self._connected = True

        # Emit session created and connected events (like real adapter)
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.SESSION_CREATED))
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.CONNECTED))

    async def disconnect(self) -> None:
        if self._connected:
            self._connected = False
            await self._event_queue.put(VoiceEvent(type=VoiceEventType.DISCONNECTED))
            # Signal event generator to stop
            await self._event_queue.put(_STOP_SENTINEL)

    def is_connected(self) -> bool:
        return self._connected

    # =========================================================================
    # Audio Streaming
    # =========================================================================

    async def send_audio(self, chunk: bytes) -> None:
        self._ensure_connected()
        if self._latency:
            await asyncio.sleep(self._latency)
        self.sent_audio.append(chunk)

    async def commit_audio(self) -> None:
        self._ensure_connected()
        self.committed_count += 1
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.AUDIO_COMMITTED))

    async def clear_audio(self) -> None:
        self._ensure_connected()
        self.cleared_count += 1
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.AUDIO_CLEARED))

    # =========================================================================
    # Text Input
    # =========================================================================

    async def add_text_item(self, text: str) -> None:
        self._ensure_connected()
        self.sent_text.append(text)

    async def send_text(self, text: str, *, trigger_response: bool = True) -> None:
        await self.add_text_item(text)
        if trigger_response:
            await self.create_response()

    # =========================================================================
    # Response Control
    # =========================================================================

    async def create_response(self, instructions: str | None = None) -> None:
        self._ensure_connected()
        self.response_requests.append(instructions)

    async def interrupt(self) -> None:
        self._ensure_connected()
        self.interrupt_count += 1
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.RESPONSE_CANCELLED))

    async def cancel_response(self, response_id: str | None = None) -> None:
        await self.interrupt()

    # =========================================================================
    # Conversation Management
    # =========================================================================

    async def reset_conversation(self) -> None:
        """Mock implementation - just clear tracking and increment counter."""
        self._ensure_connected()
        self.reset_count += 1
        self._conversation_item_ids.clear()

    # =========================================================================
    # Tool Calling
    # =========================================================================

    async def send_tool_result(
        self,
        call_id: str,
        result: str,
        is_error: bool = False,
    ) -> None:
        self._ensure_connected()
        self.tool_results.append((call_id, result, is_error))

    # =========================================================================
    # Session Updates
    # =========================================================================

    async def update_session(self, config: VoiceSessionConfig) -> None:
        self._ensure_connected()
        self._config = config
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.SESSION_UPDATED))

    # =========================================================================
    # Event Stream
    # =========================================================================

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """Stream events using stop sentinel for clean termination."""
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
        return ProviderCapabilities(
            provider_name="mock",
            supports_server_vad=True,
            supports_function_calling=True,
            supports_interruption=True,
            supports_transcription=True,
            supports_input_transcription=True,
            supports_conversation_reset=True,
            available_voices=["mock_voice"],
            available_models=["mock_model"],
        )

    # =========================================================================
    # Internal
    # =========================================================================

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RealtimeSessionError("Not connected")

    # =========================================================================
    # Test Helpers
    # =========================================================================

    async def queue_event(self, event: VoiceEvent) -> None:
        """Queue an event to be received."""
        await self._event_queue.put(event)

    async def queue_audio_response(self, audio: bytes, chunk_size: int = 4800) -> None:
        """Queue a complete audio response."""
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.RESPONSE_STARTED))

        for i in range(0, len(audio), chunk_size):
            chunk = audio[i : i + chunk_size]
            await self._event_queue.put(
                VoiceEvent(type=VoiceEventType.AUDIO_CHUNK, data=chunk)
            )

        await self._event_queue.put(VoiceEvent(type=VoiceEventType.AUDIO_DONE))
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.RESPONSE_DONE))

    async def queue_tool_call(
        self, call_id: str, name: str, arguments: dict
    ) -> None:
        """Queue a tool call event."""
        await self._event_queue.put(
            VoiceEvent(
                type=VoiceEventType.TOOL_CALL,
                data={
                    "call_id": call_id,
                    "name": name,
                    "arguments": arguments,
                },
            )
        )

    async def queue_speech_events(self) -> None:
        """Queue speech start/end events."""
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.SPEECH_STARTED))
        await asyncio.sleep(0.01)
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.SPEECH_ENDED))

    async def simulate_disconnect(self) -> None:
        """Simulate a disconnection."""
        self._connected = False
        await self._event_queue.put(VoiceEvent(type=VoiceEventType.DISCONNECTED))

    async def simulate_error(self, code: str, message: str) -> None:
        """Simulate an error event."""
        await self._event_queue.put(
            VoiceEvent(
                type=VoiceEventType.ERROR,
                data={"code": code, "message": message},
            )
        )

    def get_total_sent_audio_bytes(self) -> int:
        """Get total bytes of audio sent."""
        return sum(len(chunk) for chunk in self.sent_audio)

    def reset(self) -> None:
        """Reset all test state."""
        self.sent_audio = []
        self.sent_text = []
        self.tool_results = []
        self.committed_count = 0
        self.cleared_count = 0
        self.interrupt_count = 0
        self.reset_count = 0
        self.response_requests = []
        self._conversation_item_ids = []
        # Clear the queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def queue_conversation_item(self, item_id: str) -> None:
        """Queue a conversation item created event (simulates item tracking)."""
        self._conversation_item_ids.append(item_id)
        await self._event_queue.put(
            VoiceEvent(
                type=VoiceEventType.CONVERSATION_ITEM,
                data={"id": item_id, "type": "message"},
                metadata={"item_id": item_id},
            )
        )
