# Grok Realtime Adapter Implementation Guide

> **Version 2.0** - Updated with fixes from `grok_critic.md`

## Problem Analysis

### Core Challenge
Build a `GrokRealtimeAdapter` that implements the `RealtimeVoiceAPIPort` interface, enabling chatforge applications to use xAI's Grok Voice Agent API interchangeably with OpenAI's Realtime API.

### Key Constraints
1. Must implement all 15+ abstract methods from `RealtimeVoiceAPIPort`
2. Must handle Grok's different message format vs OpenAI
3. Must map between `VoiceSessionConfig` and Grok's session structure
4. Must translate Grok events to normalized `VoiceEvent` types
5. Should reuse existing `WebSocketClient` infrastructure
6. Must maintain thread safety (async-safe operations)

### Critical Success Factors
1. Complete API coverage for all `RealtimeVoiceAPIPort` methods
2. Correct bidirectional event translation
3. Proper error handling with meaningful error types
4. Voice mapping that feels natural to users
5. Clean separation of concerns (adapter, messages, translator)

---

## Architecture Decision

### Recommended Approach: Mirror OpenAI Structure

```
chatforge/adapters/realtime/grok/
├── __init__.py          # Export GrokRealtimeAdapter
├── adapter.py           # Main adapter implementing RealtimeVoiceAPIPort
├── messages.py          # Message factory for client→server messages
├── translator.py        # Event translator for server→client events
└── docs/                # Documentation (existing)
    ├── 1.md
    ├── 2.md
    ├── 3.md
    ├── step_by_step_grok_rt_adapter.md
    └── grok_critic.md
```

**Rationale:**
- Proven pattern from OpenAI adapter
- Easy to maintain and compare
- Clear separation of concerns
- Differences between providers justify separate implementations over shared base class

---

## API Mapping Analysis

### Connection Details

| Aspect | OpenAI | Grok |
|--------|--------|------|
| WebSocket URL | `wss://api.openai.com/v1/realtime?model={model}` | `wss://api.x.ai/v1/realtime` |
| Auth Header | `Authorization: Bearer {key}` | `Authorization: Bearer {key}` |
| Beta Header | `OpenAI-Beta: realtime=v1` | Not required |
| Model Selection | URL parameter | Not applicable (single model) |
| Ephemeral Tokens | Not mentioned | `POST /v1/realtime/client_secrets` |

### Session Configuration Mapping

```python
# VoiceSessionConfig → OpenAI session.update
{
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "voice": "alloy",
        "instructions": "...",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500,
            "create_response": True
        },
        "tools": [...],
        "tool_choice": "auto",
        "temperature": 0.8,
        "max_response_output_tokens": 4096
    }
}

# VoiceSessionConfig → Grok session.update
{
    "type": "session.update",
    "session": {
        "voice": "Ara",
        "instructions": "...",
        "turn_detection": {
            "type": "server_vad"  # or null for manual
        },
        "audio": {
            "input": {
                "format": {
                    "type": "audio/pcm",
                    "rate": 24000
                }
            },
            "output": {
                "format": {
                    "type": "audio/pcm",
                    "rate": 24000
                }
            }
        },
        "tools": [...]
    }
}
```

### Key Format Differences

| Feature | OpenAI | Grok |
|---------|--------|------|
| Audio format | `"pcm16"` string | `{"type": "audio/pcm", "rate": 24000}` object |
| VAD config | Detailed (threshold, padding, silence) | Simple (`"server_vad"` or `null`) |
| Temperature | Supported | **Not supported** (warn if set) |
| Max tokens | Supported | **Not supported** (warn if set) |
| Modalities | In session config | In response.create |

---

## Voice Mapping

### Available Voices

| Grok Voice | Type | Tone | Suggested OpenAI Equivalent |
|------------|------|------|----------------------------|
| **Ara** (default) | Female | Warm, friendly | alloy, shimmer |
| **Rex** | Male | Confident, clear | echo |
| **Sal** | Neutral | Smooth, balanced | fable |
| **Eve** | Female | Energetic, upbeat | nova |
| **Leo** | Male | Authoritative, strong | onyx |

### Voice Mapping Strategy (Simplified)

```python
# Only support Grok voices directly - don't try to map OpenAI voices
GROK_VOICES = {"ara", "rex", "sal", "eve", "leo"}

def _map_voice(voice: str) -> str:
    """Map voice name to Grok voice."""
    normalized = voice.lower()
    if normalized in GROK_VOICES:
        return normalized.capitalize()
    if normalized == "default":
        return "Ara"
    logger.warning("Unknown voice '%s', using default 'Ara'", voice)
    return "Ara"
```

---

## Event Translation Matrix

### Client → Server Events

| chatforge Method | OpenAI Event | Grok Event | Notes |
|------------------|--------------|------------|-------|
| `connect()` | `session.update` | `session.update` | |
| `send_audio()` | `input_audio_buffer.append` | `input_audio_buffer.append` | |
| `commit_audio()` | `input_audio_buffer.commit` | `conversation.item.commit` OR `input_audio_buffer.commit` | **VAD mode dependent!** |
| `clear_audio()` | `input_audio_buffer.clear` | `input_audio_buffer.clear` | |
| `send_text()` | `conversation.item.create` | `conversation.item.create` | |
| `create_response()` | `response.create` | `response.create` | |
| `interrupt()` | `response.cancel` | `response.cancel` | **Not documented** |
| `send_tool_result()` | `conversation.item.create` | `conversation.item.create` | |
| `update_session()` | `session.update` | `session.update` | |

### Server → Client Events (FIXED)

| Grok Event | VoiceEventType | Notes |
|------------|----------------|-------|
| `conversation.created` | `SESSION_CREATED` | First event on connect |
| `session.updated` | `SESSION_UPDATED` | Ack for session.update |
| `input_audio_buffer.speech_started` | `SPEECH_STARTED` | VAD detected speech |
| `input_audio_buffer.speech_stopped` | `SPEECH_ENDED` | VAD detected silence |
| `input_audio_buffer.committed` | `AUDIO_COMMITTED` | Buffer committed |
| `input_audio_buffer.cleared` | `AUDIO_CLEARED` | Buffer cleared |
| `conversation.item.added` | `CONVERSATION_ITEM` | Message added to history |
| `conversation.item.input_audio_transcription.completed` | `INPUT_TRANSCRIPT` | User speech transcribed |
| `response.created` | `RESPONSE_STARTED` | AI starting response |
| `response.output_item.added` | `CONVERSATION_ITEM` | Response item added |
| `response.output_audio.delta` | `AUDIO_CHUNK` | Audio data chunk |
| `response.output_audio.done` | `AUDIO_DONE` | Audio stream complete |
| `response.output_audio_transcript.delta` | `TRANSCRIPT` (is_delta=True) | Transcript chunk |
| `response.output_audio_transcript.done` | `TRANSCRIPT` (is_delta=False) | **FIXED: Was TEXT_DONE** |
| `response.done` | `RESPONSE_DONE` | Full response complete |
| `response.function_call_arguments.done` | `TOOL_CALL` | Function call ready |
| `error` | `ERROR` | Error occurred |

---

## Step-by-Step Implementation

### Phase 1: Foundation (Files Setup)

#### Step 1.1: Create `__init__.py`

```python
# chatforge/adapters/realtime/grok/__init__.py
"""Grok (xAI) Realtime Voice API adapter."""

from .adapter import GrokRealtimeAdapter

__all__ = ["GrokRealtimeAdapter"]
```

#### Step 1.2: Create `messages.py` (FIXED)

```python
# chatforge/adapters/realtime/grok/messages.py
"""Grok Realtime API message factory."""

import base64
import json
import logging
from typing import Any, Literal

from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Grok native voices only - don't try to map OpenAI voices
GROK_VOICES = {"ara", "rex", "sal", "eve", "leo"}

# Valid sample rates for PCM audio
VALID_SAMPLE_RATES = {8000, 16000, 21050, 24000, 32000, 44100, 48000}

# Built-in Grok tool types (not function type)
BUILTIN_TOOLS = {"web_search", "x_search", "file_search"}

# =============================================================================
# Mapping Functions
# =============================================================================

def _map_voice(voice: str) -> str:
    """Map voice name to Grok voice."""
    normalized = voice.lower()
    if normalized in GROK_VOICES:
        return normalized.capitalize()
    if normalized == "default":
        return "Ara"
    logger.warning("Unknown voice '%s', using default 'Ara'", voice)
    return "Ara"


def _map_audio_format(format_str: str, sample_rate: int) -> dict:
    """Map audio format string to Grok format object."""
    type_map = {
        "pcm16": "audio/pcm",
        "pcm": "audio/pcm",
        "g711_ulaw": "audio/pcmu",
        "g711_alaw": "audio/pcma",
    }
    audio_type = type_map.get(format_str, "audio/pcm")

    result = {"type": audio_type}

    if audio_type == "audio/pcm":
        # Validate and adjust sample rate
        if sample_rate not in VALID_SAMPLE_RATES:
            closest = min(VALID_SAMPLE_RATES, key=lambda x: abs(x - sample_rate))
            logger.warning(
                "Invalid sample rate %d, using closest valid rate %d",
                sample_rate, closest
            )
            sample_rate = closest
        result["rate"] = sample_rate
    elif audio_type in ("audio/pcmu", "audio/pcma"):
        # G.711 is always 8kHz
        if sample_rate != 8000:
            logger.warning(
                "G.711 format always uses 8kHz sample rate, ignoring %d",
                sample_rate
            )

    return result


def _warn_ignored_parameters(config: VoiceSessionConfig) -> None:
    """Log warnings for parameters that Grok doesn't support."""
    if config.temperature != 0.8:  # default
        logger.warning("Grok API does not support temperature parameter, ignoring")
    if config.max_tokens:
        logger.warning("Grok API does not support max_tokens parameter, ignoring")
    if config.tool_choice != "auto":
        logger.warning("Grok API does not support tool_choice parameter, ignoring")
    if not config.transcription_enabled:
        logger.warning("Grok API always transcribes, cannot disable transcription")
    if config.transcription_model:
        logger.warning("Grok API does not support transcription_model, ignoring")
    if config.vad_threshold != 0.5:  # default
        logger.warning("Grok API does not support VAD threshold configuration")
    if config.vad_prefix_ms != 300:  # default
        logger.warning("Grok API does not support VAD prefix configuration")
    if config.vad_silence_ms != 500:  # default
        logger.warning("Grok API does not support VAD silence configuration")


# =============================================================================
# Client → Server Messages
# =============================================================================

def session_update(config: VoiceSessionConfig) -> dict:
    """Create session.update message for Grok."""
    # Warn about ignored parameters
    _warn_ignored_parameters(config)

    session = {
        "voice": _map_voice(config.voice),
        "audio": {
            "input": {"format": _map_audio_format(config.input_format, config.sample_rate)},
            "output": {"format": _map_audio_format(config.output_format, config.sample_rate)},
        },
    }

    # Instructions (system prompt)
    if config.system_prompt:
        session["instructions"] = config.system_prompt

    # Turn detection (VAD)
    # Note: Both "client" and "none" map to null (manual mode)
    if config.vad_mode == "server":
        session["turn_detection"] = {"type": "server_vad"}
    else:
        session["turn_detection"] = None

    # Tools (with built-in tool support)
    if config.tools:
        session["tools"] = [_tool_to_grok(t) for t in config.tools]

    # Apply provider-specific options (escape hatch)
    if config.provider_options:
        session.update(config.provider_options)

    return {"type": "session.update", "session": session}


def input_audio_buffer_append(audio: bytes) -> dict:
    """Create input_audio_buffer.append message."""
    return {
        "type": "input_audio_buffer.append",
        "audio": base64.b64encode(audio).decode("ascii"),
    }


def input_audio_buffer_commit(vad_mode: str = "server") -> dict:
    """
    Create audio commit message.

    IMPORTANT: Grok uses different commit messages depending on VAD mode:
    - Server VAD: conversation.item.commit
    - Manual/Client VAD: input_audio_buffer.commit
    """
    if vad_mode in ("client", "none"):
        # Manual VAD mode uses input_audio_buffer.commit
        return {"type": "input_audio_buffer.commit"}
    else:
        # Server VAD uses conversation.item.commit
        return {"type": "conversation.item.commit"}


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
    # If error, wrap in error structure so AI knows it failed
    if is_error:
        output = json.dumps({"error": output})

    return {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": output,
        },
    }


def response_create(
    instructions: str | None = None,
    modalities: list[str] | None = None
) -> dict:
    """Create response.create message."""
    msg: dict = {
        "type": "response.create",
        "response": {
            "modalities": modalities or ["text", "audio"],
        },
    }
    if instructions:
        msg["response"]["instructions"] = instructions
    return msg


def response_cancel(response_id: str | None = None) -> dict:
    """
    Create response.cancel message.

    WARNING: Not documented in Grok API - may not be supported.
    """
    msg = {"type": "response.cancel"}
    if response_id:
        msg["response_id"] = response_id
    return msg


# =============================================================================
# Helpers
# =============================================================================

def _tool_to_grok(tool: ToolDefinition) -> dict:
    """Convert ToolDefinition to Grok format."""
    # Check for built-in Grok tools
    if tool.name in BUILTIN_TOOLS:
        result = {"type": tool.name}

        # Add tool-specific parameters
        if tool.name == "x_search" and tool.parameters.get("allowed_x_handles"):
            result["allowed_x_handles"] = tool.parameters["allowed_x_handles"]
        elif tool.name == "file_search":
            if tool.parameters.get("vector_store_ids"):
                result["vector_store_ids"] = tool.parameters["vector_store_ids"]
            if tool.parameters.get("max_num_results"):
                result["max_num_results"] = tool.parameters["max_num_results"]

        return result

    # Regular function tool
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
```

#### Step 1.3: Create `translator.py` (FIXED)

```python
# chatforge/adapters/realtime/grok/translator.py
"""Translate Grok events to normalized VoiceEvent."""

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


def _safe_json_parse(s: str) -> Any:
    """Safely parse JSON, returning original string on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


def translate_event(raw: dict) -> VoiceEvent | None:
    """
    Translate Grok event to VoiceEvent.

    Returns None for events we don't care about.
    """
    event_type = raw.get("type", "")

    # =========================================================================
    # Session Events
    # =========================================================================

    if event_type == "conversation.created":
        # Grok sends this first instead of session.created
        return VoiceEvent(
            type=VoiceEventType.SESSION_CREATED,
            data=raw.get("conversation"),
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

    if event_type == "response.output_audio.delta":
        audio_data = _safe_base64_decode(raw.get("delta", ""))
        if audio_data is None:
            return None
        return VoiceEvent(
            type=VoiceEventType.AUDIO_CHUNK,
            data=audio_data,
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "output_index": raw.get("output_index"),
                "content_index": raw.get("content_index"),
            },
            raw_event=raw,
        )

    if event_type == "response.output_audio.done":
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
            metadata={
                "item_id": raw.get("item_id"),
                "previous_item_id": raw.get("previous_item_id"),
            },
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
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.speech_stopped":
        return VoiceEvent(
            type=VoiceEventType.SPEECH_ENDED,
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Text/Transcript Events (FIXED: Both map to TRANSCRIPT)
    # =========================================================================

    if event_type == "response.output_audio_transcript.delta":
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

    if event_type == "response.output_audio_transcript.done":
        # FIXED: Was TEXT_DONE, should be TRANSCRIPT with is_delta=False
        return VoiceEvent(
            type=VoiceEventType.TRANSCRIPT,
            data=raw.get("transcript", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "is_delta": False,  # Final transcript
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
        response = raw.get("response", {})
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_STARTED,
            metadata={"response_id": response.get("id")},
            raw_event=raw,
        )

    if event_type == "response.done":
        response = raw.get("response", {})
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_DONE,
            data={
                "status": response.get("status"),
            },
            metadata={"response_id": response.get("id")},
            raw_event=raw,
        )

    if event_type == "response.output_item.added":
        return VoiceEvent(
            type=VoiceEventType.CONVERSATION_ITEM,
            data=raw.get("item"),
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

    if event_type == "conversation.item.added":
        return VoiceEvent(
            type=VoiceEventType.CONVERSATION_ITEM,
            data=raw.get("item"),
            metadata={"previous_item_id": raw.get("previous_item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Error Events (FIXED: Defensive handling)
    # =========================================================================

    if event_type == "error":
        # Handle both nested and flat error formats
        error = raw.get("error", raw)
        return VoiceEvent(
            type=VoiceEventType.ERROR,
            data={
                "code": error.get("code") or error.get("error_code"),
                "message": error.get("message") or error.get("error_message") or str(error),
                "type": error.get("type") or error.get("error_type"),
            },
            raw_event=raw,
        )

    # Unknown event - log at debug level and return None
    logger.debug("Unhandled Grok event: %s", event_type)
    return None
```

### Phase 2: Core Adapter Implementation (FIXED)

#### Step 2.1: Create `adapter.py`

```python
# chatforge/adapters/realtime/grok/adapter.py
"""Grok (xAI) Realtime API adapter using shared WebSocket infrastructure."""

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

# Grok Realtime API constants
GROK_REALTIME_URL = "wss://api.x.ai/v1/realtime"
GROK_EPHEMERAL_TOKEN_URL = "https://api.x.ai/v1/realtime/client_secrets"

# Sentinel value for stopping the event generator
_STOP_SENTINEL = object()

# Event queue size limit
_EVENT_QUEUE_MAX_SIZE = 1000


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
        if not api_key and not ephemeral_token:
            raise ValueError("Either api_key or ephemeral_token is required")

        self._auth_token = ephemeral_token or api_key
        self._api_key = api_key  # Keep for ephemeral token refresh
        self._connect_timeout = connect_timeout
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._enable_metrics = enable_metrics

        self._ws: WebSocketClient | None = None
        self._config: VoiceSessionConfig | None = None
        self._session_ready = asyncio.Event()
        self._session_configured = asyncio.Event()  # NEW: Wait for session.updated
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
        # FIXED: Use correct commit message based on VAD mode
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
        # FIXED: Pass modalities from config
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
```

### Phase 3: Integration

#### Step 3.1: Update parent `__init__.py`

```python
# chatforge/adapters/realtime/__init__.py
"""Realtime voice API adapters."""

from .openai import OpenAIRealtimeAdapter
from .mock import MockRealtimeAdapter
from .grok import GrokRealtimeAdapter

__all__ = [
    "OpenAIRealtimeAdapter",
    "MockRealtimeAdapter",
    "GrokRealtimeAdapter",
]
```

---

## Testing Strategy

### Unit Tests

1. **messages.py tests**
   - Test voice mapping for all Grok voices
   - Test voice mapping rejects unknown voices with warning
   - Test audio format mapping (pcm16, g711)
   - Test sample rate validation
   - Test session_update message structure
   - Test built-in tool conversion (web_search, x_search, file_search)
   - Test function tool conversion
   - Test is_error parameter wraps error in JSON

2. **translator.py tests**
   - Test each event type translation
   - Test transcript.done maps to TRANSCRIPT (not TEXT_DONE)
   - Test unknown event handling (should return None)
   - Test malformed event handling
   - Test base64 decode error handling
   - Test defensive error parsing

3. **adapter.py tests**
   - Test connection lifecycle
   - Test session ready sequencing
   - Test commit_audio uses correct message per VAD mode
   - Test create_response passes modalities
   - Test ephemeral token factory method
   - Test reconnection behavior
   - Test event queue behavior

### Integration Tests

```python
# test_grok_integration.py
import asyncio
import os
import pytest

from chatforge.adapters.realtime import GrokRealtimeAdapter
from chatforge.ports.realtime_voice import VoiceSessionConfig, VoiceEventType

@pytest.mark.skipif(
    not os.getenv("XAI_API_KEY"),
    reason="XAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_grok_connection():
    """Test basic connection to Grok API."""
    async with GrokRealtimeAdapter(api_key=os.getenv("XAI_API_KEY")) as adapter:
        config = VoiceSessionConfig(
            voice="Ara",
            system_prompt="You are a helpful assistant.",
            vad_mode="server",
        )
        await adapter.connect(config)
        assert adapter.is_connected()

        # Send text and get response
        await adapter.send_text("Hello")

        # Collect events until response done
        events = []
        async for event in adapter.events():
            events.append(event)
            if event.type == VoiceEventType.RESPONSE_DONE:
                break

        assert any(e.type == VoiceEventType.AUDIO_CHUNK for e in events)
        assert any(e.type == VoiceEventType.TRANSCRIPT for e in events)

        # Verify transcript events have is_delta metadata
        transcripts = [e for e in events if e.type == VoiceEventType.TRANSCRIPT]
        assert all("is_delta" in e.metadata for e in transcripts)


@pytest.mark.asyncio
async def test_ephemeral_token():
    """Test ephemeral token creation."""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        pytest.skip("XAI_API_KEY not set")

    adapter = await GrokRealtimeAdapter.with_ephemeral_token(api_key)
    assert adapter._auth_token is not None
    assert adapter._auth_token != api_key  # Should be different
```

---

## Known Limitations & Workarounds

### 1. Response Interruption (Barge-in)
**Issue:** `response.cancel` not documented
**Workaround:** Log warning, send anyway (might work), or disconnect/reconnect

### 2. Conversation Reset
**Issue:** `conversation.item.delete` not documented
**Workaround:** Raise `NotImplementedError`, suggest disconnect/reconnect

### 3. Temperature/Max Tokens
**Issue:** Not documented in session config
**Workaround:** Log warning when set, ignore parameter

### 4. VAD Configuration
**Issue:** No threshold/padding/silence settings like OpenAI
**Workaround:** Log warning when non-default values set, only support on/off

### 5. Model Selection
**Issue:** No model parameter in API
**Workaround:** Return empty list in capabilities, ignore `config.model`

### 6. Transcription Control
**Issue:** Cannot disable transcription
**Workaround:** Log warning when `transcription_enabled=False`

---

## Implementation Checklist (Updated)

- [ ] Create `grok/__init__.py`
- [ ] Create `grok/messages.py`
  - [ ] Voice mapping (Grok voices only, warn on unknown)
  - [ ] Audio format mapping with sample rate validation
  - [ ] Warn on ignored parameters
  - [ ] session_update with provider_options support
  - [ ] input_audio_buffer_append
  - [ ] input_audio_buffer_commit (VAD mode aware!)
  - [ ] input_audio_buffer_clear
  - [ ] conversation_item_create_message
  - [ ] conversation_item_create_tool_result (use is_error!)
  - [ ] response_create (with modalities parameter!)
  - [ ] response_cancel (with response_id parameter)
  - [ ] Built-in tool support (web_search, x_search, file_search)
- [ ] Create `grok/translator.py`
  - [ ] Session events (conversation.created, session.updated)
  - [ ] Audio output events (response.output_audio.delta/done)
  - [ ] Audio input events (speech_started/stopped, committed, cleared)
  - [ ] Transcript events (both delta and done → TRANSCRIPT!)
  - [ ] Response lifecycle events (created, done, output_item.added)
  - [ ] Tool calling events (function_call_arguments.done)
  - [ ] Error events (defensive parsing)
- [ ] Create `grok/adapter.py`
  - [ ] Constructor with api_key OR ephemeral_token
  - [ ] with_ephemeral_token() factory method
  - [ ] connect() with proper session sequencing
  - [ ] disconnect() with cleanup
  - [ ] send_audio()
  - [ ] commit_audio() (VAD mode aware!)
  - [ ] clear_audio()
  - [ ] send_text(), add_text_item()
  - [ ] create_response() (with modalities!)
  - [ ] interrupt() with warning
  - [ ] cancel_response() with response_id
  - [ ] send_tool_result() (is_error works!)
  - [ ] update_session()
  - [ ] reset_conversation() raises NotImplementedError
  - [ ] events() generator
  - [ ] get_capabilities() (empty models list)
  - [ ] get_stats()
- [ ] Update `realtime/__init__.py`
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with real xAI API key
- [ ] Document discovered differences

---

## Estimated Effort (Revised)

| Phase | Effort |
|-------|--------|
| Phase 1: Foundation (messages.py, translator.py) | ~3-4 hours |
| Phase 2: Core Adapter | ~3-4 hours |
| Phase 3: Integration & Testing | ~2-3 hours |
| Phase 4: Real API Testing & Fixes | ~2-3 hours |
| **Total** | **~10-14 hours** |

---

## Fixes Applied from Critic

| Issue | Fix Applied |
|-------|-------------|
| Audio commit VAD mode | `input_audio_buffer_commit(vad_mode)` parameter added |
| Transcript event type | Both delta and done → `TRANSCRIPT` with `is_delta` flag |
| is_error unused | Wraps error in `{"error": ...}` JSON structure |
| provider_options ignored | Applied in `session_update()` |
| Built-in tools not supported | Special handling for web_search, x_search, file_search |
| Sample rate validation | Validates against `VALID_SAMPLE_RATES`, auto-corrects |
| Session ready race condition | Separate `_session_ready` and `_session_configured` events |
| Ephemeral tokens missing | Added `with_ephemeral_token()` factory method |
| Silently ignored parameters | Added `_warn_ignored_parameters()` function |
| Modalities hardcoded | Pass from config in `create_response()` |
| Error event format | Defensive parsing with fallbacks |
| response_cancel no response_id | Added optional `response_id` parameter |
| G.711 sample rate | Logs warning if non-8kHz rate specified |

---

## Success Metrics

1. All `RealtimeVoiceAPIPort` methods implemented
2. Basic voice conversation works end-to-end
3. Tool calling works (including built-in tools)
4. Transcription (input + output) works correctly
5. VAD (server-side) works
6. Manual VAD mode works with correct commit message
7. Ephemeral tokens work for client-side apps
8. Graceful handling of unsupported features with clear warnings
9. Clear error messages for limitations
