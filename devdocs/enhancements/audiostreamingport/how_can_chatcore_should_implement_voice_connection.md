# How Chatforge Should Implement Voice Connection

*Deep analysis of voice API connection architecture options for Chatforge.*

---

## Executive Summary

**Recommendation**: Use a single `RealtimeVoiceAPIPort` interface with internal composition.

- Port defines provider-agnostic contract
- Each adapter (OpenAI, Anthropic, etc.) handles transport internally
- Normalized `VoiceEvent` types for consistent VoiceAgent integration
- WebSocket/gRPC/HTTP are implementation details, not separate ports

---

## Context: What realtimevoiceapi Already Has

Based on analysis of `/Users/ns/Desktop/projects/realtimevoiceapi/realtimevoiceapi`:

| Component | Description | Reuse? |
|-----------|-------------|--------|
| `WebSocketConnection` | Provider-agnostic WebSocket with reconnect, metrics | Yes (as internal utility) |
| `IVoiceProvider` protocol | Provider abstraction | Simplify for Chatforge |
| `IProviderSession` protocol | Session abstraction | Absorb into RealtimeVoiceAPIPort |
| `MessageFactory` | OpenAI message builders | Yes (in OpenAI adapter) |
| `ProviderCapabilities` | Feature discovery | Yes (simplified) |
| `FastLane/BigLane` | Dual-mode architecture | No (Chatforge uses single mode) |
| `EventBus` | Complex event routing | No (overkill for Chatforge) |
| `StreamOrchestrator` | Multi-provider orchestration | No (future consideration) |

---

## The Core Question

How should Chatforge abstract voice API connections while:
1. Supporting multiple providers (OpenAI, Anthropic, Google, Twilio)
2. Hiding transport details (WebSocket, gRPC, HTTP/SSE)
3. Maintaining hexagonal architecture purity
4. Adding minimal latency (<10ms overhead)
5. Enabling easy testing

---

## Architecture Options Analyzed

### Option A: Single Monolithic RealtimeVoiceAPIPort

```
┌─────────────────────────────────────────┐
│              RealtimeVoiceAPIPort               │
│  (handles everything: WS + messages)    │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   OpenAI       Anthropic    Google
   Adapter      Adapter      Adapter
   (has WS)     (has WS)     (has gRPC)
```

Each adapter implements the full port contract and manages its own transport.

```python
class RealtimeVoiceAPIPort(ABC):
    @abstractmethod
    async def connect(self, config: SessionConfig) -> None: ...

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None: ...

    @abstractmethod
    async def events(self) -> AsyncGenerator[RealtimeEvent, None]: ...


class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self):
        self._ws = None  # WebSocket handled internally

    async def connect(self, config):
        self._ws = await websockets.connect(OPENAI_URL)
```

| Pros | Cons |
|------|------|
| Simple interface | Transport logic duplicated per adapter |
| Clear contract | Can't share WebSocket code easily |
| Easy to understand | Larger adapter implementations |

**Verdict**: Good for MVP, but repetitive with many providers.

---

### Option B: WebSocketPort + RealtimeVoiceAPIPort (Layered)

```
┌─────────────────────────────────────────┐
│              RealtimeVoiceAPIPort               │
│         (voice-specific logic)          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│             WebSocketPort               │
│           (low-level transport)         │
└─────────────────────────────────────────┘
```

Separate port for WebSocket, RealtimeVoiceAPIPort uses it.

```python
class WebSocketPort(ABC):
    @abstractmethod
    async def connect(self, url: str, headers: dict) -> None: ...

    @abstractmethod
    async def send(self, data: bytes | str) -> None: ...

    @abstractmethod
    async def receive(self) -> AsyncGenerator[bytes | str, None]: ...


class RealtimeVoiceAPIPort(ABC):
    def __init__(self, ws: WebSocketPort): ...
```

**Problem**: Not all providers use WebSocket!

- OpenAI: WebSocket
- Google: gRPC streaming
- Some providers: HTTP/SSE

Would need: `WebSocketPort`, `GrpcPort`, `HttpStreamPort`...

| Pros | Cons |
|------|------|
| Reusable transport layers | Over-abstraction |
| Clean separation | Leaky abstraction (port knows transport) |
| | Complex dependency injection |
| | Different ports for different providers |

**Verdict**: Over-engineered. Transport is implementation detail.

---

### Option C: RealtimeVoiceAPIPort with Internal Composition (RECOMMENDED)

```
┌─────────────────────────────────────────┐
│              RealtimeVoiceAPIPort               │
│       (provider-agnostic interface)     │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   OpenAI    │ │  Anthropic  │ │   Google    │
│   Adapter   │ │   Adapter   │ │   Adapter   │
│ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │
│ │   WS    │ │ │ │   WS    │ │ │ │  gRPC   │ │
│ │(internal)│ │ │ │(internal)│ │ │ │(internal)│ │
│ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │
└─────────────┘ └─────────────┘ └─────────────┘
```

- Port defines the contract (provider-agnostic)
- Each adapter handles transport internally (composition, not inheritance)
- Transport utilities can be shared as internal code, not ports

| Pros | Cons |
|------|------|
| Clean hexagonal boundary | Adapters have internal complexity |
| Transport hidden from port | Need event translator per provider |
| Normalized events | |
| Testable with mock adapter | |
| Share WebSocket code internally | |

**Verdict**: Best balance of clean architecture and practicality.

---

### Option D: Provider-Specific Ports

```python
class OpenAIRealtimeVoiceAPIPort(ABC): ...
class AnthropicRealtimeVoiceAPIPort(ABC): ...
class GoogleRealtimeVoiceAPIPort(ABC): ...
```

Each with provider-specific methods and events.

| Pros | Cons |
|------|------|
| Maximum provider fidelity | VoiceAgent must handle each differently |
| Access to all features | No code reuse |
| | Breaks hexagonal pattern |
| | Domain layer knows about providers |

**Verdict**: Anti-pattern. Violates hexagonal architecture.

---

## Recommended Architecture: Option C

### Layer Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          VoiceAgent                               │
│              (coordinates audio + realtime + tools)               │
└──────────────────────────────────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  AudioStreamPort │   │   RealtimeVoiceAPIPort   │   │    TicketingPort    │
│   (interface)    │   │   (interface)    │   │   (existing)     │
└────────┬─────────┘   └────────┬─────────┘   └──────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌────────────────────────────────────────────┐
│ VoxStreamAdapter │   │          OpenAIRealtimeAdapter             │
│                  │   │  ┌──────────────────────────────────────┐  │
└──────────────────┘   │  │    WebSocketConnection (internal)    │  │
                       │  └──────────────────────────────────────┘  │
                       │  ┌──────────────────────────────────────┐  │
                       │  │   OpenAIEventTranslator (internal)   │  │
                       │  └──────────────────────────────────────┘  │
                       │  ┌──────────────────────────────────────┐  │
                       │  │   OpenAIMessageFactory (internal)    │  │
                       │  └──────────────────────────────────────┘  │
                       └────────────────────────────────────────────┘
```

### Key Insight

**WebSocket is not a port. It's an implementation detail.**

The `WebSocketConnection` class from realtimevoiceapi becomes an internal utility that adapters use, not a Chatforge port. This is composition, not abstraction.

---

## Port Interface Design

### RealtimeVoiceAPIPort

```python
# chatforge/ports/realtime.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Any

class VoiceEventType(str, Enum):
    """Provider-agnostic voice events."""

    # Connection lifecycle
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Audio streaming
    AUDIO_CHUNK = "audio.chunk"           # AI audio response chunk
    AUDIO_COMMITTED = "audio.committed"   # User audio buffer committed

    # Text streaming
    TEXT_CHUNK = "text.chunk"             # AI text response chunk
    TRANSCRIPT = "transcript"             # User speech transcription

    # Speech detection
    SPEECH_STARTED = "speech.started"     # User started speaking
    SPEECH_ENDED = "speech.ended"         # User stopped speaking

    # Response lifecycle
    RESPONSE_STARTED = "response.started"
    RESPONSE_DONE = "response.done"

    # Tool calling
    TOOL_CALL = "tool.call"               # AI wants to call a tool

    # Session
    SESSION_UPDATED = "session.updated"


@dataclass
class VoiceEvent:
    """Normalized voice event."""
    type: VoiceEventType
    data: bytes | str | dict | None = None
    metadata: dict = field(default_factory=dict)
    raw_event: Any = None  # Original provider event (for debugging)


@dataclass
class ProviderCapabilities:
    """What this provider supports."""
    provider_name: str
    supports_server_vad: bool = True
    supports_client_vad: bool = False
    supports_function_calling: bool = True
    supports_interruption: bool = True
    available_voices: list[str] = field(default_factory=list)
    supported_audio_formats: list[str] = field(default_factory=lambda: ["pcm16"])
    supported_sample_rates: list[int] = field(default_factory=lambda: [24000])


@dataclass
class VoiceSessionConfig:
    """Provider-agnostic session configuration."""

    # Model (provider resolves to actual model ID)
    model: str = "default"

    # Voice
    voice: str = "default"

    # Behavior
    system_prompt: str | None = None
    temperature: float = 0.8

    # Audio format
    input_format: str = "pcm16"
    output_format: str = "pcm16"
    sample_rate: int = 24000

    # VAD configuration
    vad_mode: str = "server"  # "server", "client", "none"
    silence_threshold_ms: int = 500

    # Tools (OpenAI function calling format)
    tools: list[dict] | None = None
    tool_choice: str = "auto"  # "auto", "none", "required"


class RealtimeVoiceAPIPort(ABC):
    """
    Port for real-time voice AI API connections.

    Provider-agnostic interface. Each adapter handles
    its own transport (WebSocket, gRPC, etc.) internally.
    """

    # === Connection Lifecycle ===

    @abstractmethod
    async def connect(self, config: VoiceSessionConfig) -> None:
        """
        Connect to the voice API.

        Args:
            config: Session configuration.

        Raises:
            ConnectionError: If connection fails.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the API."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        ...

    # === Audio Streaming ===

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """
        Send audio chunk to API.

        Args:
            chunk: PCM16 audio bytes.
        """
        ...

    @abstractmethod
    async def commit_audio(self) -> None:
        """
        Manually commit audio buffer.

        Used when vad_mode is "client" or "none".
        """
        ...

    @abstractmethod
    async def clear_audio(self) -> None:
        """Clear the audio input buffer."""
        ...

    # === Response Control ===

    @abstractmethod
    async def interrupt(self) -> None:
        """
        Interrupt current AI response.

        Used for barge-in (user starts speaking while AI is responding).
        """
        ...

    @abstractmethod
    async def create_response(
        self,
        instructions: str | None = None,
    ) -> None:
        """
        Manually trigger a response.

        Used when vad_mode is "none" or for text-triggered responses.
        """
        ...

    # === Tool Calling ===

    @abstractmethod
    async def send_tool_result(
        self,
        call_id: str,
        result: str,
    ) -> None:
        """
        Send tool call result back to API.

        Args:
            call_id: The tool call ID from TOOL_CALL event.
            result: JSON string of the tool result.
        """
        ...

    # === Event Stream ===

    @abstractmethod
    def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """
        Stream of events from the API.

        Yields:
            VoiceEvent instances (normalized, provider-agnostic).
        """
        ...

    # === Capabilities ===

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get this provider's capabilities."""
        ...

    # === Session Update ===

    @abstractmethod
    async def update_session(
        self,
        config: VoiceSessionConfig,
    ) -> None:
        """
        Update session configuration mid-conversation.

        Not all fields may be updatable mid-session.
        """
        ...
```

---

## Adapter Implementation Pattern

### OpenAI Realtime Adapter

```python
# chatforge/adapters/realtime/openai/adapter.py

import base64
import json
from typing import AsyncGenerator

from chatforge.ports.realtime import (
    RealtimeVoiceAPIPort,
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    ProviderCapabilities,
)
from .websocket import WebSocketConnection
from .translator import OpenAIEventTranslator
from .messages import OpenAIMessageFactory


class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    RealtimeVoiceAPIPort implementation for OpenAI Realtime API.

    Transport (WebSocket) is handled internally.
    """

    OPENAI_URL = "wss://api.openai.com/v1/realtime"

    def __init__(self, api_key: str):
        self._api_key = api_key

        # Internal components (not ports)
        self._connection = WebSocketConnection()
        self._translator = OpenAIEventTranslator()
        self._messages = OpenAIMessageFactory()

        self._connected = False

    # === Connection Lifecycle ===

    async def connect(self, config: VoiceSessionConfig) -> None:
        model = self._resolve_model(config.model)
        url = f"{self.OPENAI_URL}?model={model}"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        await self._connection.connect(url, headers)
        self._connected = True

        # Send session configuration
        session_msg = self._messages.session_update(
            self._to_openai_config(config)
        )
        await self._connection.send(json.dumps(session_msg))

    async def disconnect(self) -> None:
        await self._connection.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._connection.is_connected()

    # === Audio Streaming ===

    async def send_audio(self, chunk: bytes) -> None:
        msg = self._messages.input_audio_buffer_append(
            base64.b64encode(chunk).decode()
        )
        await self._connection.send(json.dumps(msg))

    async def commit_audio(self) -> None:
        msg = self._messages.input_audio_buffer_commit()
        await self._connection.send(json.dumps(msg))

    async def clear_audio(self) -> None:
        msg = self._messages.input_audio_buffer_clear()
        await self._connection.send(json.dumps(msg))

    # === Response Control ===

    async def interrupt(self) -> None:
        msg = self._messages.response_cancel()
        await self._connection.send(json.dumps(msg))

    async def create_response(self, instructions: str | None = None) -> None:
        msg = self._messages.response_create(instructions=instructions)
        await self._connection.send(json.dumps(msg))

    # === Tool Calling ===

    async def send_tool_result(self, call_id: str, result: str) -> None:
        msg = self._messages.conversation_item_create(
            item_type="function_call_output",
            call_id=call_id,
            output=result,
        )
        await self._connection.send(json.dumps(msg))

        # Trigger response after tool result
        await self.create_response()

    # === Event Stream ===

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        async for raw_msg in self._connection.receive():
            data = json.loads(raw_msg)
            event = self._translator.translate(data)
            if event:
                yield event

    # === Capabilities ===

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="openai",
            supports_server_vad=True,
            supports_client_vad=True,
            supports_function_calling=True,
            supports_interruption=True,
            available_voices=[
                "alloy", "ash", "ballad", "coral",
                "echo", "sage", "shimmer", "verse",
            ],
            supported_audio_formats=["pcm16", "g711_ulaw", "g711_alaw"],
            supported_sample_rates=[24000],
        )

    # === Session Update ===

    async def update_session(self, config: VoiceSessionConfig) -> None:
        msg = self._messages.session_update(
            self._to_openai_config(config)
        )
        await self._connection.send(json.dumps(msg))

    # === Internal Helpers ===

    def _resolve_model(self, model: str) -> str:
        if model == "default":
            return "gpt-4o-realtime-preview-2024-12-17"
        return model

    def _to_openai_config(self, config: VoiceSessionConfig) -> dict:
        """Translate VoiceSessionConfig to OpenAI format."""
        result = {
            "modalities": ["text", "audio"],
            "voice": config.voice if config.voice != "default" else "alloy",
            "input_audio_format": config.input_format,
            "output_audio_format": config.output_format,
            "temperature": config.temperature,
        }

        if config.system_prompt:
            result["instructions"] = config.system_prompt

        if config.vad_mode == "server":
            result["turn_detection"] = {
                "type": "server_vad",
                "silence_duration_ms": config.silence_threshold_ms,
                "threshold": 0.5,
                "prefix_padding_ms": 300,
            }
        else:
            result["turn_detection"] = None

        if config.tools:
            result["tools"] = config.tools
            result["tool_choice"] = config.tool_choice

        return result
```

### Event Translator

```python
# chatforge/adapters/realtime/openai/translator.py

import base64
import json
from chatforge.ports.realtime import VoiceEvent, VoiceEventType


class OpenAIEventTranslator:
    """Translates OpenAI Realtime API events to Chatforge VoiceEvents."""

    def translate(self, raw: dict) -> VoiceEvent | None:
        """
        Translate OpenAI event to normalized VoiceEvent.

        Returns None for events we don't care about.
        """
        event_type = raw.get("type", "")

        # Audio response
        if event_type == "response.audio.delta":
            return VoiceEvent(
                type=VoiceEventType.AUDIO_CHUNK,
                data=base64.b64decode(raw.get("delta", "")),
                metadata={"response_id": raw.get("response_id")},
                raw_event=raw,
            )

        # Text response
        if event_type == "response.text.delta":
            return VoiceEvent(
                type=VoiceEventType.TEXT_CHUNK,
                data=raw.get("delta", ""),
                metadata={"response_id": raw.get("response_id")},
                raw_event=raw,
            )

        # Transcript of user speech
        if event_type == "conversation.item.input_audio_transcription.completed":
            return VoiceEvent(
                type=VoiceEventType.TRANSCRIPT,
                data=raw.get("transcript", ""),
                raw_event=raw,
            )

        # Speech detection
        if event_type == "input_audio_buffer.speech_started":
            return VoiceEvent(
                type=VoiceEventType.SPEECH_STARTED,
                raw_event=raw,
            )

        if event_type == "input_audio_buffer.speech_stopped":
            return VoiceEvent(
                type=VoiceEventType.SPEECH_ENDED,
                raw_event=raw,
            )

        # Audio committed
        if event_type == "input_audio_buffer.committed":
            return VoiceEvent(
                type=VoiceEventType.AUDIO_COMMITTED,
                raw_event=raw,
            )

        # Response lifecycle
        if event_type == "response.created":
            return VoiceEvent(
                type=VoiceEventType.RESPONSE_STARTED,
                metadata={"response_id": raw.get("response", {}).get("id")},
                raw_event=raw,
            )

        if event_type == "response.done":
            return VoiceEvent(
                type=VoiceEventType.RESPONSE_DONE,
                metadata={"response_id": raw.get("response", {}).get("id")},
                raw_event=raw,
            )

        # Tool calling
        if event_type == "response.function_call_arguments.done":
            return VoiceEvent(
                type=VoiceEventType.TOOL_CALL,
                data={
                    "call_id": raw.get("call_id"),
                    "name": raw.get("name"),
                    "arguments": json.loads(raw.get("arguments", "{}")),
                },
                raw_event=raw,
            )

        # Session events
        if event_type in ("session.created", "session.updated"):
            return VoiceEvent(
                type=VoiceEventType.SESSION_UPDATED,
                metadata=raw.get("session", {}),
                raw_event=raw,
            )

        # Errors
        if event_type == "error":
            return VoiceEvent(
                type=VoiceEventType.ERROR,
                data=raw.get("error", {}),
                raw_event=raw,
            )

        # Unknown event - ignore
        return None
```

### Internal WebSocket (Not a Port)

```python
# chatforge/adapters/realtime/openai/websocket.py

import asyncio
from typing import AsyncGenerator
import websockets


class WebSocketConnection:
    """
    Internal WebSocket utility.

    NOT a port - this is an implementation detail
    used by adapters that need WebSocket transport.
    """

    def __init__(self):
        self._ws = None
        self._connected = False

    async def connect(self, url: str, headers: dict) -> None:
        self._ws = await websockets.connect(
            url,
            extra_headers=headers,
            ping_interval=20,
            ping_timeout=10,
        )
        self._connected = True

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._ws and not self._ws.closed

    async def send(self, message: str) -> None:
        if not self._ws:
            raise ConnectionError("Not connected")
        await self._ws.send(message)

    async def receive(self) -> AsyncGenerator[str, None]:
        if not self._ws:
            raise ConnectionError("Not connected")

        try:
            async for message in self._ws:
                yield message
        except websockets.ConnectionClosed:
            self._connected = False
```

---

## Mock Adapter for Testing

```python
# chatforge/adapters/realtime/mock.py

from typing import AsyncGenerator
from chatforge.ports.realtime import (
    RealtimeVoiceAPIPort,
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    ProviderCapabilities,
)


class MockRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    Mock adapter for testing VoiceAgent without real API.

    Can be configured to emit specific event sequences.
    """

    def __init__(self):
        self._connected = False
        self._events_queue: list[VoiceEvent] = []
        self._audio_sent: list[bytes] = []
        self._tool_results: list[tuple[str, str]] = []

    # === Test Helpers ===

    def queue_event(self, event: VoiceEvent) -> None:
        """Queue an event to be emitted."""
        self._events_queue.append(event)

    def queue_audio_response(self, audio: bytes) -> None:
        """Queue an audio response."""
        self.queue_event(VoiceEvent(
            type=VoiceEventType.RESPONSE_STARTED,
        ))
        self.queue_event(VoiceEvent(
            type=VoiceEventType.AUDIO_CHUNK,
            data=audio,
        ))
        self.queue_event(VoiceEvent(
            type=VoiceEventType.RESPONSE_DONE,
        ))

    def get_sent_audio(self) -> list[bytes]:
        """Get all audio that was sent."""
        return self._audio_sent

    def get_tool_results(self) -> list[tuple[str, str]]:
        """Get all tool results that were sent."""
        return self._tool_results

    # === RealtimeVoiceAPIPort Implementation ===

    async def connect(self, config: VoiceSessionConfig) -> None:
        self._connected = True
        self.queue_event(VoiceEvent(type=VoiceEventType.CONNECTED))

    async def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def send_audio(self, chunk: bytes) -> None:
        self._audio_sent.append(chunk)

    async def commit_audio(self) -> None:
        self.queue_event(VoiceEvent(type=VoiceEventType.AUDIO_COMMITTED))

    async def clear_audio(self) -> None:
        pass

    async def interrupt(self) -> None:
        pass

    async def create_response(self, instructions: str | None = None) -> None:
        pass

    async def send_tool_result(self, call_id: str, result: str) -> None:
        self._tool_results.append((call_id, result))

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        while self._connected:
            if self._events_queue:
                yield self._events_queue.pop(0)
            else:
                await asyncio.sleep(0.01)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="mock",
            supports_server_vad=True,
            supports_function_calling=True,
        )

    async def update_session(self, config: VoiceSessionConfig) -> None:
        pass
```

---

## Adding a New Provider

When Anthropic releases their real-time voice API:

### Step 1: Create Adapter Directory

```
chatforge/adapters/realtime/anthropic/
├── __init__.py
├── adapter.py       # AnthropicRealtimeAdapter
├── translator.py    # AnthropicEventTranslator
└── messages.py      # Anthropic message builders
```

### Step 2: Implement Adapter

```python
# chatforge/adapters/realtime/anthropic/adapter.py

class AnthropicRealtimeAdapter(RealtimeVoiceAPIPort):
    """RealtimeVoiceAPIPort for Anthropic's voice API."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        # Anthropic might use WebSocket, SSE, or something else
        # Handle transport internally

    async def connect(self, config: VoiceSessionConfig) -> None:
        # Anthropic-specific connection logic
        ...

    async def send_audio(self, chunk: bytes) -> None:
        # Anthropic-specific audio format
        ...

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        # Translate Anthropic events to VoiceEvent
        ...

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="anthropic",
            supports_server_vad=True,  # If they support it
            supports_function_calling=True,
            available_voices=["claude-voice-1", ...],
        )
```

### Step 3: Register in Factory

```python
# chatforge/adapters/realtime/__init__.py

def create_realtime_adapter(
    provider: str,
    api_key: str,
) -> RealtimeVoiceAPIPort:
    match provider:
        case "openai":
            from .openai import OpenAIRealtimeAdapter
            return OpenAIRealtimeAdapter(api_key)
        case "anthropic":
            from .anthropic import AnthropicRealtimeAdapter
            return AnthropicRealtimeAdapter(api_key)
        case "mock":
            from .mock import MockRealtimeAdapter
            return MockRealtimeAdapter()
        case _:
            raise ValueError(f"Unknown provider: {provider}")
```

---

## VoiceAgent Integration

```python
# chatforge/agent/voice.py

class VoiceAgent:
    def __init__(
        self,
        audio: AudioStreamPort,
        realtime: RealtimeVoiceAPIPort,
        actions: TicketingPort | None = None,
    ):
        self.audio = audio
        self.realtime = realtime
        self.actions = actions

    async def start(self, config: VoiceSessionConfig) -> None:
        # Check capabilities
        caps = self.realtime.get_capabilities()

        # Connect to API
        await self.realtime.connect(config)

        # Configure VAD based on provider capabilities
        if config.vad_mode == "server" and not caps.supports_server_vad:
            # Fall back to client VAD
            self.audio.set_vad_callbacks(
                on_speech_end=self._on_speech_end,
            )

        # Start pipelines
        asyncio.create_task(self._capture_loop())
        asyncio.create_task(self._event_loop())

    async def _capture_loop(self) -> None:
        async for chunk in self.audio.start_capture():
            await self.realtime.send_audio(chunk)

    async def _event_loop(self) -> None:
        async for event in self.realtime.events():
            match event.type:
                case VoiceEventType.AUDIO_CHUNK:
                    await self.audio.play_chunk(event.data)

                case VoiceEventType.SPEECH_STARTED:
                    # Barge-in: stop playback, interrupt AI
                    await self.audio.stop_playback()
                    await self.realtime.interrupt()

                case VoiceEventType.TOOL_CALL:
                    # Execute tool via TicketingPort
                    result = await self._execute_tool(event.data)
                    await self.realtime.send_tool_result(
                        event.data["call_id"],
                        result,
                    )
```

---

## File Structure

```
chatforge/
├── ports/
│   ├── __init__.py
│   ├── realtime.py              # RealtimeVoiceAPIPort, VoiceEvent, etc.
│   └── audio_stream.py          # AudioStreamPort
├── adapters/
│   └── realtime/
│       ├── __init__.py          # Factory function
│       ├── mock.py              # MockRealtimeAdapter
│       └── openai/
│           ├── __init__.py
│           ├── adapter.py       # OpenAIRealtimeAdapter
│           ├── translator.py    # Event translation
│           ├── messages.py      # Message builders
│           └── websocket.py     # Internal WebSocket utility
└── agent/
    └── voice.py                 # VoiceAgent
```

---

## What to Reuse from realtimevoiceapi

| Component | Source | Target | Changes |
|-----------|--------|--------|---------|
| `WebSocketConnection` | `connections/websocket_connection.py` | `adapters/realtime/openai/websocket.py` | Simplify, remove metrics |
| `MessageFactory` | `core/message_protocol.py` | `adapters/realtime/openai/messages.py` | Keep OpenAI-specific parts |
| `ProviderCapabilities` | `core/provider_protocol.py` | `ports/realtime.py` | Simplify for Chatforge |
| Event type mappings | `core/stream_protocol.py` | `ports/realtime.py` | Rename to `VoiceEventType` |

---

## Summary

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Port structure | Single `RealtimeVoiceAPIPort` | Clean interface, transport hidden |
| Transport handling | Internal composition | WebSocket not a port, just utility |
| Event normalization | `VoiceEvent` type | VoiceAgent doesn't know providers |
| Provider differences | Capability discovery | Runtime adaptation |
| Testing | `MockRealtimeAdapter` | No real API needed for tests |

### Why Not WebSocketPort?

1. Not all providers use WebSocket
2. Transport is implementation detail
3. Would require multiple transport ports
4. Leaks abstraction to domain layer

### Provider Decoupling

OpenAI-specific logic is isolated in:
- `adapters/realtime/openai/translator.py` (event translation)
- `adapters/realtime/openai/messages.py` (message format)
- `adapters/realtime/openai/adapter.py` (API specifics)

Adding Anthropic means adding `adapters/realtime/anthropic/` with same structure. Zero changes to `RealtimeVoiceAPIPort` or `VoiceAgent`.

---

## Related Documents

| Document | Topic |
|----------|-------|
| `chatforge_should_implement.md` | Full Chatforge enhancement list |
| `chatforge_voxstream_high_level.md` | AudioStreamPort architecture |
| `chatforge_compatibility_analysis.md` | Integration analysis |
| `what_is_missing_in_voxstream.md` | VoxStream gaps |
