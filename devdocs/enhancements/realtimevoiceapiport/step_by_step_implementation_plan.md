# RealtimeVoiceAPIPort: Step-by-Step Implementation Plan

*Implementation guide for building the RealtimeVoiceAPIPort following chatforge's hexagonal architecture.*

**Prerequisites**:
- `chatforge/infrastructure/websocket/` is implemented and tested (37 tests passing)
- Design document: `realtimevoiceapiport_design.md`

---

## Overview

### What We're Building

```
chatforge/
├── ports/
│   └── realtime_voice.py          # Port interface + types + exceptions
├── adapters/
│   └── realtime/
│       ├── __init__.py            # Package exports
│       ├── openai/
│       │   ├── __init__.py        # Exports OpenAIRealtimeAdapter
│       │   ├── adapter.py         # Main adapter (uses WebSocketClient)
│       │   ├── messages.py        # OpenAI message factory
│       │   └── translator.py      # Event translation (OpenAI → VoiceEvent)
│       └── mock/
│           ├── __init__.py        # Exports MockRealtimeAdapter
│           └── adapter.py         # Mock for testing
└── tests/
    └── adapters/
        └── realtime/
            ├── conftest.py        # Shared fixtures
            ├── test_openai.py     # OpenAI adapter tests
            └── test_mock.py       # Mock adapter tests
```

### Key Dependencies

```python
# The adapter uses WebSocket infrastructure we built:
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    JsonSerializer,
    ConnectionState,
    WebSocketConnectionError,
)
```

---

## Step 1: Port Interface (`chatforge/ports/realtime_voice.py`)

### 1.1 Create the File Structure

```python
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
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal
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
```

### 1.2 Exceptions

```python
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
```

### 1.3 Event Types

```python
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

    # Audio output (AI → User)
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_DONE = "audio.done"

    # Audio input (User → AI)
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
```

### 1.4 Configuration Types

```python
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
            raise ValueError(f"vad_threshold must be 0.0-1.0, got {self.vad_threshold}")
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.vad_silence_ms < 0:
            raise ValueError(f"vad_silence_ms must be non-negative, got {self.vad_silence_ms}")
        if self.vad_prefix_ms < 0:
            raise ValueError(f"vad_prefix_ms must be non-negative, got {self.vad_prefix_ms}")
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
    max_audio_length_seconds: float | None = None
    available_voices: list[str] = field(default_factory=list)
    available_models: list[str] = field(default_factory=list)
```

### 1.5 Port Interface

```python
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
    """

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
    async def send_text(self, text: str) -> None:
        """
        Send text message to AI.

        Args:
            text: Text message content
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
```

---

## Step 2: OpenAI Adapter (`chatforge/adapters/realtime/openai/`)

### 2.1 Package Structure

Create directory: `chatforge/adapters/realtime/openai/`

**`__init__.py`**:
```python
"""OpenAI Realtime API adapter."""

from .adapter import OpenAIRealtimeAdapter

__all__ = ["OpenAIRealtimeAdapter"]
```

### 2.2 Message Factory (`messages.py`)

```python
"""OpenAI Realtime API message factory."""

import base64
import json
from typing import Any

from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition


# =============================================================================
# Client → Server Messages
# =============================================================================


def session_update(config: VoiceSessionConfig) -> dict:
    """Create session.update message."""
    session = {
        "modalities": config.modalities,
        "temperature": config.temperature,
    }

    # Voice
    if config.voice != "default":
        session["voice"] = config.voice

    # Instructions
    if config.system_prompt:
        session["instructions"] = config.system_prompt

    # Max tokens
    if config.max_tokens:
        session["max_response_output_tokens"] = config.max_tokens

    # Audio format
    session["input_audio_format"] = config.input_format
    session["output_audio_format"] = config.output_format

    # Transcription
    if config.transcription_enabled:
        session["input_audio_transcription"] = {
            "model": config.transcription_model or "whisper-1"
        }

    # Turn detection (VAD)
    # "server" = use server-side VAD
    # "client" = client handles VAD, disable server VAD
    # "none" = no VAD, manual commit required
    if config.vad_mode == "server":
        session["turn_detection"] = {
            "type": "server_vad",
            "threshold": config.vad_threshold,
            "prefix_padding_ms": config.vad_prefix_ms,
            "silence_duration_ms": config.vad_silence_ms,
            "create_response": True,
        }
    else:  # "client" or "none" - disable server VAD
        session["turn_detection"] = None

    # Tools
    if config.tools:
        session["tools"] = [_tool_to_openai(t) for t in config.tools]
        session["tool_choice"] = config.tool_choice

    # Provider-specific overrides
    if config.provider_options:
        session.update(config.provider_options)

    return {"type": "session.update", "session": session}


def input_audio_buffer_append(audio: bytes) -> dict:
    """Create input_audio_buffer.append message."""
    return {
        "type": "input_audio_buffer.append",
        "audio": base64.b64encode(audio).decode("ascii"),
    }


def input_audio_buffer_commit() -> dict:
    """Create input_audio_buffer.commit message."""
    return {"type": "input_audio_buffer.commit"}


def input_audio_buffer_clear() -> dict:
    """Create input_audio_buffer.clear message."""
    return {"type": "input_audio_buffer.clear"}


def conversation_item_create_message(text: str) -> dict:
    """Create text message item."""
    return {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        },
    }


def conversation_item_create_tool_result(
    call_id: str,
    output: str,
    is_error: bool = False
) -> dict:
    """Create function call output item."""
    item = {
        "type": "function_call_output",
        "call_id": call_id,
        "output": output,
    }
    # Include error status if this is an error response
    # OpenAI uses this to know the tool failed
    if is_error:
        item["error"] = True
    return {
        "type": "conversation.item.create",
        "item": item,
    }


def response_create(instructions: str | None = None) -> dict:
    """Create response.create message."""
    msg = {"type": "response.create"}
    if instructions:
        msg["response"] = {"instructions": instructions}
    return msg


def response_cancel(response_id: str | None = None) -> dict:
    """Create response.cancel message."""
    msg = {"type": "response.cancel"}
    if response_id:
        msg["response_id"] = response_id
    return msg


# =============================================================================
# Helpers
# =============================================================================


def _tool_to_openai(tool: ToolDefinition) -> dict:
    """Convert ToolDefinition to OpenAI format."""
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
```

### 2.3 Event Translator (`translator.py`)

```python
"""Translate OpenAI events to normalized VoiceEvent."""

import base64
import binascii
import json
import logging
from typing import Any

from chatforge.ports.realtime_voice import VoiceEvent, VoiceEventType


logger = logging.getLogger(__name__)


def _safe_base64_decode(data: str) -> bytes | None:
    """Safely decode base64 data, returning None on failure."""
    try:
        return base64.b64decode(data)
    except (ValueError, binascii.Error) as e:
        logger.warning("Invalid base64 data: %s", e)
        return None


def translate_event(raw: dict) -> VoiceEvent | None:
    """
    Translate OpenAI event to VoiceEvent.

    Returns None for events we don't care about.
    """
    event_type = raw.get("type", "")

    # =========================================================================
    # Session Events
    # =========================================================================

    if event_type == "session.created":
        return VoiceEvent(
            type=VoiceEventType.SESSION_CREATED,
            data=raw.get("session"),
            raw_event=raw,
        )

    if event_type == "session.updated":
        return VoiceEvent(
            type=VoiceEventType.SESSION_UPDATED,
            data=raw.get("session"),
            raw_event=raw,
        )

    # =========================================================================
    # Audio Output Events
    # =========================================================================

    if event_type == "response.audio.delta":
        audio_data = _safe_base64_decode(raw.get("delta", ""))
        if audio_data is None:
            return None  # Skip invalid audio data
        return VoiceEvent(
            type=VoiceEventType.AUDIO_CHUNK,
            data=audio_data,
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "content_index": raw.get("content_index"),
            },
            raw_event=raw,
        )

    if event_type == "response.audio.done":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_DONE,
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    # =========================================================================
    # Audio Input Events
    # =========================================================================

    if event_type == "input_audio_buffer.committed":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_COMMITTED,
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.cleared":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_CLEARED,
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.speech_started":
        return VoiceEvent(
            type=VoiceEventType.SPEECH_STARTED,
            metadata={"audio_start_ms": raw.get("audio_start_ms")},
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.speech_stopped":
        return VoiceEvent(
            type=VoiceEventType.SPEECH_ENDED,
            metadata={
                "audio_end_ms": raw.get("audio_end_ms"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    # =========================================================================
    # Text/Transcript Events
    # =========================================================================

    if event_type == "response.text.delta":
        return VoiceEvent(
            type=VoiceEventType.TEXT_CHUNK,
            data=raw.get("delta", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    if event_type == "response.text.done":
        return VoiceEvent(
            type=VoiceEventType.TEXT_DONE,
            data=raw.get("text", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    if event_type == "response.audio_transcript.delta":
        return VoiceEvent(
            type=VoiceEventType.TRANSCRIPT,
            data=raw.get("delta", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "is_delta": True,
            },
            raw_event=raw,
        )

    if event_type == "response.audio_transcript.done":
        return VoiceEvent(
            type=VoiceEventType.TRANSCRIPT,
            data=raw.get("transcript", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "is_delta": False,
            },
            raw_event=raw,
        )

    if event_type == "conversation.item.input_audio_transcription.completed":
        return VoiceEvent(
            type=VoiceEventType.INPUT_TRANSCRIPT,
            data=raw.get("transcript", ""),
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Response Lifecycle Events
    # =========================================================================

    if event_type == "response.created":
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_STARTED,
            metadata={"response_id": raw.get("response", {}).get("id")},
            raw_event=raw,
        )

    if event_type == "response.done":
        response = raw.get("response", {})
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_DONE,
            data={
                "status": response.get("status"),
                "usage": response.get("usage"),
            },
            metadata={"response_id": response.get("id")},
            raw_event=raw,
        )

    if event_type == "response.cancelled":
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_CANCELLED,
            metadata={"response_id": raw.get("response_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Tool Calling Events
    # =========================================================================

    if event_type == "response.function_call_arguments.done":
        return VoiceEvent(
            type=VoiceEventType.TOOL_CALL,
            data={
                "call_id": raw.get("call_id"),
                "name": raw.get("name"),
                "arguments": _safe_json_parse(raw.get("arguments", "{}")),
            },
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    # =========================================================================
    # Conversation Events
    # =========================================================================

    if event_type == "conversation.item.created":
        return VoiceEvent(
            type=VoiceEventType.CONVERSATION_ITEM,
            data=raw.get("item"),
            raw_event=raw,
        )

    # =========================================================================
    # Usage Events
    # =========================================================================

    if event_type == "rate_limits.updated":
        return VoiceEvent(
            type=VoiceEventType.USAGE_UPDATED,
            data=raw.get("rate_limits"),
            raw_event=raw,
        )

    # =========================================================================
    # Error Events
    # =========================================================================

    if event_type == "error":
        error = raw.get("error", {})
        return VoiceEvent(
            type=VoiceEventType.ERROR,
            data={
                "code": error.get("code"),
                "message": error.get("message"),
                "type": error.get("type"),
            },
            raw_event=raw,
        )

    # Unknown event - return None (don't propagate)
    return None


def _safe_json_parse(s: str) -> Any:
    """Safely parse JSON, returning original string on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s
```

### 2.4 Main Adapter (`adapter.py`)

```python
"""OpenAI Realtime API adapter using shared WebSocket infrastructure."""

import asyncio
import logging
from typing import AsyncGenerator

from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    JsonSerializer,
    ConnectionState,
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
    RealtimeProviderError,
    RealtimeRateLimitError,
)

from . import messages
from .translator import translate_event


logger = logging.getLogger(__name__)


# OpenAI Realtime API constants
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
DEFAULT_MODEL = "gpt-4o-realtime-preview-2024-12-17"

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
                reconnect_policy=ExponentialBackoff(
                    base=1.0,
                    factor=2.0,
                    max_delay=30.0,
                    max_attempts=self._max_reconnect_attempts,
                ) if self._auto_reconnect else None,
                ping_interval=20.0,
                enable_metrics=self._enable_metrics,
                enable_send_queue=True,
            )

            self._ws = WebSocketClient(ws_config)

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
                "gpt-4o-realtime-preview",
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
                    raw = msg.as_json()
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
```

---

## Step 3: Mock Adapter (`chatforge/adapters/realtime/mock/`)

### 3.1 Package Structure

**`__init__.py`**:
```python
"""Mock Realtime adapter for testing."""

from .adapter import MockRealtimeAdapter

__all__ = ["MockRealtimeAdapter"]
```

### 3.2 Mock Adapter (`adapter.py`)

```python
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
        self._event_queue: asyncio.Queue[VoiceEvent | object] = asyncio.Queue(maxsize=1000)
        self._latency = simulate_latency_ms / 1000.0

        # Test state for assertions
        self.sent_audio: list[bytes] = []
        self.sent_text: list[str] = []
        self.tool_results: list[tuple[str, str, bool]] = []
        self.committed_count: int = 0
        self.cleared_count: int = 0
        self.interrupt_count: int = 0
        self.response_requests: list[str | None] = []

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
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.SESSION_CREATED)
        )
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.CONNECTED)
        )

    async def disconnect(self) -> None:
        if self._connected:
            self._connected = False
            await self._event_queue.put(
                VoiceEvent(type=VoiceEventType.DISCONNECTED)
            )
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
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.AUDIO_COMMITTED)
        )

    async def clear_audio(self) -> None:
        self._ensure_connected()
        self.cleared_count += 1
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.AUDIO_CLEARED)
        )

    # =========================================================================
    # Text Input
    # =========================================================================

    async def send_text(self, text: str) -> None:
        self._ensure_connected()
        self.sent_text.append(text)

    # =========================================================================
    # Response Control
    # =========================================================================

    async def create_response(self, instructions: str | None = None) -> None:
        self._ensure_connected()
        self.response_requests.append(instructions)

    async def interrupt(self) -> None:
        self._ensure_connected()
        self.interrupt_count += 1
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.RESPONSE_CANCELLED)
        )

    async def cancel_response(self, response_id: str | None = None) -> None:
        await self.interrupt()

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
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.SESSION_UPDATED)
        )

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

    async def queue_audio_response(
        self,
        audio: bytes,
        chunk_size: int = 4800
    ) -> None:
        """Queue a complete audio response."""
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.RESPONSE_STARTED)
        )

        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i + chunk_size]
            await self._event_queue.put(
                VoiceEvent(type=VoiceEventType.AUDIO_CHUNK, data=chunk)
            )

        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.AUDIO_DONE)
        )
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.RESPONSE_DONE)
        )

    async def queue_tool_call(
        self,
        call_id: str,
        name: str,
        arguments: dict
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
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.SPEECH_STARTED)
        )
        await asyncio.sleep(0.01)
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.SPEECH_ENDED)
        )

    async def simulate_disconnect(self) -> None:
        """Simulate a disconnection."""
        self._connected = False
        await self._event_queue.put(
            VoiceEvent(type=VoiceEventType.DISCONNECTED)
        )

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
        self.response_requests = []
        # Clear the queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
```

---

## Step 4: Package Exports

### 4.1 Adapter Package (`chatforge/adapters/realtime/__init__.py`)

```python
"""Realtime voice API adapters."""

from .openai import OpenAIRealtimeAdapter
from .mock import MockRealtimeAdapter

__all__ = [
    "OpenAIRealtimeAdapter",
    "MockRealtimeAdapter",
]
```

### 4.2 Update Port Package (`chatforge/ports/__init__.py`)

Add exports:
```python
from .realtime_voice import (
    # Exceptions
    RealtimeError,
    RealtimeConnectionError,
    RealtimeAuthenticationError,
    RealtimeRateLimitError,
    RealtimeProviderError,
    RealtimeSessionError,
    # Enums
    VoiceEventType,
    # Data classes
    VoiceEvent,
    VoiceSessionConfig,
    ToolDefinition,
    ProviderCapabilities,
    # Port
    RealtimeVoiceAPIPort,
)
```

---

## Step 5: Tests

### 5.1 Test Structure

```
tests/adapters/realtime/
├── conftest.py          # Shared fixtures
├── test_mock.py         # Mock adapter tests
└── test_openai.py       # OpenAI adapter tests (integration)
```

### 5.2 Conftest (`conftest.py`)

```python
"""Fixtures for realtime adapter tests."""

import pytest

from chatforge.adapters.realtime import MockRealtimeAdapter
from chatforge.ports.realtime_voice import VoiceSessionConfig


@pytest.fixture
def mock_adapter():
    """Create a fresh mock adapter."""
    return MockRealtimeAdapter()


@pytest.fixture
def default_config():
    """Default voice session config."""
    return VoiceSessionConfig()


@pytest.fixture
def config_with_tools():
    """Config with tool definitions."""
    from chatforge.ports.realtime_voice import ToolDefinition

    return VoiceSessionConfig(
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get current weather",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                    },
                    "required": ["city"],
                },
            ),
        ],
    )
```

### 5.3 Mock Adapter Tests (`test_mock.py`)

```python
"""Tests for MockRealtimeAdapter."""

import pytest

from chatforge.adapters.realtime import MockRealtimeAdapter
from chatforge.ports.realtime_voice import (
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    RealtimeSessionError,
)


class TestMockAdapterLifecycle:
    """Tests for connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, mock_adapter, default_config):
        """Test basic connect/disconnect."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)
            assert mock_adapter.is_connected()

            await mock_adapter.disconnect()
            assert not mock_adapter.is_connected()

    @pytest.mark.asyncio
    async def test_context_manager_disconnect(self, mock_adapter, default_config):
        """Test context manager disconnects on exit."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

        assert not mock_adapter.is_connected()

    @pytest.mark.asyncio
    async def test_double_connect_raises(self, mock_adapter, default_config):
        """Test connecting twice raises error."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            with pytest.raises(RealtimeSessionError):
                await mock_adapter.connect(default_config)


class TestMockAdapterAudio:
    """Tests for audio operations."""

    @pytest.mark.asyncio
    async def test_send_audio(self, mock_adapter, default_config):
        """Test sending audio chunks."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_audio(b"\x00\x01\x02")
            await mock_adapter.send_audio(b"\x03\x04\x05")

            assert len(mock_adapter.sent_audio) == 2
            assert mock_adapter.get_total_sent_audio_bytes() == 6

    @pytest.mark.asyncio
    async def test_commit_audio(self, mock_adapter, default_config):
        """Test committing audio buffer."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.commit_audio()
            await mock_adapter.commit_audio()

            assert mock_adapter.committed_count == 2

    @pytest.mark.asyncio
    async def test_clear_audio(self, mock_adapter, default_config):
        """Test clearing audio buffer."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.clear_audio()

            assert mock_adapter.cleared_count == 1


class TestMockAdapterEvents:
    """Tests for event streaming."""

    @pytest.mark.asyncio
    async def test_receive_audio_response(self, mock_adapter, default_config):
        """Test receiving audio response events."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            # Queue audio response
            await mock_adapter.queue_audio_response(b"x" * 9600, chunk_size=4800)

            # Collect events
            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.RESPONSE_DONE:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.RESPONSE_STARTED in types
            assert VoiceEventType.AUDIO_CHUNK in types
            assert VoiceEventType.RESPONSE_DONE in types

    @pytest.mark.asyncio
    async def test_tool_call_flow(self, mock_adapter, config_with_tools):
        """Test tool calling flow."""
        async with mock_adapter:
            await mock_adapter.connect(config_with_tools)

            # Queue tool call
            await mock_adapter.queue_tool_call(
                call_id="call_123",
                name="get_weather",
                arguments={"city": "SF"},
            )

            # Handle tool call
            async for event in mock_adapter.events():
                if event.type == VoiceEventType.TOOL_CALL:
                    await mock_adapter.send_tool_result(
                        call_id=event.data["call_id"],
                        result='{"temp": 72}',
                    )
                    await mock_adapter.disconnect()
                    break

            assert len(mock_adapter.tool_results) == 1
            assert mock_adapter.tool_results[0] == ("call_123", '{"temp": 72}', False)

    @pytest.mark.asyncio
    async def test_interrupt(self, mock_adapter, default_config):
        """Test interrupting response."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.interrupt()

            assert mock_adapter.interrupt_count == 1


class TestMockAdapterText:
    """Tests for text operations."""

    @pytest.mark.asyncio
    async def test_send_text(self, mock_adapter, default_config):
        """Test sending text messages."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_text("Hello")
            await mock_adapter.send_text("World")

            assert mock_adapter.sent_text == ["Hello", "World"]


class TestMockAdapterNotConnected:
    """Tests for operations when not connected."""

    @pytest.mark.asyncio
    async def test_send_audio_not_connected(self, mock_adapter):
        """Test send_audio raises when not connected."""
        with pytest.raises(RealtimeSessionError):
            await mock_adapter.send_audio(b"\x00")

    @pytest.mark.asyncio
    async def test_send_text_not_connected(self, mock_adapter):
        """Test send_text raises when not connected."""
        with pytest.raises(RealtimeSessionError):
            await mock_adapter.send_text("hello")


class TestConfigValidation:
    """Tests for VoiceSessionConfig validation."""

    def test_valid_config(self):
        """Test valid config creation."""
        config = VoiceSessionConfig(
            temperature=0.5,
            vad_threshold=0.7,
            sample_rate=24000,
        )
        assert config.temperature == 0.5
        assert config.vad_threshold == 0.7

    def test_invalid_temperature_low(self):
        """Test temperature below 0 raises error."""
        with pytest.raises(ValueError, match="temperature must be 0.0-2.0"):
            VoiceSessionConfig(temperature=-0.1)

    def test_invalid_temperature_high(self):
        """Test temperature above 2 raises error."""
        with pytest.raises(ValueError, match="temperature must be 0.0-2.0"):
            VoiceSessionConfig(temperature=2.5)

    def test_invalid_vad_threshold(self):
        """Test vad_threshold outside 0-1 raises error."""
        with pytest.raises(ValueError, match="vad_threshold must be 0.0-1.0"):
            VoiceSessionConfig(vad_threshold=1.5)

    def test_invalid_sample_rate(self):
        """Test non-positive sample_rate raises error."""
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            VoiceSessionConfig(sample_rate=0)

    def test_invalid_vad_silence_ms(self):
        """Test negative vad_silence_ms raises error."""
        with pytest.raises(ValueError, match="vad_silence_ms must be non-negative"):
            VoiceSessionConfig(vad_silence_ms=-100)

    def test_invalid_max_tokens(self):
        """Test non-positive max_tokens raises error."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            VoiceSessionConfig(max_tokens=0)


class TestMockAdapterConnectedEvent:
    """Tests for CONNECTED event emission."""

    @pytest.mark.asyncio
    async def test_connected_event_emitted(self, mock_adapter, default_config):
        """Test CONNECTED event is emitted after connect."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.CONNECTED:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.SESSION_CREATED in types
            assert VoiceEventType.CONNECTED in types


class TestMockAdapterLatencySimulation:
    """Tests for latency simulation."""

    @pytest.mark.asyncio
    async def test_latency_simulation(self, default_config):
        """Test latency simulation works."""
        import time

        mock = MockRealtimeAdapter(simulate_latency_ms=50)

        start = time.monotonic()
        async with mock:
            await mock.connect(default_config)
        elapsed = time.monotonic() - start

        # Should have at least 50ms latency
        assert elapsed >= 0.05


class TestMockAdapterSessionUpdate:
    """Tests for session update operations."""

    @pytest.mark.asyncio
    async def test_update_session(self, mock_adapter, default_config):
        """Test session update emits event."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            new_config = VoiceSessionConfig(voice="shimmer")
            await mock_adapter.update_session(new_config)

            # Check SESSION_UPDATED was queued
            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.SESSION_UPDATED:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.SESSION_UPDATED in types


class TestMockAdapterReconnection:
    """Tests for reconnection simulation."""

    @pytest.mark.asyncio
    async def test_simulate_reconnecting(self, mock_adapter, default_config):
        """Test simulating reconnection events."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            # Simulate reconnecting
            await mock_adapter.queue_event(VoiceEvent(
                type=VoiceEventType.RECONNECTING,
                metadata={"attempt": 1},
            ))

            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.RECONNECTING:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.RECONNECTING in types
```

### 5.4 OpenAI Adapter Tests (`test_openai.py`)

```python
"""Tests for OpenAIRealtimeAdapter.

These are integration tests that require a real API key.
Set OPENAI_API_KEY environment variable to run.
"""

import os
import pytest

from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.ports.realtime_voice import (
    VoiceEventType,
    VoiceSessionConfig,
    RealtimeAuthenticationError,
    RealtimeSessionError,
)


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.environ["OPENAI_API_KEY"]


@pytest.fixture
def adapter(api_key):
    """Create OpenAI adapter."""
    return OpenAIRealtimeAdapter(api_key=api_key)


class TestOpenAIAdapterLifecycle:
    """Integration tests for connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, adapter):
        """Test basic connect/disconnect."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())
            assert adapter.is_connected()

            # Should receive session created event
            async for event in adapter.events():
                if event.type == VoiceEventType.SESSION_CREATED:
                    break

            await adapter.disconnect()
            assert not adapter.is_connected()

    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test authentication error with bad key."""
        adapter = OpenAIRealtimeAdapter(api_key="invalid-key")

        async with adapter:
            with pytest.raises(RealtimeAuthenticationError):
                await adapter.connect(VoiceSessionConfig())


class TestOpenAIAdapterCapabilities:
    """Tests for capabilities."""

    def test_capabilities(self, adapter):
        """Test capabilities are correct."""
        caps = adapter.get_capabilities()

        assert caps.provider_name == "openai"
        assert caps.supports_server_vad
        assert caps.supports_function_calling
        assert "alloy" in caps.available_voices


class TestOpenAIAdapterMetrics:
    """Tests for metrics."""

    @pytest.mark.asyncio
    async def test_metrics_after_connection(self, adapter):
        """Test metrics are tracked."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            stats = adapter.get_stats()
            assert stats.get("connects", 0) >= 1

            await adapter.disconnect()


class TestOpenAIAdapterSessionUpdate:
    """Tests for session update validation."""

    @pytest.mark.asyncio
    async def test_cannot_change_model_mid_session(self, adapter):
        """Test changing model mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(model="gpt-4o-realtime-preview"))

            with pytest.raises(RealtimeSessionError, match="Cannot change model"):
                await adapter.update_session(VoiceSessionConfig(model="different-model"))

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_cannot_change_input_format(self, adapter):
        """Test changing input format mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(input_format="pcm16"))

            with pytest.raises(RealtimeSessionError, match="Cannot change input format"):
                await adapter.update_session(VoiceSessionConfig(input_format="g711_ulaw"))

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_cannot_change_output_format(self, adapter):
        """Test changing output format mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(output_format="pcm16"))

            with pytest.raises(RealtimeSessionError, match="Cannot change output format"):
                await adapter.update_session(VoiceSessionConfig(output_format="g711_alaw"))

            await adapter.disconnect()


class TestOpenAIAdapterTextInput:
    """Tests for text input operations."""

    @pytest.mark.asyncio
    async def test_send_text_with_auto_response(self, adapter):
        """Test send_text triggers response by default."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            # send_text should work and trigger response
            await adapter.send_text("Hello")

            # Should receive response events
            async for event in adapter.events():
                if event.type == VoiceEventType.RESPONSE_STARTED:
                    # Got response, cancel and exit
                    await adapter.interrupt()
                    break

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_add_text_item_no_auto_response(self, adapter):
        """Test add_text_item doesn't trigger response."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            # add_text_item should not trigger response
            await adapter.add_text_item("Context 1")
            await adapter.add_text_item("Context 2")

            # Now explicitly trigger response
            await adapter.create_response()

            # Should receive response
            async for event in adapter.events():
                if event.type == VoiceEventType.RESPONSE_STARTED:
                    await adapter.interrupt()
                    break

            await adapter.disconnect()
```

---

## Step 6: Implementation Checklist

### Phase 1: Port Interface
- [ ] Create `chatforge/ports/realtime_voice.py`
- [ ] Implement exceptions
- [ ] Implement VoiceEventType enum
- [ ] Implement data classes (VoiceEvent, VoiceSessionConfig, etc.)
- [ ] Implement RealtimeVoiceAPIPort ABC
- [ ] Update `chatforge/ports/__init__.py`

### Phase 2: Mock Adapter
- [ ] Create `chatforge/adapters/realtime/mock/`
- [ ] Implement MockRealtimeAdapter
- [ ] Add test helpers (queue_event, queue_audio_response, etc.)
- [ ] Create `tests/adapters/realtime/test_mock.py`
- [ ] Run mock tests

### Phase 3: OpenAI Adapter
- [ ] Create `chatforge/adapters/realtime/openai/`
- [ ] Implement messages.py (message factory)
- [ ] Implement translator.py (event translation)
- [ ] Implement adapter.py (main adapter using WebSocketClient)
- [ ] Create `tests/adapters/realtime/test_openai.py`
- [ ] Run integration tests (requires API key)

### Phase 4: Package Exports
- [ ] Create `chatforge/adapters/realtime/__init__.py`
- [ ] Update main `chatforge/adapters/__init__.py`
- [ ] Verify imports work: `from chatforge.adapters.realtime import OpenAIRealtimeAdapter`

### Phase 5: Documentation
- [ ] Add usage examples to port docstring
- [ ] Document VoiceSessionConfig options
- [ ] Document error handling patterns

---

## Key Integration Points

### Using WebSocket Infrastructure

The OpenAI adapter uses our WebSocket infrastructure:

```python
from chatforge.infrastructure.websocket import (
    WebSocketClient,      # Main client
    WebSocketConfig,      # Configuration
    JsonSerializer,       # JSON message handling
    ExponentialBackoff,   # Reconnect policy
)
```

**Features we get for free:**
- Automatic reconnection with exponential backoff
- Ping/pong heartbeat (dead connection detection)
- Send queue with backpressure handling
- Connection metrics tracking
- Async callback support
- Connection leak prevention

### Using with AudioStreamPort

```python
async def voice_session():
    async with OpenAIRealtimeAdapter(api_key=key) as realtime:
        async with VoxStreamAdapter() as audio:
            await realtime.connect(VoiceSessionConfig(voice="alloy"))

            async def capture_loop():
                async for chunk in audio.start_capture():
                    await realtime.send_audio(chunk)

            async def playback_loop():
                async for event in realtime.events():
                    if event.type == VoiceEventType.AUDIO_CHUNK:
                        await audio.play(event.data)
                    elif event.type == VoiceEventType.AUDIO_DONE:
                        await audio.end_playback()

            await asyncio.gather(capture_loop(), playback_loop())
```

---

## Success Criteria

1. **All mock tests pass** - Validates port interface correctness
2. **OpenAI integration tests pass** - Validates real API compatibility
3. **No circular imports** - Clean dependency graph
4. **Metrics work** - Can track messages sent/received
5. **Reconnection works** - Auto-recovers from disconnects with session re-configuration
6. **Tool calling works** - Complete flow with mock adapter
7. **Type checking passes** - No mypy errors
8. **Config validation works** - Invalid configs raise ValueError
9. **Thread safety** - Concurrent send/receive works without race conditions
10. **Backpressure handling** - RealtimeRateLimitError raised when queue full
11. **Event lifecycle correct** - CONNECTED, RECONNECTING, DISCONNECTED events emitted properly

---

## Issues Addressed from Critical Review

The following issues from `critic.md` have been fixed in this implementation:

### Critical Issues Fixed

| Issue | Fix |
|-------|-----|
| Missing CONNECTED event | Emit after session setup completes |
| Empty reconnection handler | Re-send session config via `_on_reconnect_success` |
| No thread safety | Added `asyncio.Lock` for shared state |
| Session ready race | Start receive loop BEFORE sending session update |
| No backpressure handling | Catch `WebSocketBackpressureError`, raise `RealtimeRateLimitError` |
| Unbounded event queue | `asyncio.Queue(maxsize=1000)` |

### Major Issues Fixed

| Issue | Fix |
|-------|-----|
| vad_mode="client" not handled | Handle in session_update, disable server VAD |
| send_text auto-response | Added `trigger_response` param and `add_text_item` method |
| Config validation missing | Added `__post_init__` validation |
| is_connected race | Use local reference pattern |
| Base64 error handling | `_safe_base64_decode` with logging |
| is_error ignored in tool result | Include in message payload |
| events() with yield in ABC | Removed yield from abstract method |
| events() termination | Use `_STOP_SENTINEL` for clean shutdown |

### Test Coverage Added

- Config validation tests (temperature, vad_threshold, sample_rate, etc.)
- CONNECTED event emission tests
- Reconnection event simulation tests
- Session update validation tests
- Latency simulation tests
- Text input with/without auto-response tests

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `realtimevoiceapiport_design.md` | Full design rationale |
| `../websocket_infrastructure/step_by_step_implementation.md` | WebSocket client implementation |
| `../websocket_infrastructure/what_we_are_building.md` | Infrastructure overview |
