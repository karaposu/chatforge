# What Needs to Port: realtimevoiceapi → Chatforge

*Detailed inventory of code to port, keeping loyal to Chatforge's hexagonal architecture.*

---

## Executive Summary

| Category | Files to Port | Lines | Priority |
|----------|---------------|-------|----------|
| **New Ports** | 2 new port interfaces | ~200 | Critical |
| **Protocol Layer** | 3 files from realtimevoiceapi | ~1,200 | Critical |
| **Connection Layer** | 1 file (simplified) | ~300 | Critical |
| **Adapters** | 4 new adapters | ~800 | High |
| **Agent** | 1 new agent class | ~300 | High |
| **Chatforge Fixes** | Internal changes | ~200 | Medium |
| **Total New Code** | | ~3,000 | |

---

## Part 1: New Ports (Chatforge Hexagonal Design)

### 1.1 AudioStreamPort (NEW)

**Purpose**: Abstract real-time audio I/O for local devices.

**Location**: `chatforge/ports/audio_stream.py`

**Contract**:
```python
class AudioStreamPort(ABC):
    """Port for real-time audio capture and playback."""

    # Capture
    async def start_capture(self) -> AsyncGenerator[bytes, None]: ...
    async def stop_capture(self) -> None: ...

    # Playback
    async def play_chunk(self, chunk: bytes) -> None: ...
    async def stop_playback(self) -> None: ...

    # VAD
    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None] | None,
        on_speech_end: Callable[[bytes], None] | None,
    ) -> None: ...
    def get_vad_state(self) -> Literal["silence", "speech"]: ...

    # Monitoring
    def get_input_level(self) -> float: ...
    def is_playing(self) -> bool: ...
```

**Adapters Needed**:
- `VoxStreamAdapter` - Uses VoxStream library
- `MockAudioStreamAdapter` - For testing

**Why a New Port**: Chatforge has no concept of real-time audio. This is fundamentally different from MessagingPort (which handles discrete messages).

---

### 1.2 RealtimeVoiceAPIPort (NEW)

**Purpose**: Abstract real-time voice AI API connections (WebSocket-based).

**Location**: `chatforge/ports/realtime.py`

**Contract**:
```python
class RealtimeVoiceAPIPort(ABC):
    """Port for real-time voice AI API connections."""

    # Connection
    async def connect(self, config: VoiceSessionConfig) -> None: ...
    async def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    # Audio streaming
    async def send_audio(self, chunk: bytes) -> None: ...
    async def commit_audio(self) -> None: ...
    async def clear_audio(self) -> None: ...

    # Response control
    async def interrupt(self) -> None: ...
    async def create_response(self, instructions: str | None = None) -> None: ...

    # Tool calling
    async def send_tool_result(self, call_id: str, result: str) -> None: ...

    # Event stream
    def events(self) -> AsyncGenerator[VoiceEvent, None]: ...

    # Capabilities
    def get_capabilities(self) -> ProviderCapabilities: ...
```

**Adapters Needed**:
- `OpenAIRealtimeAdapter` - Uses OpenAI Realtime API
- `MockRealtimeAdapter` - For testing
- Future: `AnthropicRealtimeAdapter`, `GoogleRealtimeAdapter`

**Why a New Port**: MessagingPort is request-response. RealtimeVoiceAPIPort is bidirectional streaming with continuous audio.

---

## Part 2: What to Port from realtimevoiceapi

### 2.1 Message Protocol (CRITICAL)

**Source**: `realtimevoiceapi/core/message_protocol.py` (381 lines)

**Port To**: `chatforge/adapters/realtime/openai/messages.py`

**What to Keep**:
```python
# Message type enums (rename for clarity)
class OpenAIClientMessageType(str, Enum):
    SESSION_UPDATE = "session.update"
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
    RESPONSE_CREATE = "response.create"
    RESPONSE_CANCEL = "response.cancel"
    CONVERSATION_ITEM_CREATE = "conversation.item.create"

class OpenAIServerMessageType(str, Enum):
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
    ERROR = "error"
    # ... etc

# Message factory (keep all methods)
class OpenAIMessageFactory:
    @staticmethod
    def session_update(config: dict) -> dict: ...
    @staticmethod
    def input_audio_buffer_append(audio_base64: str) -> dict: ...
    @staticmethod
    def input_audio_buffer_commit() -> dict: ...
    @staticmethod
    def response_create(instructions: str | None = None) -> dict: ...
    @staticmethod
    def conversation_item_create(...) -> dict: ...

# Protocol constants
class OpenAIProtocolInfo:
    AUDIO_FORMATS = ["pcm16", "g711_ulaw", "g711_alaw"]
    VOICES = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]
```

**What to Discard**:
- `MessageValidator` - Overkill for our use
- `MessageParser` - Replace with simpler event translator

**Changes**:
- Prefix all names with `OpenAI` to indicate they're provider-specific
- This code stays INSIDE the OpenAI adapter, not in the port

---

### 2.2 Stream Protocol (CRITICAL)

**Source**: `realtimevoiceapi/core/stream_protocol.py` (421 lines)

**Port To**: `chatforge/ports/realtime.py` (normalized types)

**What to Keep (Normalized for Chatforge)**:
```python
# Normalized event types (provider-agnostic)
class VoiceEventType(str, Enum):
    # Connection
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Audio
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_COMMITTED = "audio.committed"

    # Text
    TEXT_CHUNK = "text.chunk"
    TRANSCRIPT = "transcript"

    # Speech detection
    SPEECH_STARTED = "speech.started"
    SPEECH_ENDED = "speech.ended"

    # Response lifecycle
    RESPONSE_STARTED = "response.started"
    RESPONSE_DONE = "response.done"

    # Tool calling
    TOOL_CALL = "tool.call"

    # Session
    SESSION_UPDATED = "session.updated"

@dataclass
class VoiceEvent:
    type: VoiceEventType
    data: bytes | str | dict | None = None
    metadata: dict = field(default_factory=dict)
    raw_event: Any = None  # Original provider event

@dataclass
class ProviderCapabilities:
    provider_name: str
    supports_server_vad: bool = True
    supports_function_calling: bool = True
    supports_interruption: bool = True
    available_voices: list[str] = field(default_factory=list)
    supported_audio_formats: list[str] = field(default_factory=lambda: ["pcm16"])
```

**What to Discard**:
- `StreamState` enum - Simplified to `is_connected()`
- `StreamCapability` - Replaced by `ProviderCapabilities`
- `IStreamManager` protocol - Replaced by `RealtimeVoiceAPIPort`
- `IAudioHandler`, `ITextHandler` - Not needed at port level
- `StreamMetrics` - Can add later if needed

**Key Insight**: realtimevoiceapi has complex abstractions because it supports FastLane/BigLane modes. Chatforge only needs one mode (balanced), so we simplify.

---

### 2.3 WebSocket Connection (CRITICAL)

**Source**: `realtimevoiceapi/connections/websocket_connection.py` (516 lines)

**Port To**: `chatforge/adapters/realtime/openai/websocket.py` (~200 lines)

**What to Keep**:
```python
class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"

class WebSocketConnection:
    """Internal WebSocket utility for OpenAI adapter."""

    def __init__(self):
        self._ws = None
        self._state = ConnectionState.DISCONNECTED
        self._reconnect_attempts = 0

    async def connect(self, url: str, headers: dict) -> None: ...
    async def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    async def send(self, message: str) -> None: ...
    async def receive(self) -> AsyncGenerator[str, None]: ...
```

**What to Discard**:
- `ConnectionConfig` dataclass - Inline the config
- `FastLaneConnection` / `BigLaneConnection` subclasses - Not needed
- `ConnectionMetrics` - Can add later
- Message queue (`_send_worker`) - Direct send is fine
- `SerializationFormat` - Always JSON for OpenAI
- Complex reconnection logic - Simple retry is enough

**Why Simplify**: Chatforge doesn't need FastLane/BigLane distinction. We want one reliable, simple connection handler.

---

### 2.4 Event Translator (NEW - Don't Port, Create)

**Location**: `chatforge/adapters/realtime/openai/translator.py`

**Purpose**: Convert OpenAI-specific events to normalized `VoiceEvent`.

```python
class OpenAIEventTranslator:
    """Translates OpenAI Realtime events to Chatforge VoiceEvent."""

    def translate(self, raw: dict) -> VoiceEvent | None:
        event_type = raw.get("type", "")

        match event_type:
            case "response.audio.delta":
                return VoiceEvent(
                    type=VoiceEventType.AUDIO_CHUNK,
                    data=base64.b64decode(raw.get("delta", "")),
                    raw_event=raw,
                )
            case "response.text.delta":
                return VoiceEvent(
                    type=VoiceEventType.TEXT_CHUNK,
                    data=raw.get("delta", ""),
                    raw_event=raw,
                )
            case "input_audio_buffer.speech_started":
                return VoiceEvent(
                    type=VoiceEventType.SPEECH_STARTED,
                    raw_event=raw,
                )
            case "response.function_call_arguments.done":
                return VoiceEvent(
                    type=VoiceEventType.TOOL_CALL,
                    data={
                        "call_id": raw.get("call_id"),
                        "name": raw.get("name"),
                        "arguments": json.loads(raw.get("arguments", "{}")),
                    },
                    raw_event=raw,
                )
            case _:
                return None  # Ignore unknown events
```

**Why Create New**: realtimevoiceapi doesn't have a clean translator. It has handlers scattered throughout. A dedicated translator is cleaner.

---

### 2.5 Session Configuration (ADAPT)

**Source**: `realtimevoiceapi/session/session.py` (448 lines)

**Port To**: `chatforge/ports/realtime.py` (simplified)

**What to Keep (Simplified)**:
```python
@dataclass
class VoiceSessionConfig:
    """Provider-agnostic session configuration."""

    # Model
    model: str = "default"  # Provider resolves to actual model

    # Voice
    voice: str = "default"  # Provider resolves to actual voice

    # Behavior
    system_prompt: str | None = None
    temperature: float = 0.8

    # Audio format
    input_format: str = "pcm16"
    output_format: str = "pcm16"
    sample_rate: int = 24000

    # VAD
    vad_mode: str = "server"  # "server", "client", "none"
    silence_threshold_ms: int = 500

    # Tools
    tools: list[dict] | None = None
    tool_choice: str = "auto"
```

**What to Discard**:
- `Identity` objects - Use system_prompt directly
- `to_dict()` method - Each adapter does its own translation
- OpenAI-specific fields (input_audio_transcription details, etc.)

**Key Change**: Session config is provider-agnostic. OpenAI adapter translates to OpenAI format internally.

---

### 2.6 Provider Capabilities (ADAPT)

**Source**: `realtimevoiceapi/core/provider_protocol.py` (442 lines)

**Port To**: `chatforge/ports/realtime.py` (simplified)

**What to Keep**:
```python
@dataclass
class ProviderCapabilities:
    """What this voice provider supports."""
    provider_name: str
    supports_server_vad: bool = True
    supports_client_vad: bool = False
    supports_function_calling: bool = True
    supports_interruption: bool = True
    available_voices: list[str] = field(default_factory=list)
    supported_audio_formats: list[str] = field(default_factory=lambda: ["pcm16"])
    supported_sample_rates: list[int] = field(default_factory=lambda: [24000])
```

**What to Discard**:
- `CostModel`, `Usage`, `Cost` - Add later if needed
- `FunctionDefinition`, `FunctionCall` - Use standard dict format
- `IVoiceProvider`, `IProviderSession` protocols - Replaced by RealtimeVoiceAPIPort
- `ProviderRegistry` - Overkill, use simple factory

---

## Part 3: New Adapters to Create

### 3.1 OpenAIRealtimeAdapter

**Location**: `chatforge/adapters/realtime/openai/adapter.py`

**Implements**: `RealtimeVoiceAPIPort`

**Internal Components**:
- `WebSocketConnection` (from ported code)
- `OpenAIMessageFactory` (from ported code)
- `OpenAIEventTranslator` (new)

**Key Methods**:
```python
class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, api_key: str): ...

    async def connect(self, config: VoiceSessionConfig) -> None:
        # Translate config to OpenAI format
        # Connect WebSocket
        # Send session.update

    async def send_audio(self, chunk: bytes) -> None:
        # Base64 encode
        # Send input_audio_buffer.append

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        # Receive from WebSocket
        # Translate via OpenAIEventTranslator
        # Yield normalized events
```

### 3.2 MockRealtimeAdapter

**Location**: `chatforge/adapters/realtime/mock.py`

**Purpose**: Testing without real API.

```python
class MockRealtimeAdapter(RealtimeVoiceAPIPort):
    def queue_event(self, event: VoiceEvent) -> None: ...
    def queue_audio_response(self, audio: bytes) -> None: ...
    def get_sent_audio(self) -> list[bytes]: ...
```

### 3.3 VoxStreamAdapter

**Location**: `chatforge/adapters/audio/voxstream.py`

**Implements**: `AudioStreamPort`

```python
class VoxStreamAdapter(AudioStreamPort):
    def __init__(self, config: dict | None = None):
        self._voxstream = VoxStream(mode=ProcessingMode.REALTIME)

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        async for chunk in self._voxstream.capture_stream():
            yield chunk

    async def play_chunk(self, chunk: bytes) -> None:
        self._voxstream.play_audio(chunk)
```

### 3.4 MockAudioStreamAdapter

**Location**: `chatforge/adapters/audio/mock.py`

**Purpose**: Testing without real audio.

```python
class MockAudioStreamAdapter(AudioStreamPort):
    def queue_capture_chunk(self, chunk: bytes) -> None: ...
    def trigger_speech_start(self) -> None: ...
    def get_played_audio(self) -> list[bytes]: ...
```

---

## Part 4: New Agent

### 4.1 VoiceAgent

**Location**: `chatforge/agent/voice.py`

**Purpose**: Coordinate AudioStreamPort + RealtimeVoiceAPIPort for voice conversations.

```python
class VoiceAgent:
    def __init__(
        self,
        audio: AudioStreamPort,
        realtime: RealtimeVoiceAPIPort,
        actions: TicketingPort | None = None,
        config: VoiceAgentConfig | None = None,
    ): ...

    async def start(self) -> None:
        # Connect to realtime API
        # Set up VAD callbacks
        # Start capture loop
        # Start event loop

    async def stop(self) -> None: ...

    async def _capture_loop(self) -> None:
        # Capture audio → send to realtime

    async def _event_loop(self) -> None:
        # Receive events → play audio / handle tools
```

---

## Part 5: Things to Solve in Chatforge

### 5.1 True Streaming Support

**Current State**: Chatforge's `/chat/stream` endpoint is fake streaming (chunks after completion).

**Problem**: VoiceAgent needs true event streaming.

**Solution Options**:

| Option | Description | Effort |
|--------|-------------|--------|
| A. Keep separate | VoiceAgent has its own event model | Low |
| B. Unify streaming | Create StreamingPort used by both | High |
| C. Extend SSE | Add voice events to existing SSE | Medium |

**Recommendation**: Option A for now. VoiceAgent has different needs (audio bytes, not text tokens).

---

### 5.2 TicketingPort Async

**Current State**: TicketingPort methods are synchronous.

```python
class TicketingPort(ABC):
    @abstractmethod
    def execute(self, title: str, ...) -> str:  # Sync!
        ...
```

**Problem**: VoiceAgent is fully async. Calling sync TicketingPort blocks event loop.

**Solution**:
```python
class TicketingPort(ABC):
    @abstractmethod
    async def execute(self, title: str, ...) -> str:  # Make async
        ...
```

**Impact**: Need to update all TicketingPort adapters to be async.

**Alternative**: Use `asyncio.to_thread()` to wrap sync calls:
```python
result = await asyncio.to_thread(self.actions.execute, ...)
```

---

### 5.3 Tool Integration Pattern

**Current State**: ReActAgent tools are LangChain BaseTool instances.

**Problem**: VoiceAgent receives tool calls as JSON from RealtimeVoiceAPIPort:
```python
{
    "call_id": "call_abc123",
    "name": "get_weather",
    "arguments": {"city": "San Francisco"}
}
```

**Solution**: VoiceAgent needs a tool registry:
```python
class VoiceAgent:
    def __init__(self, ..., tools: dict[str, Callable] | None = None):
        self._tools = tools or {}

    async def _execute_tool(self, call: dict) -> str:
        tool_fn = self._tools.get(call["name"])
        if tool_fn:
            result = await tool_fn(**call["arguments"])
            return json.dumps(result)
        return json.dumps({"error": f"Unknown tool: {call['name']}"})
```

**Alternative**: Use TicketingPort as the tool execution layer:
```python
async def _execute_tool(self, call: dict) -> str:
    if self.actions:
        return await self.actions.execute_tool(call["name"], call["arguments"])
```

---

### 5.4 Configuration Unification

**Current State**: Chatforge has `LLMSettings`, `AgentSettings` in config/.

**Need**: Voice-specific settings.

**Solution**: Add voice configuration:
```python
# chatforge/config/voice.py

@dataclass
class VoiceSettings:
    default_voice: str = "alloy"
    default_model: str = "gpt-4o-realtime-preview"
    vad_mode: str = "server"
    silence_threshold_ms: int = 500
    enable_transcription: bool = True
```

---

### 5.5 TracingPort Integration

**Current State**: TracingPort wraps LLM calls with spans.

**Need**: Trace voice conversations (audio in, audio out, tool calls).

**Solution**: VoiceAgent emits trace events:
```python
class VoiceAgent:
    def __init__(self, ..., tracing: TracingPort | None = None):
        self._tracing = tracing

    async def _on_response_done(self, event: VoiceEvent):
        if self._tracing and self._tracing.enabled:
            self._tracing.set_trace_metadata({
                "voice.response_id": event.metadata.get("response_id"),
                "voice.audio_duration_ms": ...,
            })
```

---

## Part 6: File Structure After Porting

```
chatforge/
├── ports/
│   ├── __init__.py
│   ├── storage.py         # Existing
│   ├── messaging.py       # Existing
│   ├── action.py          # Existing (make async)
│   ├── knowledge.py       # Existing
│   ├── tracing.py         # Existing
│   ├── audio_stream.py    # NEW - AudioStreamPort
│   └── realtime.py        # NEW - RealtimeVoiceAPIPort, VoiceEvent, etc.
├── adapters/
│   ├── storage/           # Existing
│   ├── fastapi/           # Existing
│   ├── audio/             # NEW
│   │   ├── __init__.py
│   │   ├── voxstream.py   # VoxStreamAdapter
│   │   └── mock.py        # MockAudioStreamAdapter
│   └── realtime/          # NEW
│       ├── __init__.py    # Factory function
│       ├── mock.py        # MockRealtimeAdapter
│       └── openai/        # OpenAI-specific
│           ├── __init__.py
│           ├── adapter.py     # OpenAIRealtimeAdapter
│           ├── websocket.py   # WebSocketConnection (ported)
│           ├── messages.py    # OpenAIMessageFactory (ported)
│           └── translator.py  # OpenAIEventTranslator (new)
├── agent/
│   ├── __init__.py
│   ├── engine.py          # Existing ReActAgent
│   ├── state.py           # Existing
│   └── voice.py           # NEW - VoiceAgent
└── config/
    ├── __init__.py
    ├── agent.py           # Existing
    ├── llm.py             # Existing
    └── voice.py           # NEW - VoiceSettings
```

---

## Part 7: Porting Checklist

### Critical Path (Must Complete)

- [ ] Create `chatforge/ports/audio_stream.py`
- [ ] Create `chatforge/ports/realtime.py`
- [ ] Create `chatforge/adapters/audio/mock.py`
- [ ] Create `chatforge/adapters/realtime/mock.py`
- [ ] Create `chatforge/agent/voice.py`
- [ ] Write tests with mock adapters

### OpenAI Integration

- [ ] Port `websocket_connection.py` → `adapters/realtime/openai/websocket.py`
- [ ] Port `message_protocol.py` → `adapters/realtime/openai/messages.py`
- [ ] Create `adapters/realtime/openai/translator.py`
- [ ] Create `adapters/realtime/openai/adapter.py`
- [ ] Write integration tests

### VoxStream Integration

- [ ] Create `chatforge/adapters/audio/voxstream.py`
- [ ] Test with real microphone

### Chatforge Fixes

- [ ] Make TicketingPort async (or use asyncio.to_thread)
- [ ] Add voice configuration
- [ ] Add tracing integration for voice

---

## Part 8: What NOT to Port

| Component | Reason |
|-----------|--------|
| FastLane/BigLane split | Chatforge uses single mode |
| EventBus | Overkill for our needs |
| StreamOrchestrator | Future multi-provider feature |
| ResponseAggregator | Not needed for streaming |
| AudioPipeline | VoxStream handles audio processing |
| BaseEngine | Too coupled to audioengine |
| VoiceEngine | Replace with VoiceAgent |
| SessionManager | Chatforge has StoragePort |
| client.py | Incomplete, has missing imports |
| CostModel/Usage | Nice to have, not critical |

---

## Summary

### Lines of Code Estimate

| Component | New Lines | Ported Lines |
|-----------|-----------|--------------|
| AudioStreamPort | 80 | 0 |
| RealtimeVoiceAPIPort + types | 150 | 0 |
| MockAudioStreamAdapter | 100 | 0 |
| MockRealtimeAdapter | 120 | 0 |
| VoiceAgent | 300 | 0 |
| OpenAIRealtimeAdapter | 250 | 0 |
| WebSocketConnection | 0 | 200 (simplified) |
| OpenAIMessageFactory | 0 | 150 (simplified) |
| OpenAIEventTranslator | 150 | 0 |
| Config/Fixes | 100 | 0 |
| **Total** | **1,250** | **350** |

### Key Principles

1. **Ports are provider-agnostic** - No OpenAI-specific code in port interfaces
2. **Adapters contain provider logic** - All OpenAI code in `adapters/realtime/openai/`
3. **Simplify aggressively** - realtimevoiceapi has complexity we don't need
4. **Test with mocks first** - Build confidence before real integrations
5. **Stable intermediate forms** - Each step produces working, testable code

---

## Related Documents

| Document | Topic |
|----------|-------|
| `actionable_plan.md` | Implementation phases |
| `how_can_chatforge_should_implement_voice_connection.md` | RealtimeVoiceAPIPort design |
| `chatforge_voxstream_high_level.md` | AudioStreamPort design |
| `chatforge_should_implement.md` | Full enhancement list |
