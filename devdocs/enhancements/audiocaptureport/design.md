# AudioCapturePort Design

## Overview

AudioCapturePort abstracts audio input sources, enabling cross-platform voice capture from microphones, files, or browser-based WebRTC streams.

**Source**: `voxstream/io/capture.py` (DirectAudioCapture)
**Target**: `chatforge/ports/audio_capture.py` + `chatforge/adapters/audio_capture/`

## Problem Statement

Current audio capture is tightly coupled to `sounddevice`:
- Desktop-only (no browser support)
- Single backend (no PyAudio fallback)
- Hard to test without real microphone
- Platform-specific device enumeration

## Goals

1. Abstract audio capture behind a clean port interface
2. Enable browser-based capture via WebRTC/WebAudio
3. Support multiple desktop backends (sounddevice, PyAudio)
4. Provide file-based capture for testing
5. Unified device discovery across platforms

---

## Port Interface

### Core Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, AsyncIterator, List, Callable
from abc import ABC, abstractmethod

class CaptureState(Enum):
    """Audio capture state"""
    IDLE = "idle"
    STARTING = "starting"
    CAPTURING = "capturing"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class AudioCaptureConfig:
    """Configuration for audio capture"""
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100
    device_id: Optional[str] = None  # None = default device
    buffer_size: int = 30  # Queue size

@dataclass
class AudioDevice:
    """Audio input device information"""
    id: str                      # Platform-specific identifier
    name: str                    # Human-readable name
    channels: int                # Max input channels
    sample_rates: List[int]      # Supported sample rates
    is_default: bool = False     # Is system default

    def supports_config(self, config: AudioCaptureConfig) -> bool:
        """Check if device supports the given configuration"""
        return (
            config.channels <= self.channels and
            config.sample_rate in self.sample_rates
        )

@dataclass
class CaptureMetrics:
    """Metrics for audio capture performance"""
    chunks_captured: int = 0
    chunks_dropped: int = 0
    buffer_overruns: int = 0
    total_bytes: int = 0
    capture_duration_seconds: float = 0.0

    @property
    def drop_rate(self) -> float:
        """Percentage of dropped chunks"""
        total = self.chunks_captured + self.chunks_dropped
        return self.chunks_dropped / total if total > 0 else 0.0
```

### Port Interface

```python
class AudioCapturePort(ABC):
    """
    Abstract interface for audio capture.

    Implementations provide audio input from various sources:
    microphones, files, network streams, etc.
    """

    @property
    @abstractmethod
    def state(self) -> CaptureState:
        """Current capture state"""
        pass

    @property
    @abstractmethod
    def config(self) -> AudioCaptureConfig:
        """Current configuration"""
        pass

    @property
    @abstractmethod
    def is_capturing(self) -> bool:
        """True if actively capturing audio"""
        pass

    @abstractmethod
    async def start(self) -> AsyncIterator[bytes]:
        """
        Start audio capture.

        Returns:
            Async iterator yielding audio chunks as bytes.
            Each chunk is PCM16 audio of chunk_duration_ms length.

        Raises:
            AudioCaptureError: If capture fails to start
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop audio capture.

        Blocks until capture is fully stopped.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> CaptureMetrics:
        """Get capture performance metrics"""
        pass

    @abstractmethod
    def get_device_info(self) -> Optional[AudioDevice]:
        """Get info about current capture device"""
        pass

    @classmethod
    @abstractmethod
    def list_devices(cls) -> List[AudioDevice]:
        """
        List available audio input devices.

        Returns:
            List of available devices, empty if none found.
        """
        pass

    # Optional callback interface
    def set_callbacks(
        self,
        on_capture_started: Optional[Callable[[], None]] = None,
        on_capture_stopped: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Set optional callbacks for capture events"""
        self._on_capture_started = on_capture_started
        self._on_capture_stopped = on_capture_stopped
        self._on_error = on_error
```

### Exceptions

```python
class AudioCaptureError(Exception):
    """Base exception for audio capture errors"""
    pass

class DeviceNotFoundError(AudioCaptureError):
    """Requested device not found"""
    pass

class DeviceInUseError(AudioCaptureError):
    """Device is in use by another application"""
    pass

class UnsupportedConfigError(AudioCaptureError):
    """Device doesn't support requested configuration"""
    pass

class CaptureTimeoutError(AudioCaptureError):
    """Capture operation timed out"""
    pass
```

---

## Adapters

### 1. SoundDeviceCaptureAdapter (Primary Desktop)

```python
class SoundDeviceCaptureAdapter(AudioCapturePort):
    """
    Audio capture using sounddevice library.

    Best for: Desktop applications (macOS, Windows, Linux)
    Latency: Low (~10-20ms)
    Dependencies: sounddevice, numpy
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        latency: str = "low",  # "low", "high", or float in seconds
    ):
        self._config = config or AudioCaptureConfig()
        self._latency = latency
        self._stream: Optional[sd.InputStream] = None
        self._state = CaptureState.IDLE
        # ... implementation
```

**Features**:
- Triple-buffered capture for zero drops
- Low latency mode
- Automatic device selection
- Hot-plug detection (optional)

### 2. PyAudioCaptureAdapter (Fallback Desktop)

```python
class PyAudioCaptureAdapter(AudioCapturePort):
    """
    Audio capture using PyAudio (PortAudio binding).

    Best for: Fallback when sounddevice unavailable
    Latency: Medium (~20-50ms)
    Dependencies: pyaudio
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        frames_per_buffer: int = 1024,
    ):
        # ... implementation
```

**Features**:
- Wide platform support
- Stable, mature library
- Good for legacy systems

### 3. WebRTCCaptureAdapter (Browser)

```python
class WebRTCCaptureAdapter(AudioCapturePort):
    """
    Audio capture from browser via WebRTC.

    Best for: Browser-based applications
    Latency: Variable (network-dependent)
    Dependencies: aiortc or browser WebSocket bridge

    Usage:
        Works with a JavaScript frontend that captures audio
        via getUserMedia() and sends it over WebSocket/WebRTC.
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        websocket_url: Optional[str] = None,
    ):
        # ... implementation
```

**Features**:
- Browser audio capture
- Works with WebSocket bridge
- Handles encoding/decoding
- Echo cancellation support (browser-side)

### 4. FileCaptureAdapter (Testing)

```python
class FileCaptureAdapter(AudioCapturePort):
    """
    Audio capture from file (WAV, MP3, etc).

    Best for: Testing, demos, batch processing
    Latency: N/A (simulated real-time)
    Dependencies: wave (built-in), or pydub for other formats
    """

    def __init__(
        self,
        file_path: str,
        config: Optional[AudioCaptureConfig] = None,
        loop: bool = False,
        realtime: bool = True,  # Simulate real-time playback speed
    ):
        # ... implementation
```

**Features**:
- Load from WAV/MP3 files
- Simulate real-time capture
- Loop mode for continuous testing
- Automatic resampling

### 5. NullCaptureAdapter (Testing)

```python
class NullCaptureAdapter(AudioCapturePort):
    """
    Null audio capture for testing.

    Generates silence or configurable test signals.
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        signal: str = "silence",  # "silence", "sine", "noise"
        frequency: int = 440,  # For sine wave
    ):
        # ... implementation
```

---

## Adapter Comparison

| Adapter | Platform | Latency | Dependencies | Use Case |
|---------|----------|---------|--------------|----------|
| SoundDevice | Desktop | 10-20ms | sounddevice, numpy | Primary desktop |
| PyAudio | Desktop | 20-50ms | pyaudio | Fallback |
| WebRTC | Browser | Variable | aiortc / JS bridge | Web apps |
| File | Any | N/A | wave | Testing |
| Null | Any | N/A | None | Unit tests |

---

## Usage Examples

### Basic Usage

```python
from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
from chatforge.ports.audio_capture import AudioCaptureConfig

# Create capture with custom config
config = AudioCaptureConfig(
    sample_rate=24000,
    chunk_duration_ms=100,
)
capture = SoundDeviceCaptureAdapter(config)

# Start capture
async for chunk in await capture.start():
    # Process audio chunk
    process_audio(chunk)

    if should_stop:
        await capture.stop()
        break
```

### Device Selection

```python
# List available devices
devices = SoundDeviceCaptureAdapter.list_devices()
for device in devices:
    print(f"{device.id}: {device.name} ({'DEFAULT' if device.is_default else ''})")

# Use specific device
config = AudioCaptureConfig(device_id="hw:1,0")
capture = SoundDeviceCaptureAdapter(config)
```

### With Callbacks

```python
capture = SoundDeviceCaptureAdapter()

capture.set_callbacks(
    on_capture_started=lambda: print("Recording started"),
    on_capture_stopped=lambda: print("Recording stopped"),
    on_error=lambda e: print(f"Error: {e}"),
)

async for chunk in await capture.start():
    # ...
```

### Testing with File

```python
from chatforge.adapters.audio_capture import FileCaptureAdapter

# Use recorded audio for testing
capture = FileCaptureAdapter(
    file_path="test_audio.wav",
    realtime=True,  # Simulate real-time speed
    loop=True,      # Loop forever
)

async for chunk in await capture.start():
    # Test your processing pipeline
    result = process_audio(chunk)
```

---

## Integration with VoxStream

### Current VoxStream Usage

```python
# voxstream/io/capture.py
self._capture = DirectAudioCapture(
    device=self.config.input_device,
    config=self._audio_config,
)
raw_queue = await self._capture.start_async_capture()
```

### With AudioCapturePort

```python
# Updated voxstream usage
from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter

self._capture = SoundDeviceCaptureAdapter(
    config=AudioCaptureConfig(
        device_id=self.config.input_device,
        sample_rate=self._audio_config.sample_rate,
        channels=self._audio_config.channels,
        chunk_duration_ms=self._audio_config.chunk_duration_ms,
    )
)

# Use async iterator instead of queue
async for chunk in await self._capture.start():
    yield chunk
```

---

## File Structure

```
chatforge/
├── ports/
│   ├── __init__.py
│   └── audio_capture.py          # Port interface
└── adapters/
    └── audio_capture/
        ├── __init__.py
        ├── sounddevice.py        # SoundDeviceCaptureAdapter
        ├── pyaudio.py            # PyAudioCaptureAdapter
        ├── webrtc.py             # WebRTCCaptureAdapter
        ├── file.py               # FileCaptureAdapter
        └── null.py               # NullCaptureAdapter

tests/
└── adapters/
    └── audio_capture/
        ├── test_sounddevice.py
        ├── test_file.py
        └── fixtures.py
```

---

## Implementation Notes

### Thread Safety

Audio callbacks run in separate threads. Implementations must:
- Use thread-safe queues for chunk transfer
- Protect shared state with locks
- Marshal events to async context via `call_soon_threadsafe`

### Buffer Management

```python
# Recommended buffer flow
callback_queue: queue.Queue  # Sync queue for audio thread
async_queue: asyncio.Queue   # Async queue for consumers

async def _transfer_loop():
    """Transfer from sync to async queue"""
    while self.is_capturing:
        try:
            chunk = await loop.run_in_executor(
                None, callback_queue.get, True, 0.1
            )
            await async_queue.put(chunk)
        except queue.Empty:
            continue
```

### Error Recovery

```python
async def start(self) -> AsyncIterator[bytes]:
    try:
        self._state = CaptureState.STARTING
        # Initialize hardware...
        self._state = CaptureState.CAPTURING

        async for chunk in self._capture_loop():
            yield chunk

    except Exception as e:
        self._state = CaptureState.ERROR
        if self._on_error:
            self._on_error(e)
        raise AudioCaptureError(f"Capture failed: {e}") from e
    finally:
        self._state = CaptureState.IDLE
```

---

## Dependencies

### Required
- None (port interface only)

### Per Adapter
| Adapter | Dependencies |
|---------|-------------|
| SoundDevice | `sounddevice`, `numpy` |
| PyAudio | `pyaudio` |
| WebRTC | `aiortc` or custom bridge |
| File | `wave` (built-in), optionally `pydub` |
| Null | None |

---

## Future Enhancements

1. **Hot-plug Detection** - Detect device connect/disconnect
2. **Automatic Fallback** - Fall back to next adapter on failure
3. **Audio Level Monitoring** - Real-time input level callback
4. **Echo Cancellation** - AEC for full-duplex scenarios
5. **Noise Suppression** - Built-in noise reduction option
