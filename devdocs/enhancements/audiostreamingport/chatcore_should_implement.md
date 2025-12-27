# Chatforge Enhancements for Voice AI

*What Chatforge needs to absorb VoiceEngine and Voxon functionality.*

---

## Summary

| Enhancement | Priority | Absorbs From | Effort |
|-------------|----------|--------------|--------|
| AudioStreamPort | Critical | VoxStream integration | Medium |
| RealtimeVoiceAPIPort | Critical | VoiceEngine | High |
| VoiceAgent | Critical | VoiceEngine | Medium |
| Session Management | High | Voxon | Medium |
| Conversation Memory | High | Voxon | Medium |
| Identity/Persona Config | Medium | Voxon | Low |
| Voice Strategies | Medium | VoiceEngine | Medium |
| Analytics Integration | Low | Voxon | Low |

---

## 1. Critical: New Ports

### 1.1 AudioStreamPort

**Purpose**: Abstract local audio I/O for real-time streaming.

**Location**: `chatforge/ports/audio_stream.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable, Literal

class AudioStreamPort(ABC):
    """Port for real-time audio capture and playback."""

    # Capture
    @abstractmethod
    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Start capturing audio from microphone.

        Yields:
            Audio chunks as bytes (PCM16, 24kHz, mono).
        """
        ...

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop audio capture."""
        ...

    # Playback
    @abstractmethod
    async def play_chunk(self, chunk: bytes) -> None:
        """Play audio chunk to speaker."""
        ...

    @abstractmethod
    async def stop_playback(self) -> None:
        """Stop playback immediately (for barge-in)."""
        ...

    # VAD
    @abstractmethod
    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None] | None = None,
        on_speech_end: Callable[[bytes], None] | None = None,
    ) -> None:
        """Register VAD event callbacks."""
        ...

    @abstractmethod
    def get_vad_state(self) -> Literal["silence", "speech"]:
        """Get current VAD state."""
        ...

    # Monitoring
    @abstractmethod
    def get_input_level(self) -> float:
        """Get current input level (0.0 to 1.0)."""
        ...

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        ...
```

**Adapters needed**:
- `VoxStreamAdapter` - Desktop (sounddevice)
- `WebRTCAdapter` - Browser
- `TwilioAdapter` - Phone calls
- `NullAudioStreamAdapter` - Testing

---

### 1.2 RealtimeVoiceAPIPort

**Purpose**: Abstract real-time AI API connections (WebSocket-based).

**Location**: `chatforge/ports/realtime.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum

class RealtimeEventType(str, Enum):
    # Input events (to API)
    AUDIO_CHUNK = "audio.chunk"
    TEXT_INPUT = "text.input"
    INTERRUPT = "interrupt"

    # Output events (from API)
    AUDIO_RESPONSE = "audio.response"
    TEXT_RESPONSE = "text.response"
    TRANSCRIPT = "transcript"
    FUNCTION_CALL = "function.call"

    # State events
    SPEECH_STARTED = "speech.started"
    SPEECH_ENDED = "speech.ended"
    RESPONSE_STARTED = "response.started"
    RESPONSE_ENDED = "response.ended"
    ERROR = "error"

@dataclass
class RealtimeEvent:
    type: RealtimeEventType
    data: bytes | str | dict | None = None
    metadata: dict = None

class RealtimeVoiceAPIPort(ABC):
    """Port for real-time AI API connections."""

    @abstractmethod
    async def connect(
        self,
        model: str = "gpt-4o-realtime-preview",
        voice: str = "alloy",
        system_prompt: str | None = None,
        tools: list[dict] | None = None,
    ) -> None:
        """Establish connection to realtime API."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        ...

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """Send audio chunk to API."""
        ...

    @abstractmethod
    async def send_text(self, text: str) -> None:
        """Send text input to API."""
        ...

    @abstractmethod
    async def interrupt(self) -> None:
        """Interrupt current response (barge-in)."""
        ...

    @abstractmethod
    async def send_function_result(
        self,
        call_id: str,
        result: str,
    ) -> None:
        """Send function call result back to API."""
        ...

    @abstractmethod
    def events(self) -> AsyncGenerator[RealtimeEvent, None]:
        """Stream of events from API."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        ...
```

**Adapters needed**:
- `OpenAIRealtimeAdapter` - OpenAI Realtime API
- `GoogleGeminiAdapter` - Google's realtime API (future)
- `MockRealtimeAdapter` - Testing

---

## 2. Critical: VoiceAgent

**Purpose**: Coordinate AudioStreamPort and RealtimeVoiceAPIPort for voice conversations.

**Location**: `chatforge/agent/voice.py`

```python
from dataclasses import dataclass
from typing import Callable
from chatforge.ports.audio_stream import AudioStreamPort
from chatforge.ports.realtime import RealtimeVoiceAPIPort, RealtimeEvent, RealtimeEventType

@dataclass
class VoiceAgentConfig:
    """Configuration for voice agent."""
    model: str = "gpt-4o-realtime-preview"
    voice: str = "alloy"
    system_prompt: str | None = None
    tools: list[dict] | None = None

    # Behavior
    enable_barge_in: bool = True
    vad_silence_threshold_ms: int = 500

    # Strategy (absorbed from VoiceEngine)
    strategy: str = "balanced"  # "fast_lane", "balanced", "quality"

class VoiceAgent:
    """
    Voice conversation agent.

    Coordinates:
    - AudioStreamPort for local audio I/O
    - RealtimeVoiceAPIPort for AI API
    - Tool execution via TicketingPort
    """

    def __init__(
        self,
        audio: AudioStreamPort,
        realtime: RealtimeVoiceAPIPort,
        config: VoiceAgentConfig | None = None,
    ):
        self.audio = audio
        self.realtime = realtime
        self.config = config or VoiceAgentConfig()

        self._is_running = False
        self._is_speaking = False

    async def start(self) -> None:
        """Start voice conversation."""
        # Connect to realtime API
        await self.realtime.connect(
            model=self.config.model,
            voice=self.config.voice,
            system_prompt=self.config.system_prompt,
            tools=self.config.tools,
        )

        # Set up VAD callbacks
        self.audio.set_vad_callbacks(
            on_speech_start=self._handle_speech_start,
            on_speech_end=self._handle_speech_end,
        )

        self._is_running = True

        # Start audio capture → API pipeline
        asyncio.create_task(self._capture_loop())

        # Start API → playback pipeline
        asyncio.create_task(self._playback_loop())

    async def stop(self) -> None:
        """Stop voice conversation."""
        self._is_running = False
        await self.audio.stop_capture()
        await self.audio.stop_playback()
        await self.realtime.disconnect()

    async def _capture_loop(self) -> None:
        """Capture audio and send to API."""
        async for chunk in self.audio.start_capture():
            if not self._is_running:
                break
            await self.realtime.send_audio(chunk)

    async def _playback_loop(self) -> None:
        """Receive API responses and play audio."""
        async for event in self.realtime.events():
            if not self._is_running:
                break

            match event.type:
                case RealtimeEventType.AUDIO_RESPONSE:
                    await self.audio.play_chunk(event.data)

                case RealtimeEventType.FUNCTION_CALL:
                    result = await self._execute_tool(event.data)
                    await self.realtime.send_function_result(
                        event.data["call_id"],
                        result,
                    )

                case RealtimeEventType.RESPONSE_STARTED:
                    self._is_speaking = True

                case RealtimeEventType.RESPONSE_ENDED:
                    self._is_speaking = False

    def _handle_speech_start(self) -> None:
        """User started speaking."""
        if self.config.enable_barge_in and self._is_speaking:
            # Interrupt AI response
            asyncio.create_task(self.audio.stop_playback())
            asyncio.create_task(self.realtime.interrupt())

    def _handle_speech_end(self, audio: bytes) -> None:
        """User stopped speaking."""
        # Could be used for local VAD-triggered commit
        pass

    async def _execute_tool(self, call_data: dict) -> str:
        """Execute tool and return result."""
        # Delegate to TicketingPort
        ...
```

---

## 3. High: Session Management

**Purpose**: Manage conversation sessions (absorbed from Voxon).

**Current state**: Chatforge has basic context but no persistent sessions.

**Enhancement**: Add to StoragePort or create SessionPort.

```python
# Option A: Extend StoragePort
class StoragePort(ABC):
    # Existing methods...

    # New session methods
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        metadata: dict | None = None,
    ) -> str:
        """Create new session, return session_id."""
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None:
        """Get session by ID."""
        ...

    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        metadata: dict,
    ) -> None:
        """Update session metadata."""
        ...

    @abstractmethod
    async def list_sessions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[Session]:
        """List user's sessions."""
        ...

# Option B: Separate SessionPort
class SessionPort(ABC):
    """Port for session management."""
    ...
```

**From Voxon**:
- Session creation/retrieval
- Session state persistence
- Multi-session support
- Session expiry/cleanup

---

## 4. High: Conversation Memory

**Purpose**: Remember conversation history across sessions.

**Current state**: Chatforge tracks messages within a session.

**Enhancement**: Persistent memory with retrieval.

```python
@dataclass
class MemoryEntry:
    content: str
    role: str  # "user", "assistant", "system"
    timestamp: datetime
    session_id: str
    metadata: dict | None = None

class MemoryPort(ABC):
    """Port for conversation memory."""

    @abstractmethod
    async def add_memory(
        self,
        session_id: str,
        content: str,
        role: str,
        metadata: dict | None = None,
    ) -> None:
        """Add memory entry."""
        ...

    @abstractmethod
    async def get_recent_memories(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Get recent memories for session."""
        ...

    @abstractmethod
    async def search_memories(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search memories (vector similarity)."""
        ...

    @abstractmethod
    async def summarize_session(
        self,
        session_id: str,
    ) -> str:
        """Generate summary of session."""
        ...
```

**Adapters**:
- `SQLiteMemoryAdapter` - Local storage
- `PostgresMemoryAdapter` - Production
- `RedisMemoryAdapter` - Fast access
- `PineconeMemoryAdapter` - Vector search

---

## 5. Medium: Identity/Persona Configuration

**Purpose**: Configure agent personality and behavior.

**From Voxon**: Identity profiles like "customer_service", "technical_support".

```python
@dataclass
class AgentIdentity:
    """Agent identity configuration."""
    name: str
    system_prompt: str
    voice: str = "alloy"
    personality_traits: list[str] | None = None

    # Behavior modifiers
    verbosity: str = "normal"  # "brief", "normal", "detailed"
    formality: str = "professional"  # "casual", "professional", "formal"

    # Domain knowledge
    domain: str | None = None  # "customer_service", "technical", etc.
    knowledge_base_ids: list[str] | None = None

# Usage in VoiceAgent
class VoiceAgent:
    def __init__(
        self,
        audio: AudioStreamPort,
        realtime: RealtimeVoiceAPIPort,
        identity: AgentIdentity | None = None,  # NEW
        config: VoiceAgentConfig | None = None,
    ):
        ...
```

---

## 6. Medium: Voice Strategies

**Purpose**: Different modes for latency vs quality tradeoffs.

**From VoiceEngine**: `fast_lane` and `big_lane` strategies.

```python
from enum import Enum

class VoiceStrategy(str, Enum):
    FAST_LANE = "fast_lane"      # Lowest latency, smaller model
    BALANCED = "balanced"        # Default balance
    QUALITY = "quality"          # Best quality, higher latency

@dataclass
class StrategyConfig:
    """Strategy-specific configuration."""

    # Model selection
    model: str

    # Latency tuning
    vad_silence_ms: int
    audio_buffer_ms: int

    # Quality tuning
    temperature: float
    max_tokens: int | None

STRATEGY_PRESETS: dict[VoiceStrategy, StrategyConfig] = {
    VoiceStrategy.FAST_LANE: StrategyConfig(
        model="gpt-4o-mini-realtime",
        vad_silence_ms=300,
        audio_buffer_ms=50,
        temperature=0.7,
        max_tokens=150,
    ),
    VoiceStrategy.BALANCED: StrategyConfig(
        model="gpt-4o-realtime-preview",
        vad_silence_ms=500,
        audio_buffer_ms=100,
        temperature=0.8,
        max_tokens=500,
    ),
    VoiceStrategy.QUALITY: StrategyConfig(
        model="gpt-4o-realtime-preview",
        vad_silence_ms=800,
        audio_buffer_ms=200,
        temperature=0.9,
        max_tokens=None,
    ),
}
```

---

## 7. Low: Analytics Integration

**Purpose**: Track conversation metrics.

**From Voxon**: Analytics and learning.

**Enhancement**: Extend TracingPort or add AnalyticsPort.

```python
@dataclass
class ConversationMetrics:
    session_id: str
    duration_seconds: float
    turn_count: int
    user_words: int
    assistant_words: int
    avg_response_latency_ms: float
    interruption_count: int
    tool_calls: int
    errors: int

class AnalyticsPort(ABC):
    """Port for conversation analytics."""

    @abstractmethod
    async def record_metrics(
        self,
        metrics: ConversationMetrics,
    ) -> None:
        """Record conversation metrics."""
        ...

    @abstractmethod
    async def get_metrics(
        self,
        session_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ConversationMetrics]:
        """Query metrics."""
        ...
```

---

## Implementation Roadmap

### Phase 1: Core Voice (Week 1-2)
1. Create `AudioStreamPort` interface
2. Create `VoxStreamAdapter`
3. Create `RealtimeVoiceAPIPort` interface
4. Create `OpenAIRealtimeAdapter`
5. Create basic `VoiceAgent`

### Phase 2: Sessions & Memory (Week 2-3)
6. Add session methods to `StoragePort`
7. Create `MemoryPort` interface
8. Create `SQLiteMemoryAdapter`
9. Integrate memory into `VoiceAgent`

### Phase 3: Configuration (Week 3-4)
10. Add `AgentIdentity` configuration
11. Implement voice strategies
12. Add strategy presets

### Phase 4: Polish (Week 4+)
13. Add `AnalyticsPort`
14. Add more adapters (WebRTC, Twilio)
15. Documentation and examples

---

## File Structure

```
chatforge/
├── ports/
│   ├── __init__.py
│   ├── messaging.py      # Existing
│   ├── storage.py        # Existing + session methods
│   ├── action.py         # Existing
│   ├── knowledge.py      # Existing
│   ├── tracing.py        # Existing
│   ├── audio_stream.py   # NEW
│   ├── realtime.py       # NEW
│   └── memory.py         # NEW (optional)
├── adapters/
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── voxstream.py  # NEW
│   │   ├── webrtc.py     # NEW (future)
│   │   └── null.py       # NEW
│   ├── realtime/
│   │   ├── __init__.py
│   │   ├── openai.py     # NEW
│   │   └── mock.py       # NEW
│   └── memory/
│       ├── __init__.py
│       └── sqlite.py     # NEW
├── agent/
│   ├── __init__.py
│   ├── engine.py         # Existing ReActAgent
│   └── voice.py          # NEW VoiceAgent
└── config/
    ├── __init__.py
    ├── identity.py       # NEW
    └── strategy.py       # NEW
```

---

## Dependencies

| Enhancement | New Dependencies |
|-------------|------------------|
| AudioStreamPort | None (VoxStream is adapter) |
| RealtimeVoiceAPIPort | `websockets` |
| OpenAIRealtimeAdapter | `openai` (already have) |
| MemoryPort | None |
| SQLiteMemoryAdapter | `aiosqlite` |
| VectorMemoryAdapter | `chromadb` or `pinecone` |

---

## Testing Strategy

Each enhancement tested with:

1. **Unit tests** with mock adapters
2. **Integration tests** with real adapters
3. **Validation** against VoiceEngine (the stable intermediate)

```
Add Chatforge feature
        │
        ▼
Run unit tests (mock adapters)
        │
        ▼
Run integration tests (real adapters)
        │
        ▼
Validate via VoiceEngine
        │
        ├── Pass → Next feature
        │
        └── Fail → Debug, fix
```

---

## Related Documents

| Document | Topic |
|----------|-------|
| `chatforge_compatibility_analysis.md` | Integration analysis |
| `chatforge_voxstream_high_level.md` | AudioStreamPort architecture |
| `chatforge_audioport.md` | Batch audio (AudioPort) |
| `what_is_missing_in_voxstream.md` | VoxStream gaps |
