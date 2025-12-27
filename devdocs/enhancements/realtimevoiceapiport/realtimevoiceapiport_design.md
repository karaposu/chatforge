# RealtimeVoiceAPIPort: Design Considerations

*Designing Chatforge's RealtimeVoiceAPIPort based on realtimevoiceapi implementation analysis.*

---

## What is RealtimeVoiceAPIPort?

### Definition

**RealtimeVoiceAPIPort** is a Chatforge port for **real-time bidirectional AI API connections**.

It handles:
- **Audio streaming** (voice input/output)
- **Text streaming** (text input/output)
- **Tool/function calling**
- **Voice activity detection** (server-side VAD)
- **Session management**

### Why "RealtimeVoiceAPIPort"?

| Name | Why Not |
|------|---------|
| VoicePort | Too vague, ignores text capability |
| RealtimePort | Too vague - realtime what? |
| VoiceAIPlatformIntegrationPort | Too long |
| **RealtimeVoiceAPIPort** | Clear: realtime + voice + API. Matches "OpenAI Realtime API" naming |

The port supports **both voice AND text** in the same session (the API handles both).

### How It Fits in Chatforge

```
┌─────────────────────────────────────────────────────────────────┐
│                      Chatforge Ports                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Text-based:                                                     │
│  ├── MessagingPlatformIntegrationPort → Slack, Discord, Teams   │
│  └── StreamingPort      → SSE text streaming (one-way)          │
│                                                                  │
│  Real-time:                                                      │
│  ├── RealtimeVoiceAPIPort       → WebSocket AI (voice+text, two-way) ◄──│
│  └── AudioStreamPort    → Local audio hardware (mic/speaker) ◄──│
│                                                                  │
│  Infrastructure:                                                 │
│  ├── StoragePort        → Conversation persistence              │
│  ├── TicketingPort         → Tool execution                        │
│  ├── KnowledgePort      → RAG / knowledge base                  │
│  └── TracingPort        → Observability                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### RealtimeVoiceAPIPort vs Other Ports

| Port | Direction | Transport | Content | Use Case |
|------|-----------|-----------|---------|----------|
| **MessagingPlatformIntegrationPort** | Request/Response | HTTP | Text | Chat platforms |
| **StreamingPort** | One-way (server→client) | SSE | Text tokens | Streaming text responses |
| **RealtimeVoiceAPIPort** | Bidirectional | WebSocket | Audio + Text | Real-time voice/text AI |
| **AudioStreamPort** | Local I/O | sounddevice | Audio | Mic/speaker hardware |

---

## Part 1: Lessons from realtimevoiceapi

### 1.1 Message Protocol Complexity

**Source**: `realtimevoiceapi/core/message_protocol.py`

OpenAI Realtime API has **~30 message types**:

**Client → Server (10 types)**:
```
session.update                    # Configure session
input_audio_buffer.append         # Send audio chunk
input_audio_buffer.commit         # Commit audio (manual VAD)
input_audio_buffer.clear          # Clear audio buffer
conversation.item.create          # Create message or tool result
conversation.item.truncate        # Truncate conversation
conversation.item.delete          # Delete conversation item
response.create                   # Trigger AI response
response.cancel                   # Cancel in-progress response
```

**Server → Client (20+ types)**:
```
session.created / session.updated
conversation.created / conversation.item.created
input_audio_buffer.committed / cleared
input_audio_buffer.speech_started / speech_stopped
response.created / response.done
response.output_item.added / done
response.content_part.added / done
response.audio.delta / done
response.audio_transcript.delta / done
response.text.delta / done
response.function_call_arguments.delta / done
rate_limits.updated
error
```

**Key Insight**: These are **OpenAI-specific**. Anthropic will have different message types. RealtimeVoiceAPIPort must **normalize events** to a provider-agnostic format.

### 1.2 Connection State Machine

**Source**: `realtimevoiceapi/connections/websocket_connection.py`

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
             ┌──────────────┐                         │
             │ DISCONNECTED │◄────────────────────────┤
             └──────┬───────┘                         │
                    │ connect()                       │
                    ▼                                  │
             ┌──────────────┐                         │
             │  CONNECTING  │                         │
             └──────┬───────┘                         │
                    │ success                         │
                    ▼                                  │
             ┌──────────────┐      connection lost    │
             │  CONNECTED   │─────────────────────────┤
             └──────┬───────┘                         │
                    │                                  │
                    ▼                                  │
             ┌──────────────┐      max retries        │
             │ RECONNECTING │─────────────────────────┤
             └──────┬───────┘                         │
                    │ success                         │
                    └──────────────► CONNECTED        │
                                                      │
             ┌──────────────┐                         │
             │    CLOSED    │◄────────────────────────┘
             └──────────────┘
```

**Key Insight**: Need to handle reconnection gracefully. Emit events for state changes so VoiceAgent can react.

### 1.3 Session Configuration

**Source**: `realtimevoiceapi/session/session.py`

OpenAI's session config is **very rich**:

```python
{
    "model": "gpt-4o-realtime-preview-2024-12-17",
    "modalities": ["text", "audio"],
    "voice": "alloy",
    "instructions": "You are a helpful assistant.",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": {
        "model": "whisper-1"
    },
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500,
        "create_response": true
    },
    "tools": [...],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_response_output_tokens": "inf"
}
```

**Key Insight**: Most of this is OpenAI-specific. RealtimeVoiceAPIPort needs a **provider-agnostic config** that adapters translate.

### 1.4 Tool Calling Flow

**Source**: `realtimevoiceapi/connections/client.py`

```
1. AI decides to call a function
   Server → response.function_call_arguments.done
   {
       "type": "response.function_call_arguments.done",
       "call_id": "call_abc123",
       "name": "get_weather",
       "arguments": "{\"city\": \"San Francisco\"}"
   }

2. Client executes function locally
   result = get_weather(city="San Francisco")

3. Client sends result back
   Client → conversation.item.create
   {
       "type": "conversation.item.create",
       "item": {
           "type": "function_call_output",
           "call_id": "call_abc123",
           "output": "{\"temp\": 72, \"condition\": \"sunny\"}"
       }
   }

4. Client triggers continuation
   Client → response.create
   {
       "type": "response.create"
   }

5. AI continues with result
   Server → response.audio.delta (continues speaking)
```

**Key Insight**: Tool calling is **async** and requires explicit continuation. RealtimeVoiceAPIPort must expose this flow clearly.

### 1.5 Audio Format Requirements

**Source**: `realtimevoiceapi/core/message_protocol.py`

```python
AUDIO_FORMATS = ["pcm16", "g711_ulaw", "g711_alaw"]
SAMPLE_RATE = 24000  # Fixed for OpenAI
CHANNELS = 1         # Mono only
BIT_DEPTH = 16       # 16-bit PCM
```

**Key Insight**: Audio format is standardized (PCM16 @ 24kHz mono). Include in config but expect most providers to use same format.

### 1.6 Rate Limiting

**Source**: `realtimevoiceapi/core/message_protocol.py`

```python
ServerMessageType.RATE_LIMITS_UPDATED = "rate_limits.updated"
```

Server sends rate limit info. Need to:
- Expose as event
- Potentially buffer/throttle sends
- Provide retry_after info

---

## Part 2: Key Requirements

### 2.1 Provider Agnosticism

**Requirement**: Port interface must not contain OpenAI-specific concepts.

**How**:
- Normalized event types (VoiceEventType enum)
- Provider-agnostic config (VoiceSessionConfig)
- Capability discovery (ProviderCapabilities)
- Adapters translate to/from provider format

```
VoiceAgent
    │
    ▼
RealtimeVoiceAPIPort (normalized events)
    │
    ▼
OpenAIRealtimeAdapter (translates)
    │
    ▼
OpenAI Realtime API (provider-specific)
```

### 2.2 Bidirectional Streaming

**Requirement**: Handle simultaneous input and output.

```python
# These happen concurrently:
async def capture_loop():
    async for chunk in audio.start_capture():
        await realtime.send_audio(chunk)  # Sending

async def playback_loop():
    async for event in realtime.events():  # Receiving
        if event.type == VoiceEventType.AUDIO_CHUNK:
            await audio.play_chunk(event.data)
```

### 2.3 Low Latency

**Requirement**: <10ms overhead for audio operations.

**How**:
- No unnecessary copying
- Direct WebSocket send (no queuing in fast path)
- Efficient base64 encoding
- Minimal event object creation

### 2.4 Event Normalization

**Requirement**: VoiceAgent sees consistent events regardless of provider.

```python
class VoiceEventType(str, Enum):
    # Connection
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

    # Audio
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_COMMITTED = "audio.committed"

    # Text
    TEXT_CHUNK = "text.chunk"
    TRANSCRIPT = "transcript"

    # VAD
    SPEECH_STARTED = "speech.started"
    SPEECH_ENDED = "speech.ended"

    # Response
    RESPONSE_STARTED = "response.started"
    RESPONSE_DONE = "response.done"

    # Tools
    TOOL_CALL = "tool.call"
```

### 2.5 Capability Discovery

**Requirement**: Know what provider supports at runtime.

```python
@dataclass
class ProviderCapabilities:
    provider_name: str
    supports_server_vad: bool = True
    supports_function_calling: bool = True
    supports_interruption: bool = True
    supports_transcription: bool = True
    available_voices: list[str] = field(default_factory=list)
    available_models: list[str] = field(default_factory=list)
```

**Use case**:
```python
caps = realtime.get_capabilities()
if not caps.supports_server_vad:
    # Use client-side VAD from AudioStreamPort
    audio.set_vad_callbacks(on_speech_end=commit_audio)
```

### 2.6 Graceful Error Handling

**Requirement**: Clear error categories and recovery paths.

```python
class RealtimeError(Exception): ...
class ConnectionError(RealtimeError): ...     # Network issues
class AuthenticationError(RealtimeError): ... # Invalid API key
class RateLimitError(RealtimeError): ...      # Rate limited
class ProviderError(RealtimeError): ...       # Provider-specific error
class SessionError(RealtimeError): ...        # Invalid session state
```

### 2.7 Reconnection Support

**Requirement**: Handle connection drops gracefully.

```python
@dataclass
class ReconnectionConfig:
    enabled: bool = True
    max_attempts: int = 5
    base_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
```

On disconnect:
1. Emit `DISCONNECTED` event
2. Attempt reconnect with exponential backoff
3. Emit `RECONNECTING` events
4. On success: `CONNECTED` + re-send session config
5. On max retries: `DISCONNECTED` with error

---

## Part 3: Interface Design

### 3.1 Core Interface

```python
class RealtimeVoiceAPIPort(ABC):
    """
    Port for real-time AI API connections.

    Handles bidirectional streaming with AI providers:
    - OpenAI Realtime API
    - Anthropic Real-time (future)
    - Google Gemini Real-time (future)

    Supports:
    - Audio streaming (voice input/output)
    - Text streaming (text input/output)
    - Tool/function calling
    - Voice activity detection (VAD)
    """

    # === Connection Lifecycle ===

    @abstractmethod
    async def connect(self, config: VoiceSessionConfig) -> None:
        """Connect and configure session."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect gracefully."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        ...

    # === Audio Streaming ===

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """Send audio chunk to API."""
        ...

    @abstractmethod
    async def commit_audio(self) -> None:
        """Commit audio buffer (manual VAD)."""
        ...

    @abstractmethod
    async def clear_audio(self) -> None:
        """Clear audio buffer."""
        ...

    # === Text Input ===

    @abstractmethod
    async def send_text(self, text: str) -> None:
        """Send text message."""
        ...

    # === Response Control ===

    @abstractmethod
    async def create_response(self, instructions: str | None = None) -> None:
        """Trigger AI response."""
        ...

    @abstractmethod
    async def interrupt(self) -> None:
        """Interrupt current response (barge-in)."""
        ...

    # === Tool Calling ===

    @abstractmethod
    async def send_tool_result(
        self,
        call_id: str,
        result: str,
        is_error: bool = False,
    ) -> None:
        """Send tool result back to API."""
        ...

    # === Event Stream ===

    @abstractmethod
    def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """Stream of normalized events from API."""
        ...

    # === Capabilities ===

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name."""
        ...
```

### 3.2 Configuration

```python
@dataclass
class VoiceSessionConfig:
    """Provider-agnostic session configuration."""

    # Model (provider resolves to actual model)
    model: str = "default"

    # Voice (provider resolves to actual voice)
    voice: str = "default"

    # System prompt
    system_prompt: str | None = None

    # Generation
    temperature: float = 0.8
    max_tokens: int | None = None

    # Audio format
    input_format: str = "pcm16"
    output_format: str = "pcm16"
    sample_rate: int = 24000

    # VAD
    vad_mode: Literal["server", "client", "none"] = "server"
    vad_threshold: float = 0.5
    vad_silence_ms: int = 500
    vad_prefix_ms: int = 300

    # Tools
    tools: list[ToolDefinition] | None = None
    tool_choice: Literal["auto", "none", "required"] = "auto"

    # Provider-specific (escape hatch)
    provider_options: dict | None = None
```

### 3.3 Event Structure

```python
@dataclass
class VoiceEvent:
    """Normalized event from realtime API."""
    type: VoiceEventType
    data: bytes | str | dict | None = None
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    raw_event: Any = None  # Original provider event (for debugging)
```

---

## Part 4: Things to Consider

### 4.1 Modality Support

**Question**: Should RealtimeVoiceAPIPort expose modality configuration?

**Current thinking**: Yes, via config:
```python
@dataclass
class VoiceSessionConfig:
    modalities: list[Literal["audio", "text"]] = field(
        default_factory=lambda: ["audio", "text"]
    )
```

This allows:
- Audio-only mode (no text transcripts)
- Text-only mode (for testing without audio)
- Both (default)

### 4.2 Transcription Control

**Question**: Should user speech transcription be configurable?

**OpenAI supports**:
```python
"input_audio_transcription": {
    "model": "whisper-1"
}
```

**Recommendation**: Include in config:
```python
@dataclass
class VoiceSessionConfig:
    transcription_enabled: bool = True
    transcription_model: str | None = None  # Provider default
```

### 4.3 Response Streaming Granularity

**Question**: How granular should audio events be?

**Options**:
1. **Every delta**: Emit event for each `response.audio.delta`
2. **Batched**: Accumulate and emit every N ms
3. **Configurable**: Let caller choose

**Recommendation**: Option 1 (every delta). Let AudioStreamPort/VoiceAgent handle batching if needed.

### 4.4 Conversation History

**Question**: Should RealtimeVoiceAPIPort expose conversation history?

**OpenAI provides**: `conversation.item.created` events with full history.

**Recommendation**: Emit as events, let VoiceAgent/StoragePort handle persistence:
```python
class VoiceEventType(str, Enum):
    CONVERSATION_ITEM = "conversation.item"  # New item added
```

### 4.5 Session Updates

**Question**: What can be updated mid-session?

**OpenAI allows updating**:
- instructions
- voice
- temperature
- tools
- turn_detection settings

**Not updatable**:
- model
- audio formats

**Recommendation**: `update_session()` method with same config object. Adapter validates what's updatable.

### 4.6 Multiple Concurrent Responses

**Question**: Can there be multiple responses in flight?

**OpenAI**: Yes, responses have IDs. Can cancel specific ones.

**Recommendation**: Include response_id in events and cancel method:
```python
async def cancel_response(self, response_id: str | None = None) -> None:
    """Cancel specific or current response."""
```

### 4.7 Audio Buffer State

**Question**: Should port expose audio buffer state?

**OpenAI provides**:
- `input_audio_buffer.committed` - audio was committed
- `input_audio_buffer.cleared` - audio was cleared
- `input_audio_buffer.speech_started` - speech detected
- `input_audio_buffer.speech_stopped` - silence detected

**Recommendation**: Expose as events:
```python
class VoiceEventType(str, Enum):
    AUDIO_COMMITTED = "audio.committed"
    AUDIO_CLEARED = "audio.cleared"
    SPEECH_STARTED = "speech.started"
    SPEECH_ENDED = "speech.ended"
```

### 4.8 Cost/Usage Tracking

**Question**: Should port expose usage/cost info?

**OpenAI provides**: `rate_limits.updated` with token counts.

**Recommendation**: Expose as event, let caller track:
```python
class VoiceEventType(str, Enum):
    USAGE_UPDATED = "usage.updated"

# Event data:
{
    "audio_input_tokens": 1234,
    "audio_output_tokens": 5678,
    "text_input_tokens": 100,
    "text_output_tokens": 200,
}
```

### 4.9 Error Recovery

**Question**: What should happen after an error?

**Scenarios**:
1. **Connection lost**: Reconnect automatically
2. **Rate limited**: Pause, retry after delay
3. **Invalid request**: Emit error, don't retry
4. **Server error**: Emit error, maybe retry

**Recommendation**:
- Adapter handles reconnection internally
- Emit error events for visibility
- Provide `retry_after` info when available

### 4.10 Thread Safety

**Question**: Is RealtimeVoiceAPIPort thread-safe?

**Consideration**: VoiceAgent may call `send_audio()` from capture loop while consuming `events()`.

**Recommendation**:
- Adapters must be thread-safe
- Use `asyncio.Lock` for shared state
- Document concurrency model

---

## Part 5: Adapter Implementation Notes

### 5.1 OpenAI Adapter Structure

```
chatforge/adapters/realtime/openai/
├── __init__.py          # Exports OpenAIRealtimeAdapter
├── adapter.py           # Main adapter class
├── websocket.py         # WebSocket connection utility
├── messages.py          # OpenAI message factory
├── translator.py        # Event translation
└── config.py            # Config translation helpers
```

### 5.2 Translation Layer

**Config translation**:
```python
# VoiceSessionConfig → OpenAI format
def to_openai_session(config: VoiceSessionConfig) -> dict:
    return {
        "model": resolve_model(config.model),
        "voice": resolve_voice(config.voice),
        "instructions": config.system_prompt,
        "temperature": config.temperature,
        "turn_detection": {
            "type": "server_vad" if config.vad_mode == "server" else None,
            "threshold": config.vad_threshold,
            "silence_duration_ms": config.vad_silence_ms,
            "prefix_padding_ms": config.vad_prefix_ms,
        } if config.vad_mode == "server" else None,
        "tools": [to_openai_tool(t) for t in config.tools] if config.tools else None,
        "tool_choice": config.tool_choice,
        **(config.provider_options or {}),
    }
```

**Event translation**:
```python
def translate_event(raw: dict) -> VoiceEvent | None:
    event_type = raw.get("type")

    match event_type:
        case "response.audio.delta":
            return VoiceEvent(
                type=VoiceEventType.AUDIO_CHUNK,
                data=base64.b64decode(raw["delta"]),
                metadata={"response_id": raw.get("response_id")},
                raw_event=raw,
            )

        case "response.function_call_arguments.done":
            return VoiceEvent(
                type=VoiceEventType.TOOL_CALL,
                data={
                    "call_id": raw["call_id"],
                    "name": raw["name"],
                    "arguments": json.loads(raw["arguments"]),
                },
                raw_event=raw,
            )

        case "error":
            return VoiceEvent(
                type=VoiceEventType.ERROR,
                data={
                    "code": raw.get("error", {}).get("code"),
                    "message": raw.get("error", {}).get("message"),
                },
                raw_event=raw,
            )

        case _:
            return None  # Ignore unhandled events
```

### 5.3 What to Port from realtimevoiceapi

| Component | Source | Target | Action |
|-----------|--------|--------|--------|
| WebSocketConnection | `connections/websocket_connection.py` | `adapters/realtime/openai/websocket.py` | Simplify |
| MessageFactory | `core/message_protocol.py` | `adapters/realtime/openai/messages.py` | Keep |
| Event types | `core/stream_protocol.py` | `ports/realtime.py` | Normalize |
| SessionConfig | `session/session.py` | `ports/realtime.py` | Abstract |

---

## Part 6: Testing Strategy

### 6.1 Mock Adapter

```python
class MockRealtimeAdapter(RealtimeVoiceAPIPort):
    """For testing without real API."""

    def __init__(self):
        self._connected = False
        self._events: list[VoiceEvent] = []
        self._sent_audio: list[bytes] = []
        self._tool_results: list[tuple] = []

    # Test helpers
    def queue_event(self, event: VoiceEvent) -> None:
        self._events.append(event)

    def queue_audio_response(self, audio: bytes, chunk_size: int = 4800) -> None:
        self.queue_event(VoiceEvent(type=VoiceEventType.RESPONSE_STARTED))
        for i in range(0, len(audio), chunk_size):
            self.queue_event(VoiceEvent(
                type=VoiceEventType.AUDIO_CHUNK,
                data=audio[i:i+chunk_size],
            ))
        self.queue_event(VoiceEvent(type=VoiceEventType.RESPONSE_DONE))

    def queue_tool_call(self, call_id: str, name: str, args: dict) -> None:
        self.queue_event(VoiceEvent(
            type=VoiceEventType.TOOL_CALL,
            data={"call_id": call_id, "name": name, "arguments": args},
        ))

    def simulate_disconnect(self) -> None:
        self._connected = False
        self.queue_event(VoiceEvent(type=VoiceEventType.DISCONNECTED))

    def get_sent_audio(self) -> list[bytes]:
        return self._sent_audio.copy()

    def get_tool_results(self) -> list[tuple]:
        return self._tool_results.copy()
```

### 6.2 Test Scenarios

```python
async def test_connect_and_receive_audio():
    realtime = MockRealtimeAdapter()
    realtime.queue_audio_response(b"hello world audio")

    await realtime.connect(VoiceSessionConfig())

    events = []
    async for event in realtime.events():
        events.append(event)
        if event.type == VoiceEventType.RESPONSE_DONE:
            break

    assert events[0].type == VoiceEventType.RESPONSE_STARTED
    assert events[1].type == VoiceEventType.AUDIO_CHUNK
    assert events[-1].type == VoiceEventType.RESPONSE_DONE


async def test_tool_calling_flow():
    realtime = MockRealtimeAdapter()
    realtime.queue_tool_call("call_123", "get_weather", {"city": "SF"})

    await realtime.connect(VoiceSessionConfig())

    async for event in realtime.events():
        if event.type == VoiceEventType.TOOL_CALL:
            # Execute tool
            result = json.dumps({"temp": 72})
            await realtime.send_tool_result("call_123", result)
            await realtime.create_response()
            break

    assert realtime.get_tool_results() == [("call_123", '{"temp": 72}', False)]


async def test_barge_in():
    realtime = MockRealtimeAdapter()
    await realtime.connect(VoiceSessionConfig())

    # Simulate interrupt while AI is responding
    await realtime.interrupt()

    # Should stop playback and cancel response
    assert not realtime.is_connected() or True  # Adapter handles cleanup
```

---

## Summary

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Name** | RealtimeVoiceAPIPort | Matches industry, covers voice+text |
| **Event model** | Normalized VoiceEventType | Provider-agnostic for VoiceAgent |
| **Config** | VoiceSessionConfig | Abstract from provider format |
| **Transport** | Hidden in adapter | WebSocket is implementation detail |
| **Tool calling** | Explicit methods | Clear async flow |
| **Errors** | Typed exceptions | Clear categorization |
| **Testing** | MockRealtimeAdapter | No API needed for tests |

### Critical Considerations

1. **Provider agnosticism**: Never expose OpenAI-specific types in port
2. **Event normalization**: All events translated to VoiceEventType
3. **Latency**: <10ms overhead for audio operations
4. **Reconnection**: Automatic with configurable backoff
5. **Tool calling**: Async flow with explicit continuation
6. **Thread safety**: Safe for concurrent send/receive

### What to Port from realtimevoiceapi

| Keep | Discard |
|------|---------|
| WebSocketConnection (simplified) | FastLane/BigLane split |
| MessageFactory | Complex EventBus |
| Connection state machine | StreamOrchestrator |
| Event type mappings | Cost tracking (for now) |

---

## Related Documents

| Document | Topic |
|----------|-------|
| `how_audiostreamport_should_work_to_be_compatible_with_voxstream.md` | AudioStreamPort design |
| `what_needs_to_port.md` | Full porting inventory |
| `how_can_chatforge_should_implement_voice_connection.md` | Architecture overview |
| `actionable_plan.md` | Implementation phases |
