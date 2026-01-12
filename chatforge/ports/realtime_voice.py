"""
RealtimeVoiceAPIPort - Abstract interface for real-time AI voice APIs.

This port enables voice applications to connect to real-time AI APIs
(OpenAI Realtime, future Anthropic/Google) without coupling to specific
provider implementations.

Implementations handle provider-specific details:
- OpenAIRealtimeAdapter: OpenAI Realtime API
- MockRealtimeAdapter: For testing without real API

Usage:
    from chatforge.ports.realtime_voice import RealtimeVoiceAPIPort, VoiceSessionConfig

    async with OpenAIRealtimeAdapter(api_key=key) as realtime:
        await realtime.connect(VoiceSessionConfig(voice="alloy"))

        async for event in realtime.events():
            if event.type == VoiceEventType.AUDIO_CHUNK:
                await audio.play(event.data)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, AsyncGenerator, ClassVar, Literal
import time


__all__ = [
    # Exceptions
    "RealtimeError",
    "RealtimeConnectionError",
    "RealtimeAuthenticationError",
    "RealtimeRateLimitError",
    "RealtimeProviderError",
    "RealtimeSessionError",
    # Enums
    "VoiceEventType",
    # Data classes
    "VoiceEvent",
    "VoiceSessionConfig",
    "ToolDefinition",
    "ProviderCapabilities",
    # Port
    "RealtimeVoiceAPIPort",
]


# =============================================================================
# Exceptions
# =============================================================================


class RealtimeError(Exception):
    """Base exception for RealtimeVoiceAPIPort."""

    pass


class RealtimeConnectionError(RealtimeError):
    """Network or connection issues."""

    pass


class RealtimeAuthenticationError(RealtimeError):
    """Invalid API key or authentication failure."""

    pass


class RealtimeRateLimitError(RealtimeError):
    """Rate limited by provider."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class RealtimeProviderError(RealtimeError):
    """Provider-specific error (e.g., model unavailable)."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class RealtimeSessionError(RealtimeError):
    """Invalid session state (e.g., not connected, already connected)."""

    pass


# =============================================================================
# Event Types
# =============================================================================


class VoiceEventType(str, Enum):
    """Normalized event types from realtime API."""

    # Connection lifecycle
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

    # Session
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"

    # Audio output (AI -> User)
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_DONE = "audio.done"

    # Audio input (User -> AI)
    AUDIO_COMMITTED = "audio.committed"
    AUDIO_CLEARED = "audio.cleared"

    # Voice Activity Detection
    SPEECH_STARTED = "speech.started"
    SPEECH_ENDED = "speech.ended"

    # Text/Transcripts
    TEXT_CHUNK = "text.chunk"
    TEXT_DONE = "text.done"
    TRANSCRIPT = "transcript"
    INPUT_TRANSCRIPT = "input_transcript"

    # Response lifecycle
    RESPONSE_STARTED = "response.started"
    RESPONSE_DONE = "response.done"
    RESPONSE_CANCELLED = "response.cancelled"

    # Tool calling
    TOOL_CALL = "tool.call"
    TOOL_CALL_DONE = "tool.call.done"

    # Conversation
    CONVERSATION_ITEM = "conversation.item"

    # Usage/Limits
    USAGE_UPDATED = "usage.updated"


@dataclass
class VoiceEvent:
    """
    Normalized event from realtime API.

    Attributes:
        type: Event type (from VoiceEventType enum)
        data: Event payload (bytes for audio, dict for structured data)
        metadata: Additional context (response_id, item_id, etc.)
        timestamp: Event timestamp (monotonic for duration calculations)
        raw_event: Original provider event (for debugging)
    """

    type: VoiceEventType
    data: bytes | str | dict | None = None
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.monotonic)
    raw_event: Any = None


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class ToolDefinition:
    """Tool/function definition for AI to call."""

    name: str
    description: str
    parameters: dict  # JSON Schema


@dataclass
class VoiceSessionConfig:
    """
    Provider-agnostic session configuration.

    Adapters translate this to provider-specific format.
    """

    # Model (adapter resolves to actual model name)
    model: str = "default"

    # Voice (adapter resolves to actual voice ID)
    voice: str = "default"

    # System prompt
    system_prompt: str | None = None

    # Generation parameters
    temperature: float = 0.8
    max_tokens: int | None = None

    # Modalities
    modalities: list[Literal["audio", "text"]] = field(
        default_factory=lambda: ["audio", "text"]
    )

    # Audio format
    input_format: str = "pcm16"
    output_format: str = "pcm16"
    sample_rate: int = 24000

    # Voice Activity Detection
    vad_mode: Literal["server", "client", "none"] = "server"
    vad_threshold: float = 0.5
    vad_silence_ms: int = 500
    vad_prefix_ms: int = 300

    # Transcription
    transcription_enabled: bool = True
    transcription_model: str | None = None

    # Tools
    tools: list[ToolDefinition] | None = None
    tool_choice: Literal["auto", "none", "required"] = "auto"

    # Provider-specific options (escape hatch)
    provider_options: dict | None = None

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be 0.0-2.0, got {self.temperature}")
        if not 0.0 <= self.vad_threshold <= 1.0:
            raise ValueError(
                f"vad_threshold must be 0.0-1.0, got {self.vad_threshold}"
            )
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.vad_silence_ms < 0:
            raise ValueError(
                f"vad_silence_ms must be non-negative, got {self.vad_silence_ms}"
            )
        if self.vad_prefix_ms < 0:
            raise ValueError(
                f"vad_prefix_ms must be non-negative, got {self.vad_prefix_ms}"
            )
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")


@dataclass
class ProviderCapabilities:
    """What the provider supports."""

    provider_name: str
    supports_server_vad: bool = True
    supports_function_calling: bool = True
    supports_interruption: bool = True
    supports_transcription: bool = True
    supports_input_transcription: bool = True
    supports_conversation_reset: bool = False
    max_audio_length_seconds: float | None = None
    available_voices: list[str] = field(default_factory=list)
    available_models: list[str] = field(default_factory=list)


# =============================================================================
# Port Interface
# =============================================================================


class RealtimeVoiceAPIPort(ABC):
    """
    Abstract interface for real-time AI voice APIs.

    Implementations handle provider-specific details:
    - OpenAIRealtimeAdapter: OpenAI Realtime API
    - AnthropicRealtimeAdapter: Anthropic (future)
    - MockRealtimeAdapter: For testing

    Example:
        async with OpenAIRealtimeAdapter(api_key=key) as realtime:
            await realtime.connect(VoiceSessionConfig(voice="alloy"))

            # Concurrent send/receive
            async def send_loop():
                async for chunk in audio.start_capture():
                    await realtime.send_audio(chunk)

            async def receive_loop():
                async for event in realtime.events():
                    if event.type == VoiceEventType.AUDIO_CHUNK:
                        await audio.play(event.data)

            await asyncio.gather(send_loop(), receive_loop())

    Using the registry pattern:
        import chatforge.adapters.realtime  # Triggers registration

        # Create adapter by provider name
        adapter = RealtimeVoiceAPIPort.create("openai")
        adapter = RealtimeVoiceAPIPort.create("grok")

        # List available providers
        providers = RealtimeVoiceAPIPort.available_providers()
    """

    # =========================================================================
    # Adapter Registry
    # =========================================================================

    _adapters: ClassVar[dict[str, type["RealtimeVoiceAPIPort"]]] = {}

    @classmethod
    def register(cls, provider: str):
        """
        Decorator to register an adapter for a provider.

        Usage:
            @RealtimeVoiceAPIPort.register("openai")
            class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
                ...
        """
        def decorator(adapter_cls: type["RealtimeVoiceAPIPort"]):
            cls._adapters[provider] = adapter_cls
            return adapter_cls
        return decorator

    @classmethod
    def create(cls, provider: str, **kwargs) -> "RealtimeVoiceAPIPort":
        """
        Create adapter instance for provider.

        Args:
            provider: Provider name ("openai", "grok", etc.)
            **kwargs: Optional overrides (api_key, model, etc.)

        Returns:
            Configured adapter instance (not yet connected)

        Raises:
            ValueError: If provider not registered or config missing
        """
        if provider not in cls._adapters:
            available = list(cls._adapters.keys())
            raise ValueError(f"Unknown provider '{provider}'. Available: {available}")
        return cls._adapters[provider](**kwargs)

    @classmethod
    def available_providers(cls) -> list[str]:
        """List registered provider names."""
        return list(cls._adapters.keys())

    # =========================================================================
    # Abstract Properties
    # =========================================================================

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'openai', 'mock')."""
        ...

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @abstractmethod
    async def __aenter__(self) -> "RealtimeVoiceAPIPort":
        """Enter async context (prepare for connection)."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context (cleanup)."""
        ...

    @abstractmethod
    async def connect(self, config: VoiceSessionConfig) -> None:
        """
        Connect to the AI provider and configure session.

        Args:
            config: Session configuration

        Raises:
            RealtimeConnectionError: Network issues
            RealtimeAuthenticationError: Invalid credentials
            RealtimeSessionError: Already connected
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect gracefully."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected."""
        ...

    # =========================================================================
    # Audio Streaming
    # =========================================================================

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """
        Send audio chunk to AI.

        Args:
            chunk: PCM16 audio bytes (24kHz mono)

        Raises:
            RealtimeSessionError: Not connected
        """
        ...

    @abstractmethod
    async def commit_audio(self) -> None:
        """
        Commit audio buffer (for manual VAD mode).

        Call this when user stops speaking to trigger AI response.
        """
        ...

    @abstractmethod
    async def clear_audio(self) -> None:
        """Clear audio buffer without committing."""
        ...

    # =========================================================================
    # Text Input
    # =========================================================================

    @abstractmethod
    async def add_text_item(self, text: str) -> None:
        """
        Add text to conversation without triggering response.

        Use this when you want to send multiple text items before
        triggering a response with create_response().
        """
        ...

    @abstractmethod
    async def send_text(self, text: str, *, trigger_response: bool = True) -> None:
        """
        Send text message to AI.

        Args:
            text: Text message content
            trigger_response: If True (default), automatically trigger AI response.
                             Set to False to send multiple texts before responding.
        """
        ...

    # =========================================================================
    # Response Control
    # =========================================================================

    @abstractmethod
    async def create_response(self, instructions: str | None = None) -> None:
        """
        Trigger AI response.

        Args:
            instructions: Optional one-time instructions for this response
        """
        ...

    @abstractmethod
    async def interrupt(self) -> None:
        """
        Interrupt current response (barge-in).

        Cancels AI response and clears output.
        """
        ...

    @abstractmethod
    async def cancel_response(self, response_id: str | None = None) -> None:
        """
        Cancel specific or current response.

        Args:
            response_id: Specific response to cancel, or None for current
        """
        ...

    # =========================================================================
    # Conversation Management
    # =========================================================================

    @abstractmethod
    async def reset_conversation(self) -> None:
        """
        Clear conversation history.

        After reset:
        - Conversation history is empty
        - System prompt remains active
        - Tools remain configured
        - Session stays connected

        Use this for "stateless-like" behavior where you want
        to inject fresh context without prior conversation history.

        Raises:
            RealtimeSessionError: Not connected
            NotImplementedError: Provider doesn't support reset
        """
        ...

    # =========================================================================
    # Tool Calling
    # =========================================================================

    @abstractmethod
    async def send_tool_result(
        self,
        call_id: str,
        result: str,
        is_error: bool = False,
    ) -> None:
        """
        Send tool execution result back to AI.

        Args:
            call_id: The call_id from TOOL_CALL event
            result: JSON-encoded result string
            is_error: True if tool execution failed
        """
        ...

    # =========================================================================
    # Session Updates
    # =========================================================================

    @abstractmethod
    async def update_session(self, config: VoiceSessionConfig) -> None:
        """
        Update session configuration mid-session.

        Not all settings can be updated (e.g., model, audio formats).
        Adapter validates and raises RealtimeSessionError if invalid.

        Args:
            config: New configuration (only changed fields matter)
        """
        ...

    # =========================================================================
    # Event Stream
    # =========================================================================

    @abstractmethod
    def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """
        Stream normalized events from AI.

        Note: Only one consumer should iterate events(). Multiple consumers
        will compete for events (each event goes to only one consumer).

        Yields:
            VoiceEvent with normalized type and data

        Example:
            async for event in realtime.events():
                match event.type:
                    case VoiceEventType.AUDIO_CHUNK:
                        await audio.play(event.data)
                    case VoiceEventType.TOOL_CALL:
                        result = execute_tool(event.data)
                        await realtime.send_tool_result(...)
        """
        ...

    # =========================================================================
    # Capabilities
    # =========================================================================

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities for runtime feature detection."""
        ...

    # =========================================================================
    # Metrics (Optional)
    # =========================================================================

    def get_stats(self) -> dict:
        """
        Get connection statistics.

        Returns:
            Dict with messages_sent, messages_received, uptime, etc.
            Returns empty dict if metrics not supported.
        """
        return {}
