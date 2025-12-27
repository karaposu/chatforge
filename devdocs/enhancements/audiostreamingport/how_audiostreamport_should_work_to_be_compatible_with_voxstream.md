# How AudioStreamPort Should Work to be Compatible with VoxStream

*Designing Chatforge's AudioStreamPort interface based on VoxStream's capabilities.*

---

## Part 1: What is VoxStream?

### One-Line Definition

**VoxStream** is a streaming audio I/O abstraction layer that handles microphone capture, speaker playback, and voice activity detection (VAD) with configurable latency modes.

### What VoxStream Does

```
┌─────────────────────────────────────────────────────────────────┐
│                         VoxStream                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Capture   │    │  Processing │    │  Playback   │         │
│  │             │    │             │    │             │         │
│  │ • Mic input │    │ • VAD       │    │ • Speaker   │         │
│  │ • Buffering │    │ • Metrics   │    │ • Buffering │         │
│  │ • Streaming │    │ • Validation│    │ • Interrupt │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │                                        ▲
         ▼                                        │
    🎤 Microphone                            🔊 Speaker
```

### VoxStream's Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Latency-first** | Pre-allocated buffers, zero-copy operations |
| **Mode-based** | REALTIME (10ms), BALANCED (50ms), QUALITY (200ms) |
| **Lazy initialization** | Components created only when needed |
| **Queue-based I/O** | Async queues for capture, thread-safe playback |
| **Callback-driven VAD** | Speech start/end callbacks, not polling |

---

## Part 2: VoxStream's Public API

### Core Methods

```python
class VoxStream:
    # === Audio Capture ===
    async def start_capture_stream(self) -> asyncio.Queue:
        """Start capturing audio from microphone.

        Returns:
            asyncio.Queue that yields audio chunks (bytes).
        """

    async def stop_capture_stream(self) -> None:
        """Stop audio capture."""

    # === Audio Playback ===
    def play_audio(self, audio_data: bytes) -> bool:
        """Play audio immediately (low latency).

        Returns:
            True if playback started successfully.
        """

    def queue_playback(self, audio_data: bytes) -> None:
        """Queue audio for buffered playback (smoother)."""

    def mark_playback_complete(self) -> None:
        """Signal that no more audio will be queued."""

    def interrupt_playback(self, force: bool = True) -> None:
        """Stop playback immediately (for barge-in)."""

    # === Callbacks ===
    def set_playback_callbacks(
        self,
        completion_callback: Callable[[], None] | None = None,
        chunk_played_callback: Callable[[bytes], None] | None = None,
    ) -> None:
        """Set callbacks for playback events."""

    # === VAD (configured via AudioManager) ===
    # VAD callbacks set via configure_vad() or AudioManager

    # === State ===
    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""

    # === Configuration ===
    def configure_devices(
        self,
        input_device: int | str | None = None,
        output_device: int | str | None = None,
    ) -> None:
        """Configure audio input/output devices."""

    def optimize_for_latency(self) -> None:
        """Switch to REALTIME mode (10ms buffer)."""

    def optimize_for_quality(self) -> None:
        """Switch to QUALITY mode (200ms buffer)."""

    # === Cleanup ===
    async def cleanup_async(self) -> None:
        """Release all resources."""
```

### Configuration Objects

```python
@dataclass
class StreamConfig:
    sample_rate: int = 24000      # OpenAI standard
    channels: int = 1             # Mono
    bit_depth: int = 16           # 16-bit PCM
    chunk_duration_ms: int = 100  # Chunk size

@dataclass
class VADConfig:
    energy_threshold: float = 0.02
    speech_start_ms: int = 100    # Confirmation time
    speech_end_ms: int = 500      # Silence confirmation
    pre_buffer_ms: int = 300      # Audio before speech

class ProcessingMode(Enum):
    REALTIME = "realtime"   # 10ms buffer, max 20ms latency
    BALANCED = "balanced"   # 50ms buffer, max 100ms latency
    QUALITY = "quality"     # 200ms buffer, max 500ms latency
```

### VAD Callbacks

VAD is configured through AudioManager internally, but exposes callbacks:

```python
# VAD fires these callbacks:
on_speech_start: Callable[[], None]      # User started speaking
on_speech_end: Callable[[bytes], None]   # User stopped (with buffered audio)
```

---

## Part 3: VoxStream's Internal Architecture

### Component Diagram

```
VoxStream (facade)
    │
    ├── StreamConfig (audio format settings)
    │
    ├── AudioManager (lazy, manages capture/playback)
    │   │
    │   ├── DirectAudioCapture
    │   │   └── sounddevice InputStream
    │   │       └── Callback → Queue → AsyncQueue
    │   │
    │   ├── DirectAudioPlayer (immediate playback)
    │   │   └── sounddevice OutputStream
    │   │       └── Ring buffer in audio thread
    │   │
    │   └── VADetector
    │       └── State machine: SILENCE → SPEECH_STARTING → SPEECH → SPEECH_ENDING
    │
    ├── BufferedAudioPlayer (lazy, queued playback)
    │   └── Daemon thread with smart buffering
    │
    ├── StreamProcessor (audio processing)
    │   └── Validation, normalization, metrics
    │
    └── BufferPool (REALTIME mode only)
        └── Pre-allocated bytearrays for zero-copy
```

### Data Flow: Capture

```
Microphone
    │
    ▼
sounddevice callback (audio thread, must be fast!)
    │
    ▼
callback_queue.put_nowait(audio_bytes)
    │
    ▼
Transfer task (asyncio)
    │
    ▼
asyncio.Queue (returned to caller)
    │
    ▼
async for chunk in queue:
    # Process chunk
```

### Data Flow: Playback

**Immediate (play_audio)**:
```
audio_bytes
    │
    ▼
DirectAudioPlayer._buffer (ring buffer)
    │
    ▼
sounddevice callback reads from buffer
    │
    ▼
Speaker
```

**Buffered (queue_playback)**:
```
audio_bytes
    │
    ▼
BufferedAudioPlayer.buffer (list)
    │
    ▼
Playback thread waits for min_buffer_chunks (2)
    │
    ▼
Batch play up to 5 chunks
    │
    ▼
DirectAudioPlayer
    │
    ▼
Speaker
```

### VAD State Machine

```
              ┌──────────────────────────────────────────────────────┐
              │                                                      │
              ▼                                                      │
        ┌──────────┐                                                 │
        │ SILENCE  │◄───────────────────────────────────┐           │
        └────┬─────┘                                    │           │
             │ speech detected                          │           │
             ▼                                          │           │
    ┌─────────────────┐                                 │           │
    │ SPEECH_STARTING │ (100ms confirmation)            │           │
    └────────┬────────┘                                 │           │
             │ confirmed                     silence    │           │
             ▼                               detected   │           │
        ┌──────────┐                                    │           │
        │  SPEECH  │────────────────────────────────────┤           │
        └────┬─────┘                                    │           │
             │ silence detected                         │           │
             ▼                                          │           │
    ┌─────────────────┐                                 │           │
    │  SPEECH_ENDING  │ (500ms confirmation)            │           │
    └────────┬────────┘                                 │           │
             │ confirmed                                │           │
             └──────────────────────────────────────────┘           │
                                                                     │
             │ speech resumes                                        │
             └───────────────────────────────────────────────────────┘

Callbacks:
- SPEECH_STARTING → confirmed → on_speech_start()
- SPEECH_ENDING → confirmed → on_speech_end(buffered_audio)
```

---

## Part 4: AudioStreamPort Interface Design

### Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Match VoxStream's async model** | Capture is async, playback can be sync |
| **Abstract away buffering modes** | Port user doesn't need to know about BufferedAudioPlayer |
| **Expose VAD as callbacks** | Same pattern as VoxStream |
| **Keep state queries simple** | `is_playing()`, `is_capturing()` |
| **Allow capability discovery** | Not all backends support all features |

### Proposed Interface

```python
# chatforge/ports/audio_stream.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable, Literal

@dataclass
class AudioStreamConfig:
    """Configuration for audio streaming."""
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100

    # VAD settings (optional)
    vad_enabled: bool = True
    vad_speech_start_ms: int = 100
    vad_speech_end_ms: int = 500

    # Latency mode
    mode: Literal["realtime", "balanced", "quality"] = "balanced"


@dataclass
class AudioStreamCapabilities:
    """What this audio backend supports."""
    supports_capture: bool = True
    supports_playback: bool = True
    supports_vad: bool = True
    supports_interrupt: bool = True
    supports_level_monitoring: bool = True
    available_input_devices: list[str] = field(default_factory=list)
    available_output_devices: list[str] = field(default_factory=list)


class AudioStreamPort(ABC):
    """
    Port for real-time audio capture and playback.

    This is the contract that audio backends must implement.
    VoxStream is the primary adapter for this port.
    """

    # =========================================================================
    # CAPTURE
    # =========================================================================

    @abstractmethod
    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """
        Start capturing audio from microphone.

        Yields:
            Audio chunks as bytes (PCM16, configured sample rate, mono).

        Example:
            async for chunk in audio.start_capture():
                await send_to_api(chunk)
        """
        ...

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop audio capture."""
        ...

    @abstractmethod
    def is_capturing(self) -> bool:
        """Check if currently capturing audio."""
        ...

    # =========================================================================
    # PLAYBACK
    # =========================================================================

    @abstractmethod
    async def play_chunk(self, chunk: bytes) -> None:
        """
        Play audio chunk.

        For streaming playback, call this repeatedly with chunks.
        The implementation handles buffering internally.

        Args:
            chunk: Audio bytes (PCM16, same format as capture).
        """
        ...

    @abstractmethod
    async def stop_playback(self) -> None:
        """
        Stop playback immediately.

        Used for barge-in (user interrupts AI).
        """
        ...

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        ...

    # =========================================================================
    # VAD (Voice Activity Detection)
    # =========================================================================

    @abstractmethod
    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None] | None = None,
        on_speech_end: Callable[[bytes], None] | None = None,
    ) -> None:
        """
        Register VAD event callbacks.

        Args:
            on_speech_start: Called when user starts speaking.
            on_speech_end: Called when user stops speaking.
                           Receives buffered audio from speech segment.
        """
        ...

    @abstractmethod
    def get_vad_state(self) -> Literal["silence", "speech"]:
        """Get current VAD state."""
        ...

    # =========================================================================
    # MONITORING
    # =========================================================================

    @abstractmethod
    def get_input_level(self) -> float:
        """
        Get current audio input level.

        Returns:
            Level from 0.0 (silence) to 1.0 (max).
        """
        ...

    @abstractmethod
    def get_output_level(self) -> float:
        """
        Get current audio output level.

        Returns:
            Level from 0.0 (silence) to 1.0 (max).
        """
        ...

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    @abstractmethod
    def get_config(self) -> AudioStreamConfig:
        """Get current audio configuration."""
        ...

    @abstractmethod
    def get_capabilities(self) -> AudioStreamCapabilities:
        """Get capabilities of this audio backend."""
        ...

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize audio subsystem.

        Called once before first use.
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Release all audio resources.

        Called when done with audio.
        """
        ...
```

---

## Part 5: VoxStreamAdapter Implementation

### Mapping VoxStream → AudioStreamPort

| AudioStreamPort | VoxStream Method | Notes |
|-----------------|------------------|-------|
| `start_capture()` | `start_capture_stream()` | Returns AsyncGenerator wrapping queue |
| `stop_capture()` | `stop_capture_stream()` | Direct mapping |
| `is_capturing()` | Internal state check | Track in adapter |
| `play_chunk()` | `play_audio()` or `queue_playback()` | Use queue_playback for smoothness |
| `stop_playback()` | `interrupt_playback()` | Direct mapping |
| `is_playing()` | `is_playing` property | Direct mapping |
| `set_vad_callbacks()` | Via AudioManager/VADetector | Configure during init |
| `get_vad_state()` | Via AudioManager | Track state in adapter |
| `get_input_level()` | Via AudioManager metrics | Expose level |
| `get_config()` | Store config in adapter | Return stored config |
| `get_capabilities()` | Query VoxStream | Build from VoxStream state |
| `initialize()` | Lazy - VoxStream initializes on first use | Optionally pre-initialize |
| `cleanup()` | `cleanup_async()` | Direct mapping |

### Implementation

```python
# chatforge/adapters/audio/voxstream.py

from typing import AsyncGenerator, Callable, Literal
from voxstream import VoxStream, StreamConfig, VADConfig
from voxstream.config.types import ProcessingMode
from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    AudioStreamCapabilities,
)


class VoxStreamAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation using VoxStream.

    Maps Chatforge's audio interface to VoxStream's API.
    """

    def __init__(self, config: AudioStreamConfig | None = None):
        self._config = config or AudioStreamConfig()
        self._voxstream: VoxStream | None = None
        self._is_capturing = False
        self._capture_queue = None

        # VAD callbacks stored for later registration
        self._on_speech_start: Callable[[], None] | None = None
        self._on_speech_end: Callable[[bytes], None] | None = None

        # VAD state tracking
        self._vad_state: Literal["silence", "speech"] = "silence"

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize VoxStream with our configuration."""
        # Map config to VoxStream format
        stream_config = StreamConfig(
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            bit_depth=self._config.bit_depth,
            chunk_duration_ms=self._config.chunk_duration_ms,
        )

        # Map mode
        mode_map = {
            "realtime": ProcessingMode.REALTIME,
            "balanced": ProcessingMode.BALANCED,
            "quality": ProcessingMode.QUALITY,
        }
        mode = mode_map.get(self._config.mode, ProcessingMode.BALANCED)

        # Create VoxStream instance
        self._voxstream = VoxStream(
            config=stream_config,
            mode=mode,
        )

        # Configure VAD if enabled
        if self._config.vad_enabled:
            vad_config = VADConfig(
                speech_start_ms=self._config.vad_speech_start_ms,
                speech_end_ms=self._config.vad_speech_end_ms,
            )
            self._voxstream.configure_vad(vad_config)

    async def cleanup(self) -> None:
        """Release VoxStream resources."""
        if self._voxstream:
            await self._voxstream.cleanup_async()
            self._voxstream = None

    # =========================================================================
    # CAPTURE
    # =========================================================================

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Start capturing and yield audio chunks."""
        if not self._voxstream:
            await self.initialize()

        self._capture_queue = await self._voxstream.start_capture_stream()
        self._is_capturing = True

        try:
            while self._is_capturing:
                try:
                    # Get chunk with timeout to allow checking _is_capturing
                    chunk = await asyncio.wait_for(
                        self._capture_queue.get(),
                        timeout=0.1,
                    )
                    yield chunk
                except asyncio.TimeoutError:
                    continue
        finally:
            self._is_capturing = False

    async def stop_capture(self) -> None:
        """Stop audio capture."""
        self._is_capturing = False
        if self._voxstream:
            await self._voxstream.stop_capture_stream()

    def is_capturing(self) -> bool:
        """Check if currently capturing."""
        return self._is_capturing

    # =========================================================================
    # PLAYBACK
    # =========================================================================

    async def play_chunk(self, chunk: bytes) -> None:
        """Play audio chunk using buffered playback."""
        if not self._voxstream:
            await self.initialize()

        # Use queue_playback for smoother streaming
        self._voxstream.queue_playback(chunk)

    async def stop_playback(self) -> None:
        """Stop playback immediately."""
        if self._voxstream:
            self._voxstream.interrupt_playback(force=True)

    def is_playing(self) -> bool:
        """Check if currently playing."""
        if self._voxstream:
            return self._voxstream.is_playing
        return False

    # =========================================================================
    # VAD
    # =========================================================================

    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None] | None = None,
        on_speech_end: Callable[[bytes], None] | None = None,
    ) -> None:
        """Register VAD callbacks."""
        self._on_speech_start = on_speech_start
        self._on_speech_end = on_speech_end

        # Wrap callbacks to update internal state
        def wrapped_start():
            self._vad_state = "speech"
            if self._on_speech_start:
                self._on_speech_start()

        def wrapped_end(audio: bytes):
            self._vad_state = "silence"
            if self._on_speech_end:
                self._on_speech_end(audio)

        # Register with VoxStream's AudioManager
        # Note: This requires VoxStream to expose VAD callback registration
        if self._voxstream and hasattr(self._voxstream, '_audio_manager'):
            # Implementation depends on VoxStream's internal API
            pass

    def get_vad_state(self) -> Literal["silence", "speech"]:
        """Get current VAD state."""
        return self._vad_state

    # =========================================================================
    # MONITORING
    # =========================================================================

    def get_input_level(self) -> float:
        """Get current input audio level."""
        if self._voxstream:
            metrics = self._voxstream.get_metrics()
            # Extract level from metrics if available
            return metrics.get("input_level", 0.0)
        return 0.0

    def get_output_level(self) -> float:
        """Get current output audio level."""
        if self._voxstream:
            metrics = self._voxstream.get_metrics()
            return metrics.get("output_level", 0.0)
        return 0.0

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self) -> AudioStreamConfig:
        """Get current configuration."""
        return self._config

    def get_capabilities(self) -> AudioStreamCapabilities:
        """Get VoxStream capabilities."""
        return AudioStreamCapabilities(
            supports_capture=True,
            supports_playback=True,
            supports_vad=True,
            supports_interrupt=True,
            supports_level_monitoring=True,
            # Could query sounddevice for actual devices
            available_input_devices=[],
            available_output_devices=[],
        )
```

---

## Part 6: What VoxStream Needs to Expose

For full AudioStreamPort compatibility, VoxStream should expose:

### Currently Available

| Feature | VoxStream API | Status |
|---------|---------------|--------|
| Capture stream | `start_capture_stream()` | ✅ Available |
| Stop capture | `stop_capture_stream()` | ✅ Available |
| Play audio | `play_audio()`, `queue_playback()` | ✅ Available |
| Stop playback | `interrupt_playback()` | ✅ Available |
| Is playing | `is_playing` property | ✅ Available |
| Cleanup | `cleanup_async()` | ✅ Available |
| Metrics | `get_metrics()` | ✅ Available |

### Needs Exposure

| Feature | Needed API | Current State |
|---------|------------|---------------|
| VAD callbacks | Public `set_vad_callbacks()` on VoxStream | Internal to AudioManager |
| VAD state | Public `get_vad_state()` | Internal to VADetector |
| Input level | `get_input_level()` | In metrics, not direct method |
| Is capturing | `is_capturing` property | Not exposed |
| Device listing | `list_audio_devices()` | Not exposed |

### Recommended VoxStream Additions

```python
# Add to VoxStream class:

def set_vad_callbacks(
    self,
    on_speech_start: Callable[[], None] | None = None,
    on_speech_end: Callable[[bytes], None] | None = None,
) -> None:
    """Set VAD callbacks directly on VoxStream."""
    if self._audio_manager:
        self._audio_manager.set_vad_callbacks(on_speech_start, on_speech_end)
    else:
        # Store for later when AudioManager is created
        self._pending_vad_callbacks = (on_speech_start, on_speech_end)

@property
def is_capturing(self) -> bool:
    """Check if currently capturing audio."""
    if hasattr(self, '_audio_manager') and self._audio_manager:
        return self._audio_manager.is_capturing
    return False

def get_vad_state(self) -> str:
    """Get current VAD state ('silence' or 'speech')."""
    if hasattr(self, '_audio_manager') and self._audio_manager:
        return self._audio_manager.get_vad_state()
    return "silence"

def get_input_level(self) -> float:
    """Get current input audio level (0.0 to 1.0)."""
    if hasattr(self, '_audio_manager') and self._audio_manager:
        return self._audio_manager.get_input_level()
    return 0.0
```

---

## Part 7: Design Decisions

### Why AsyncGenerator for Capture?

**VoxStream returns**: `asyncio.Queue`
**AudioStreamPort uses**: `AsyncGenerator[bytes, None]`

Reason: AsyncGenerator is more Pythonic for consumers:

```python
# Queue-based (VoxStream raw):
queue = await voxstream.start_capture_stream()
while True:
    chunk = await queue.get()
    process(chunk)

# Generator-based (AudioStreamPort):
async for chunk in audio.start_capture():
    process(chunk)
```

The adapter wraps the queue in an async generator.

### Why Single play_chunk() Instead of Two Methods?

**VoxStream has**: `play_audio()` (immediate) and `queue_playback()` (buffered)
**AudioStreamPort has**: Just `play_chunk()`

Reason: Simplicity. The adapter chooses the right method internally:
- For streaming AI responses: Use `queue_playback()` for smoothness
- The port user doesn't need to know about buffering strategies

### Why Callbacks for VAD Instead of Events?

**VoxStream uses**: Callbacks (`on_speech_start`, `on_speech_end`)
**AudioStreamPort uses**: Same callback pattern

Reason: Direct callbacks have lower latency than event queues. For VAD, speed matters.

---

## Part 8: Testing Strategy

### Mock Adapter for Testing

```python
class MockAudioStreamAdapter(AudioStreamPort):
    """Mock for testing without real audio."""

    def __init__(self):
        self._capture_chunks: list[bytes] = []
        self._played_chunks: list[bytes] = []
        self._is_capturing = False
        self._is_playing = False
        self._vad_state = "silence"

    # Test helpers
    def queue_capture_chunk(self, chunk: bytes) -> None:
        """Queue a chunk to be yielded by start_capture()."""
        self._capture_chunks.append(chunk)

    def trigger_speech_start(self) -> None:
        """Simulate speech starting."""
        self._vad_state = "speech"
        if self._on_speech_start:
            self._on_speech_start()

    def trigger_speech_end(self, audio: bytes = b"") -> None:
        """Simulate speech ending."""
        self._vad_state = "silence"
        if self._on_speech_end:
            self._on_speech_end(audio)

    def get_played_chunks(self) -> list[bytes]:
        """Get all chunks that were played."""
        return self._played_chunks.copy()
```

### Test Cases

```python
async def test_capture_yields_chunks():
    audio = MockAudioStreamAdapter()
    audio.queue_capture_chunk(b"chunk1")
    audio.queue_capture_chunk(b"chunk2")

    chunks = []
    async for chunk in audio.start_capture():
        chunks.append(chunk)
        if len(chunks) == 2:
            await audio.stop_capture()

    assert chunks == [b"chunk1", b"chunk2"]

async def test_playback_stores_chunks():
    audio = MockAudioStreamAdapter()
    await audio.play_chunk(b"audio1")
    await audio.play_chunk(b"audio2")

    assert audio.get_played_chunks() == [b"audio1", b"audio2"]

async def test_vad_callbacks_fire():
    audio = MockAudioStreamAdapter()
    events = []

    audio.set_vad_callbacks(
        on_speech_start=lambda: events.append("start"),
        on_speech_end=lambda a: events.append(f"end:{len(a)}"),
    )

    audio.trigger_speech_start()
    audio.trigger_speech_end(b"hello")

    assert events == ["start", "end:5"]
```

---

## Summary

### AudioStreamPort Design

```python
class AudioStreamPort(ABC):
    # Capture
    async def start_capture(self) -> AsyncGenerator[bytes, None]: ...
    async def stop_capture(self) -> None: ...
    def is_capturing(self) -> bool: ...

    # Playback
    async def play_chunk(self, chunk: bytes) -> None: ...
    async def stop_playback(self) -> None: ...
    def is_playing(self) -> bool: ...

    # VAD
    def set_vad_callbacks(self, on_start, on_end) -> None: ...
    def get_vad_state(self) -> Literal["silence", "speech"]: ...

    # Monitoring
    def get_input_level(self) -> float: ...
    def get_output_level(self) -> float: ...

    # Config
    def get_config(self) -> AudioStreamConfig: ...
    def get_capabilities(self) -> AudioStreamCapabilities: ...

    # Lifecycle
    async def initialize(self) -> None: ...
    async def cleanup(self) -> None: ...
```

### Compatibility with VoxStream

| AudioStreamPort Method | Maps To VoxStream |
|------------------------|-------------------|
| `start_capture()` | `start_capture_stream()` → wrap queue |
| `stop_capture()` | `stop_capture_stream()` |
| `play_chunk()` | `queue_playback()` |
| `stop_playback()` | `interrupt_playback()` |
| `is_playing()` | `is_playing` property |
| `set_vad_callbacks()` | Needs VoxStream addition |
| `get_vad_state()` | Needs VoxStream addition |
| `cleanup()` | `cleanup_async()` |

### VoxStream Enhancements Needed

1. Public `set_vad_callbacks()` method
2. Public `is_capturing` property
3. Public `get_vad_state()` method
4. Public `get_input_level()` method

---

## Related Documents

| Document | Topic |
|----------|-------|
| `what_needs_to_port.md` | Full porting inventory |
| `actionable_plan.md` | Implementation phases |
| `chatforge_voxstream_high_level.md` | Architecture overview |
