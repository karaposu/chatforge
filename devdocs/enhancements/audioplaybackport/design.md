# AudioPlaybackPort Design

## Overview

AudioPlaybackPort abstracts audio output, enabling cross-platform audio playback to speakers, files, or browser-based WebAudio streams.

**Source**: `voxstream/io/player.py` (BufferedAudioPlayer, DirectAudioPlayer)
**Target**: `chatforge/ports/audio_playback.py` + `chatforge/adapters/audio_playback/`

## Problem Statement

Current audio playback is tightly coupled to `sounddevice`:
- Desktop-only (no browser support)
- Single backend (no PyAudio fallback)
- Hard to test without real speakers
- Mixed buffering strategies (direct vs buffered)

## Goals

1. Abstract audio playback behind a clean port interface
2. Enable browser-based playback via WebAudio
3. Support multiple desktop backends (sounddevice, PyAudio)
4. Provide file-based sink for testing/recording
5. Unified playback state and completion tracking

---

## Port Interface

### Core Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Callable
from abc import ABC, abstractmethod

class PlaybackState(Enum):
    """Audio playback state"""
    IDLE = "idle"
    STARTING = "starting"
    BUFFERING = "buffering"
    PLAYING = "playing"
    DRAINING = "draining"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class AudioPlaybackConfig:
    """Configuration for audio playback"""
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    device_id: Optional[str] = None  # None = default device

    # Buffering settings
    min_buffer_chunks: int = 2      # Start after this many chunks
    max_buffer_ms: int = 5000       # Maximum buffer size

    # Latency preference
    latency: str = "low"            # "low", "high", or float seconds

@dataclass
class OutputDevice:
    """Audio output device information"""
    id: str                      # Platform-specific identifier
    name: str                    # Human-readable name
    channels: int                # Max output channels
    sample_rates: List[int]      # Supported sample rates
    is_default: bool = False     # Is system default

@dataclass
class PlaybackMetrics:
    """Metrics for audio playback performance"""
    chunks_received: int = 0
    chunks_played: int = 0
    chunks_buffered: int = 0
    total_bytes_received: int = 0
    total_bytes_played: int = 0
    buffer_duration_ms: float = 0.0
    playback_duration_seconds: float = 0.0
    underruns: int = 0           # Buffer ran empty during playback

    @property
    def buffer_health(self) -> float:
        """Buffer health 0.0-1.0 (1.0 = healthy)"""
        if self.chunks_received == 0:
            return 1.0
        return 1.0 - (self.underruns / self.chunks_received)
```

### Port Interface

```python
class AudioPlaybackPort(ABC):
    """
    Abstract interface for audio playback.

    Implementations provide audio output to various sinks:
    speakers, files, network streams, etc.
    """

    @property
    @abstractmethod
    def state(self) -> PlaybackState:
        """Current playback state"""
        pass

    @property
    @abstractmethod
    def config(self) -> AudioPlaybackConfig:
        """Current configuration"""
        pass

    @property
    @abstractmethod
    def is_playing(self) -> bool:
        """True if actively playing audio (not just buffering)"""
        pass

    @property
    @abstractmethod
    def buffer_duration_ms(self) -> float:
        """Current buffer duration in milliseconds"""
        pass

    @abstractmethod
    def play(self, audio_data: bytes) -> bool:
        """
        Queue audio for playback.

        Args:
            audio_data: PCM16 audio bytes to play

        Returns:
            True if queued successfully, False if buffer full
        """
        pass

    @abstractmethod
    def mark_complete(self) -> None:
        """
        Mark that all audio has been sent.

        Call this after sending the last chunk to enable
        proper completion detection.
        """
        pass

    @abstractmethod
    def stop(self, force: bool = False) -> None:
        """
        Stop playback.

        Args:
            force: If True, stop immediately discarding buffer.
                   If False, drain buffer before stopping.
        """
        pass

    @abstractmethod
    async def wait_until_complete(self, timeout: float = 30.0) -> bool:
        """
        Wait until all queued audio has been played.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        pass

    @abstractmethod
    def get_metrics(self) -> PlaybackMetrics:
        """Get playback performance metrics"""
        pass

    @abstractmethod
    def get_device_info(self) -> Optional[OutputDevice]:
        """Get info about current output device"""
        pass

    @classmethod
    @abstractmethod
    def list_devices(cls) -> List[OutputDevice]:
        """
        List available audio output devices.

        Returns:
            List of available devices, empty if none found.
        """
        pass

    # Callback interface
    def set_callbacks(
        self,
        on_playback_started: Optional[Callable[[], None]] = None,
        on_playback_complete: Optional[Callable[[], None]] = None,
        on_buffer_low: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        Set callbacks for playback events.

        Args:
            on_playback_started: Called when first audio starts playing
            on_playback_complete: Called when all audio has been played
            on_buffer_low: Called when buffer is running low
            on_error: Called on playback error
        """
        self._on_playback_started = on_playback_started
        self._on_playback_complete = on_playback_complete
        self._on_buffer_low = on_buffer_low
        self._on_error = on_error
```

### Exceptions

```python
class AudioPlaybackError(Exception):
    """Base exception for audio playback errors"""
    pass

class DeviceNotFoundError(AudioPlaybackError):
    """Requested output device not found"""
    pass

class DeviceInUseError(AudioPlaybackError):
    """Device is in use by another application"""
    pass

class BufferOverflowError(AudioPlaybackError):
    """Playback buffer is full"""
    pass

class PlaybackTimeoutError(AudioPlaybackError):
    """Playback operation timed out"""
    pass
```

---

## Adapters

### 1. SoundDevicePlaybackAdapter (Primary Desktop)

```python
class SoundDevicePlaybackAdapter(AudioPlaybackPort):
    """
    Audio playback using sounddevice library.

    Best for: Desktop applications (macOS, Windows, Linux)
    Latency: Low (~10-20ms)
    Dependencies: sounddevice, numpy

    Features:
    - Pre-initialized stream for instant start
    - Callback-based for minimal latency
    - Automatic buffer management
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        pre_initialize: bool = True,  # Keep stream warm
    ):
        self._config = config or AudioPlaybackConfig()
        self._pre_initialize = pre_initialize
        self._stream: Optional[sd.OutputStream] = None
        self._state = PlaybackState.IDLE
        self._buffer = bytearray()
        self._buffer_lock = threading.Lock()
        # ... implementation

    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Stream callback - runs in audio thread.
        Pulls data from buffer with minimal latency.
        """
        with self._buffer_lock:
            bytes_needed = frames * self._config.channels * 2

            if len(self._buffer) >= bytes_needed:
                data = self._buffer[:bytes_needed]
                self._buffer = self._buffer[bytes_needed:]
                outdata[:] = np.frombuffer(data, dtype=np.int16).reshape(outdata.shape)
            else:
                outdata.fill(0)  # Silence on underrun
                self._metrics.underruns += 1
```

**Features**:
- Pre-initialized stream for zero-latency start
- Callback-based playback (lowest latency)
- Automatic silence on buffer underrun
- Completion detection

### 2. BufferedPlaybackAdapter (High-Level Desktop)

```python
class BufferedPlaybackAdapter(AudioPlaybackPort):
    """
    Buffered audio playback with smart batching.

    Best for: Streaming scenarios with variable chunk arrival
    Latency: Medium (~50-100ms)
    Dependencies: sounddevice, numpy

    Features:
    - Smart buffering with configurable thresholds
    - Batch playback for efficiency
    - Completion tracking
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        min_buffer_chunks: int = 2,
        max_batch_chunks: int = 5,
    ):
        # ... implementation
```

**Features**:
- Collects chunks before playing
- Handles variable chunk arrival
- Better for streaming from network

### 3. PyAudioPlaybackAdapter (Fallback Desktop)

```python
class PyAudioPlaybackAdapter(AudioPlaybackPort):
    """
    Audio playback using PyAudio (PortAudio binding).

    Best for: Fallback when sounddevice unavailable
    Latency: Medium (~30-50ms)
    Dependencies: pyaudio
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        frames_per_buffer: int = 1024,
    ):
        # ... implementation
```

### 4. WebAudioPlaybackAdapter (Browser)

```python
class WebAudioPlaybackAdapter(AudioPlaybackPort):
    """
    Audio playback to browser via WebSocket.

    Best for: Browser-based applications
    Latency: Variable (network-dependent)

    Usage:
        Works with JavaScript frontend that receives audio
        via WebSocket and plays via Web Audio API.
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        websocket: Optional[WebSocket] = None,
    ):
        # ... implementation

    def play(self, audio_data: bytes) -> bool:
        """Send audio to browser via WebSocket"""
        message = {
            "type": "audio",
            "data": base64.b64encode(audio_data).decode(),
            "sample_rate": self._config.sample_rate,
        }
        self._websocket.send(json.dumps(message))
        return True
```

### 5. FilePlaybackAdapter (Recording/Testing)

```python
class FilePlaybackAdapter(AudioPlaybackPort):
    """
    Audio playback to file (WAV format).

    Best for: Recording, testing, offline processing
    Latency: N/A
    Dependencies: wave (built-in)
    """

    def __init__(
        self,
        file_path: str,
        config: Optional[AudioPlaybackConfig] = None,
        append: bool = False,
    ):
        self._file_path = file_path
        self._config = config or AudioPlaybackConfig()
        self._wav_file: Optional[wave.Wave_write] = None
        # ... implementation

    def play(self, audio_data: bytes) -> bool:
        """Write audio to file"""
        if self._wav_file is None:
            self._open_file()
        self._wav_file.writeframes(audio_data)
        return True
```

### 6. NullPlaybackAdapter (Testing)

```python
class NullPlaybackAdapter(AudioPlaybackPort):
    """
    Null audio playback for testing.

    Discards audio, simulates timing.
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        simulate_timing: bool = True,  # Simulate real playback duration
    ):
        # ... implementation

    def play(self, audio_data: bytes) -> bool:
        """Discard audio, optionally simulate timing"""
        self._metrics.chunks_received += 1
        self._metrics.total_bytes_received += len(audio_data)

        if self._simulate_timing:
            duration = len(audio_data) / 2 / self._config.sample_rate
            asyncio.get_event_loop().call_later(duration, self._on_chunk_played)

        return True
```

---

## Adapter Comparison

| Adapter | Platform | Latency | Buffering | Use Case |
|---------|----------|---------|-----------|----------|
| SoundDevice | Desktop | 10-20ms | Minimal | Real-time voice |
| Buffered | Desktop | 50-100ms | Smart | Streaming |
| PyAudio | Desktop | 30-50ms | Manual | Fallback |
| WebAudio | Browser | Variable | Network | Web apps |
| File | Any | N/A | None | Recording |
| Null | Any | N/A | None | Unit tests |

---

## Usage Examples

### Basic Usage

```python
from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
from chatforge.ports.audio_playback import AudioPlaybackConfig

# Create playback with config
config = AudioPlaybackConfig(sample_rate=24000)
player = SoundDevicePlaybackAdapter(config)

# Set up callbacks
player.set_callbacks(
    on_playback_started=lambda: print("Playing..."),
    on_playback_complete=lambda: print("Done!"),
)

# Play audio chunks
for chunk in audio_chunks:
    player.play(chunk)

# Mark complete and wait
player.mark_complete()
await player.wait_until_complete()
```

### Streaming from API

```python
from chatforge.adapters.audio_playback import BufferedPlaybackAdapter

player = BufferedPlaybackAdapter(
    config=AudioPlaybackConfig(sample_rate=24000),
    min_buffer_chunks=3,  # Buffer before starting
)

async for event in realtime_api.stream():
    if event.type == "audio":
        player.play(event.audio)
    elif event.type == "audio_done":
        player.mark_complete()

await player.wait_until_complete()
```

### Recording to File

```python
from chatforge.adapters.audio_playback import FilePlaybackAdapter

# Record to WAV file
recorder = FilePlaybackAdapter(
    file_path="output.wav",
    config=AudioPlaybackConfig(sample_rate=24000),
)

for chunk in audio_chunks:
    recorder.play(chunk)

recorder.mark_complete()
```

### Interrupt/Barge-in

```python
player = SoundDevicePlaybackAdapter()

# Start playing response
for chunk in response_chunks:
    player.play(chunk)

    # Check for user interrupt
    if user_started_speaking():
        player.stop(force=True)  # Stop immediately
        break

# If not interrupted, mark complete
if not user_started_speaking():
    player.mark_complete()
    await player.wait_until_complete()
```

---

## Integration with VoxStream

### Current VoxStream Usage

```python
# voxstream/core/stream.py
from voxstream.io.player import BufferedAudioPlayer

self._buffered_player = BufferedAudioPlayer(
    config=self.config,
    device=self._output_device,
    on_playback_started=self._on_playback_started_callback,
    on_playback_complete=self._on_playback_complete_callback,
)

self._buffered_player.play(audio_data)
self._buffered_player.mark_complete()
```

### With AudioPlaybackPort

```python
# Updated voxstream usage
from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter

self._player = SoundDevicePlaybackAdapter(
    config=AudioPlaybackConfig(
        device_id=self._output_device,
        sample_rate=self.config.sample_rate,
        channels=self.config.channels,
    )
)

self._player.set_callbacks(
    on_playback_started=self._on_playback_started_callback,
    on_playback_complete=self._on_playback_complete_callback,
)

self._player.play(audio_data)
self._player.mark_complete()
```

---

## File Structure

```
chatforge/
├── ports/
│   ├── __init__.py
│   └── audio_playback.py         # Port interface
└── adapters/
    └── audio_playback/
        ├── __init__.py
        ├── sounddevice.py        # SoundDevicePlaybackAdapter
        ├── buffered.py           # BufferedPlaybackAdapter
        ├── pyaudio.py            # PyAudioPlaybackAdapter
        ├── webaudio.py           # WebAudioPlaybackAdapter
        ├── file.py               # FilePlaybackAdapter
        └── null.py               # NullPlaybackAdapter

tests/
└── adapters/
    └── audio_playback/
        ├── test_sounddevice.py
        ├── test_file.py
        └── fixtures.py
```

---

## State Machine

```
                     play()
    ┌─────────────────────────────────────┐
    │                                     │
    │    ┌──────────────────────────┐     │
    │    │                          │     │
    ▼    ▼                          │     │
┌──────┐    ┌──────────┐    ┌───────────┐ │
│ IDLE │───►│ STARTING │───►│ BUFFERING │─┘
└──────┘    └──────────┘    └───────────┘
    ▲                             │
    │                             │ buffer ready
    │                             ▼
    │       ┌──────────┐    ┌─────────┐
    │       │ STOPPING │◄───│ PLAYING │
    │       └──────────┘    └─────────┘
    │             │               │
    │             │               │ mark_complete()
    │             ▼               ▼
    │       ┌──────────┐    ┌──────────┐
    └───────│   IDLE   │◄───│ DRAINING │
            └──────────┘    └──────────┘
```

---

## Implementation Notes

### Thread Safety

Playback callbacks run in audio threads. Implementations must:
- Protect buffer access with locks
- Use atomic operations for state
- Marshal callbacks to main thread if needed

### Completion Detection

```python
def _check_completion(self):
    """Called periodically or after each chunk plays"""
    with self._buffer_lock:
        if self._is_complete and len(self._buffer) == 0:
            self._state = PlaybackState.IDLE
            if self._on_playback_complete:
                self._on_playback_complete()
            self._completion_event.set()
```

### Pre-initialization

For lowest latency, keep the audio stream warm:

```python
def __init__(self, pre_initialize: bool = True):
    if pre_initialize:
        self._initialize_stream()  # Open but don't play

def _initialize_stream(self):
    """Pre-open audio stream for instant start"""
    self._stream = sd.OutputStream(
        samplerate=self._config.sample_rate,
        channels=self._config.channels,
        dtype='int16',
        callback=self._audio_callback,
        latency='low',
    )
    self._stream.start()  # Outputs silence until data arrives
```

---

## Dependencies

### Required
- None (port interface only)

### Per Adapter
| Adapter | Dependencies |
|---------|-------------|
| SoundDevice | `sounddevice`, `numpy` |
| Buffered | `sounddevice`, `numpy` |
| PyAudio | `pyaudio` |
| WebAudio | `websockets` or framework |
| File | `wave` (built-in) |
| Null | None |

---

## Future Enhancements

1. **Volume Control** - Set/get playback volume
2. **Spatial Audio** - 3D positioning for VR/AR
3. **Multi-Device** - Play to multiple devices simultaneously
4. **Resampling** - Auto-resample to device sample rate
5. **Audio Effects** - Apply effects during playback
6. **Visualization** - Provide audio level data for visualizers
