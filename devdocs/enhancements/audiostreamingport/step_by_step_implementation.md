# AudioStreamPort: Step-by-Step Implementation

**Date:** 2025-01-01
**Prerequisites:** `detailed_desc.md`, `gaps_to_fill/answers/`, `critic.md`, `last_critic.md`
**Estimated Scope:** 4 files, ~400 lines
**Revision:** 3 (post-final-validation)

---

## Overview

```
Step 1: Create port interface
Step 2: Create VoxStreamAdapter
Step 3: Create MockAdapter
Step 4: Wire up exports
Step 5: Write tests
```

---

## Step 1: Create Port Interface

**File:** `chatforge/ports/audio_stream.py`

### 1.1 Define Exception Hierarchy

Following chatforge pattern (all ports have custom exceptions):

```python
class AudioStreamError(Exception):
    """Base exception for AudioStreamPort."""
    pass

class AudioStreamDeviceError(AudioStreamError):
    """Device not found, disconnected, or unavailable."""
    pass

class AudioStreamBufferError(AudioStreamError):
    """Buffer overflow or underflow."""
    pass

class AudioStreamNotInitializedError(AudioStreamError):
    """Adapter used before entering async context."""
    pass
```

### 1.2 Define Config Dataclasses

Two configs needed:
- `AudioStreamConfig` - sample rate, channels, bit depth, chunk duration
- `VADConfig` - thresholds, timing, pre-buffer

Include computed property `bytes_per_chunk` on AudioStreamConfig.

### 1.3 Define Callbacks Dataclass

```python
@dataclass
class AudioCallbacks:
    on_speech_start: Callable[[], None] | None = None
    on_speech_end: Callable[[bytes], None] | None = None  # Receives pre-buffer audio
    on_playback_complete: Callable[[], None] | None = None
    on_error: Callable[[Exception], None] | None = None  # For device errors
```

### 1.4 Define AudioDevice Dataclass

```python
@dataclass
class AudioDevice:
    id: int
    name: str
    channels: int
    is_default: bool
```

### 1.5 Define Abstract Port

Format constants (class-level):
```python
SAMPLE_RATE: int = 24000
CHANNELS: int = 1
FORMAT: str = "pcm16"
```

Key methods:
- Property: `provider_name -> str` (required - all chatforge ports have this)
- Lifecycle: `__aenter__`, `__aexit__`
- Capture: `start_capture() -> AsyncGenerator[bytes, None]`, `stop_capture()`
- Playback: `play()`, `end_playback()`, `stop_playback()`
- Callbacks: `set_callbacks()`
- Devices: `list_input_devices()`, `set_input_device()`
- Config: `get_config()`

```python
class AudioStreamPort(ABC):
    SAMPLE_RATE: int = 24000
    CHANNELS: int = 1
    FORMAT: str = "pcm16"

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the audio provider (e.g., 'voxstream', 'mock')."""
        ...

    # ... other abstract methods
```

All methods are `@abstractmethod`. See `detailed_desc.md` for full signatures.

**Removed from original design** (per critic.md):
- `is_capturing()`, `is_playing()` - caller should track own state
- `get_vad_state()`, `get_vad_config()` - not essential
- `get_input_level()`, `get_output_level()` - unimplemented
- `play_chunk()`, `queue_chunk()` - consolidated into `play()`
- `flush_playback()` - renamed to `end_playback()`

---

## Step 2: Create VoxStreamAdapter

**File:** `chatforge/adapters/audio/voxstream.py`

### 2.1 Constructor

Store configs and initialize state:
```python
def __init__(self, config=None, vad_config=None, mode="realtime"):
    self._config = config or AudioStreamConfig()
    self._vad_config = vad_config or VADConfig()
    self._mode = mode

    self._voxstream = None
    self._vad = None  # VADetector reference for callbacks
    self._callbacks = AudioCallbacks()
    self._capturing = False
    self._input_device: int | None = None

@property
def provider_name(self) -> str:
    return "voxstream"
```

### 2.2 Config Conversion Helper

VoxStream uses its own `StreamConfig`, we need to convert:

```python
def _to_vox_stream_config(self):
    """Convert our AudioStreamConfig to VoxStream's StreamConfig."""
    from voxstream.config.types import StreamConfig as VoxStreamConfig
    return VoxStreamConfig(
        sample_rate=self._config.sample_rate,
        channels=self._config.channels,
        bit_depth=self._config.bit_depth,
        chunk_duration_ms=self._config.chunk_duration_ms,
    )
```

### 2.3 Lifecycle Methods

**`__aenter__`:**
```python
async def __aenter__(self) -> "VoxStreamAdapter":
    from voxstream import VoxStream
    from voxstream.config.types import ProcessingMode

    mode_map = {
        "realtime": ProcessingMode.REALTIME,
        "balanced": ProcessingMode.BALANCED,
        "quality": ProcessingMode.QUALITY,
    }

    # Create VoxStream with proper config object (not sample_rate kwarg!)
    self._voxstream = VoxStream(
        mode=mode_map.get(self._mode, ProcessingMode.REALTIME),
        config=self._to_vox_stream_config(),  # Pass StreamConfig object
    )

    # Configure VAD if enabled
    if self._vad_config.enabled:
        self._setup_vad()

    # Configure input device if set
    if self._input_device is not None:
        self._voxstream.configure_devices(input_device=self._input_device)

    return self
```

**`__aexit__`:**
1. Call `await self._voxstream.cleanup_async()`
2. Set `self._voxstream = None` and `self._vad = None`

### 2.4 Capture Methods

**`start_capture`** - This is the key method:
```python
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    if not self._voxstream:
        raise AudioStreamNotInitializedError("Use 'async with' context first.")
    if self._capturing:
        raise AudioStreamError("Already capturing.")

    self._capturing = True
    queue = await self._voxstream.start_capture_stream()

    try:
        while self._capturing:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=0.1)  # 100ms
                # Feed to VAD if enabled
                if self._vad:
                    self._vad.process_chunk(chunk)
                yield chunk
            except asyncio.TimeoutError:
                continue
    finally:
        self._capturing = False
```

**`stop_capture`:**
- Set `self._capturing = False`

### 2.5 Playback Methods

Direct delegation to VoxStream:
- `play()` → `self._voxstream.queue_playback(chunk)`
- `end_playback()` → `self._voxstream.mark_playback_complete()`
- `stop_playback()` → `self._voxstream.interrupt_playback(force=True)`

### 2.6 VAD Callback Wiring

Bridge VoxStream's no-argument callbacks to our audio-passing callbacks.

**Important:** VoxStream's VADConfig uses `type: VADType` not `enabled: bool`. Map accordingly:

```python
def _setup_vad(self):
    """Wire internal VAD callbacks."""
    from voxstream.voice.vad import VADetector
    from voxstream.config.types import VADConfig as VoxVADConfig, VADType

    # Map our 'enabled' field to VoxStream's 'type' field
    vox_config = VoxVADConfig(
        type=VADType.ENERGY_BASED,  # Our enabled=True means use energy-based VAD
        energy_threshold=self._vad_config.energy_threshold,
        speech_start_ms=self._vad_config.speech_start_ms,
        speech_end_ms=self._vad_config.speech_end_ms,
        pre_buffer_ms=self._vad_config.pre_buffer_ms,
    )

    # Pass audio_config for correct byte/sample calculations
    self._vad = VADetector(
        config=vox_config,
        audio_config=self._to_vox_stream_config(),  # Important for pre-buffer sizing
        on_speech_start=self._on_speech_start,
        on_speech_end=self._on_speech_end,
    )

def _on_speech_start(self):
    """Internal callback - VoxStream passes no arguments."""
    if self._callbacks.on_speech_start:
        try:
            self._callbacks.on_speech_start()
        except Exception as e:
            self._handle_callback_error(e)

def _on_speech_end(self):
    """Internal callback - retrieve pre-buffer and pass to user callback."""
    if self._callbacks.on_speech_end and self._vad:
        try:
            pre_buffer = self._vad.get_pre_buffer()
            if pre_buffer:
                self._callbacks.on_speech_end(pre_buffer)
        except Exception as e:
            self._handle_callback_error(e)

def _handle_callback_error(self, error: Exception):
    """Route callback errors to on_error handler."""
    if self._callbacks.on_error:
        self._callbacks.on_error(error)
```

### 2.7 Device Selection Methods

```python
def list_input_devices(self) -> list[AudioDevice]:
    from voxstream.io.capture import DirectAudioCapture
    devices = DirectAudioCapture.list_devices()
    return [
        AudioDevice(
            id=d["index"],
            name=d["name"],
            channels=d["channels"],
            is_default=d["default"],
        )
        for d in devices
    ]

def set_input_device(self, device_id: int | None) -> None:
    if self._capturing:
        raise RuntimeError("Cannot change device while capturing.")
    self._input_device = device_id
    if self._voxstream:
        self._voxstream.configure_devices(input_device=device_id)
```

### 2.8 Callback and Config Methods

**`set_callbacks`** - Store callbacks AND wire playback completion to VoxStream:
```python
def set_callbacks(self, callbacks: AudioCallbacks) -> None:
    self._callbacks = callbacks

    # Wire playback completion callback to VoxStream if initialized
    if self._voxstream and callbacks.on_playback_complete:
        self._voxstream.set_playback_callbacks(
            completion_callback=callbacks.on_playback_complete
        )
```

**`get_config`:**
```python
def get_config(self) -> AudioStreamConfig:
    return self._config
```

---

## Step 3: Create MockAdapter

**File:** `chatforge/adapters/audio/mock.py`

### 3.1 Purpose

Testing without hardware. Provides:
- Pre-recorded audio for capture
- Collection of played chunks for assertions
- Manual trigger methods for VAD and error events

### 3.2 Constructor

```python
def __init__(self, capture_audio=None, chunk_size=4800, capture_delay_ms=100):
    self._capture_audio = capture_audio or b""
    self._chunk_size = chunk_size
    self._capture_delay = capture_delay_ms / 1000

    self._config = AudioStreamConfig()
    self._callbacks = AudioCallbacks()
    self._capturing = False
    self._input_device: int | None = None

    # Test state for assertions
    self.played_chunks: list[bytes] = []
    self.capture_started = False
    self.capture_stopped = False
    self.playback_stopped = False
    self.end_playback_called = False

@property
def provider_name(self) -> str:
    return "mock"
```

### 3.3 Key Methods

**`start_capture`:**
```python
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    if self._capturing:
        raise RuntimeError("Already capturing.")

    self.capture_started = True
    self._capturing = True

    try:
        for i in range(0, len(self._capture_audio), self._chunk_size):
            if not self._capturing:
                break
            chunk = self._capture_audio[i:i + self._chunk_size]
            await asyncio.sleep(self._capture_delay)  # Simulate real-time
            yield chunk
    finally:
        self._capturing = False
```

**Playback methods:**
```python
async def play(self, chunk: bytes) -> None:
    self.played_chunks.append(chunk)

async def end_playback(self) -> None:
    self.end_playback_called = True
    if self._callbacks.on_playback_complete:
        self._callbacks.on_playback_complete()

async def stop_playback(self) -> None:
    self.playback_stopped = True
```

**Device methods (return mock data):**
```python
def list_input_devices(self) -> list[AudioDevice]:
    return [
        AudioDevice(id=0, name="Mock Microphone", channels=1, is_default=True),
        AudioDevice(id=1, name="Mock USB Mic", channels=2, is_default=False),
    ]

def set_input_device(self, device_id: int | None) -> None:
    if self._capturing:
        raise RuntimeError("Cannot change device while capturing.")
    self._input_device = device_id
```

**Test helpers:**
```python
def simulate_speech_start(self):
    if self._callbacks.on_speech_start:
        self._callbacks.on_speech_start()

def simulate_speech_end(self, audio: bytes = b""):
    if self._callbacks.on_speech_end:
        self._callbacks.on_speech_end(audio)

def simulate_error(self, error: Exception):
    if self._callbacks.on_error:
        self._callbacks.on_error(error)

def get_total_played_bytes(self) -> int:
    return sum(len(c) for c in self.played_chunks)
```

---

## Step 4: Wire Up Exports

### 4.1 Adapter Package Init

**File:** `chatforge/adapters/audio/__init__.py`

```python
from chatforge.adapters.audio.voxstream import VoxStreamAdapter
from chatforge.adapters.audio.mock import MockAudioStreamAdapter

__all__ = ["VoxStreamAdapter", "MockAudioStreamAdapter"]
```

### 4.2 Port Package Export

**File:** `chatforge/ports/__init__.py` (update existing)

Add to exports:
```python
from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    VADConfig,
    AudioDevice,
    AudioCallbacks,
    # Exceptions (all chatforge ports export their exceptions)
    AudioStreamError,
    AudioStreamDeviceError,
    AudioStreamBufferError,
    AudioStreamNotInitializedError,
)
```

### 4.3 Main Adapters Export

**File:** `chatforge/adapters/__init__.py` (update existing)

Add:
```python
from chatforge.adapters.audio import VoxStreamAdapter, MockAudioStreamAdapter
```

### 4.4 NullAdapter (Optional)

**File:** `chatforge/adapters/null.py` (update existing)

Following chatforge pattern, add a NullAudioStreamAdapter for testing without audio:

```python
class NullAudioStreamAdapter(AudioStreamPort):
    """No-op audio adapter for testing without audio hardware."""

    @property
    def provider_name(self) -> str:
        return "null"

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        # Yields nothing, just returns
        return
        yield  # Make it a generator

    async def stop_capture(self) -> None:
        pass

    async def play(self, chunk: bytes) -> None:
        pass  # Discard audio

    async def end_playback(self) -> None:
        pass

    async def stop_playback(self) -> None:
        pass

    def set_callbacks(self, callbacks: AudioCallbacks) -> None:
        pass  # No callbacks fire

    def list_input_devices(self) -> list[AudioDevice]:
        return []

    def set_input_device(self, device_id: int | None) -> None:
        pass

    def get_config(self) -> AudioStreamConfig:
        return AudioStreamConfig()
```

This is useful when audio features are disabled but the code expects an adapter.

---

## Step 5: Write Tests

**Directory:** `tests/adapters/audio/`

### 5.1 Mock Adapter Tests

**File:** `tests/adapters/audio/test_mock.py`

```python
@pytest.mark.asyncio
async def test_capture_yields_chunks():
    audio_data = b"\x00\x01" * 4800  # 2 chunks
    mock = MockAudioStreamAdapter(capture_audio=audio_data, chunk_size=4800)

    async with mock:
        chunks = [c async for c in mock.start_capture()]

    assert len(chunks) == 2
    assert mock.capture_started

@pytest.mark.asyncio
async def test_playback_collects_chunks():
    mock = MockAudioStreamAdapter()

    async with mock:
        await mock.play(b"chunk1")
        await mock.play(b"chunk2")

    assert len(mock.played_chunks) == 2
    assert mock.get_total_played_bytes() == 12

@pytest.mark.asyncio
async def test_end_playback_triggers_callback():
    mock = MockAudioStreamAdapter()
    completed = False

    def on_complete():
        nonlocal completed
        completed = True

    async with mock:
        mock.set_callbacks(AudioCallbacks(
            on_playback_complete=on_complete,
        ))
        await mock.end_playback()

    assert mock.end_playback_called
    assert completed  # Verify callback actually fired

@pytest.mark.asyncio
async def test_speech_callbacks():
    mock = MockAudioStreamAdapter()
    speech_started = False
    speech_audio = None

    def on_start():
        nonlocal speech_started
        speech_started = True

    def on_end(audio):
        nonlocal speech_audio
        speech_audio = audio

    async with mock:
        mock.set_callbacks(AudioCallbacks(
            on_speech_start=on_start,
            on_speech_end=on_end,
        ))

        mock.simulate_speech_start()
        mock.simulate_speech_end(b"pre_buffer_audio")

    assert speech_started
    assert speech_audio == b"pre_buffer_audio"

@pytest.mark.asyncio
async def test_error_callback():
    mock = MockAudioStreamAdapter()
    errors = []

    async with mock:
        mock.set_callbacks(AudioCallbacks(
            on_error=lambda e: errors.append(e),
        ))
        mock.simulate_error(RuntimeError("Device disconnected"))

    assert len(errors) == 1
    assert "disconnected" in str(errors[0])

@pytest.mark.asyncio
async def test_device_selection():
    mock = MockAudioStreamAdapter()

    async with mock:
        devices = mock.list_input_devices()
        assert len(devices) == 2
        assert devices[0].is_default

        mock.set_input_device(1)
        # Should not raise
```

### 5.2 VoxStream Adapter Tests (Integration)

**File:** `tests/adapters/audio/test_voxstream.py`

These require VoxStream installed. Mark with `@pytest.mark.integration`:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_voxstream_adapter_initializes():
    async with VoxStreamAdapter() as audio:
        assert audio.get_config().sample_rate == 24000

@pytest.mark.integration
@pytest.mark.asyncio
async def test_voxstream_capture_yields_audio():
    async with VoxStreamAdapter() as audio:
        chunks = []
        async for chunk in audio.start_capture():
            chunks.append(chunk)
            if len(chunks) >= 5:
                await audio.stop_capture()
                break

        assert len(chunks) == 5
        assert all(isinstance(c, bytes) for c in chunks)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_voxstream_list_devices():
    async with VoxStreamAdapter() as audio:
        devices = audio.list_input_devices()
        assert isinstance(devices, list)
        # At least one device should exist
        assert len(devices) >= 1
```

### 5.3 Port Interface Tests

**File:** `tests/ports/test_audio_stream.py`

Test that both adapters implement the interface correctly:

```python
@pytest.mark.parametrize("adapter_class", [MockAudioStreamAdapter])
@pytest.mark.asyncio
async def test_adapter_implements_port(adapter_class):
    adapter = adapter_class()

    # Verify all abstract methods exist
    assert hasattr(adapter, 'start_capture')
    assert hasattr(adapter, 'stop_capture')
    assert hasattr(adapter, 'play')
    assert hasattr(adapter, 'end_playback')
    assert hasattr(adapter, 'stop_playback')
    assert hasattr(adapter, 'set_callbacks')
    assert hasattr(adapter, 'list_input_devices')
    assert hasattr(adapter, 'set_input_device')
    assert hasattr(adapter, 'get_config')
    assert hasattr(adapter, 'provider_name')

@pytest.mark.asyncio
async def test_provider_name():
    mock = MockAudioStreamAdapter()
    assert mock.provider_name == "mock"
```

---

## File Summary

| File | Lines (est.) | Description |
|------|--------------|-------------|
| `ports/audio_stream.py` | ~120 | Port interface + configs (simplified) |
| `adapters/audio/voxstream.py` | ~150 | VoxStream implementation |
| `adapters/audio/mock.py` | ~100 | Mock for testing |
| `adapters/audio/__init__.py` | ~5 | Exports |
| `tests/adapters/audio/test_mock.py` | ~80 | Mock tests |
| `tests/adapters/audio/test_voxstream.py` | ~40 | Integration tests |

---

## Implementation Order

1. **Port interface first** - Get the API right before implementing
2. **Mock adapter second** - Enables writing tests without hardware
3. **Tests for mock** - Verify mock works
4. **VoxStream adapter** - Real implementation
5. **Integration tests** - Verify VoxStream works

This order lets you test as you go without needing audio hardware until step 4.

---

## Potential Issues

| Issue | Mitigation |
|-------|------------|
| VoxStream not installed | Mock adapter works without it; lazy import in VoxStreamAdapter |
| VAD callbacks race conditions | VAD runs in same thread as process_chunk; callbacks are synchronous |
| Callback exceptions | Wrap in try/except, route to `on_error` callback |
| Audio device not available | VoxStreamAdapter should raise clear error in `__aenter__` |
| Device disconnect mid-capture | Route to `on_error` callback (future enhancement) |
| Queue backpressure | Consumer must keep up; 100ms timeout for responsive shutdown |
| Concurrent capture calls | Raise `RuntimeError("Already capturing.")` |

---

## Changes from Original Design (per critic.md)

| Original | Changed To | Reason |
|----------|------------|--------|
| `play_chunk()` + `queue_chunk()` | `play()` | Were identical; simpler API |
| `flush_playback()` | `end_playback()` | Clearer naming |
| `on_level_change` callback | Removed | Unimplemented |
| `is_capturing()`, `is_playing()` | Removed | Caller should track own state |
| `get_vad_state()` | Removed | Not essential |
| `get_input_level()`, `get_output_level()` | Removed | Unimplemented |
| 1.0s timeout | 0.1s (100ms) | Faster shutdown response |
| No device selection | Added `list_input_devices()`, `set_input_device()` | Missing feature |
| No error callback | Added `on_error` | Handle device errors |

---

## Additional Fixes (per last_critic.md)

Validation against actual chatforge and voxstream codebases revealed these issues:

| Issue | Fix Applied | Location |
|-------|-------------|----------|
| Missing exception hierarchy | Added `AudioStreamError`, `AudioStreamDeviceError`, etc. | Step 1.1 |
| VoxStream constructor mismatch | Use `config=StreamConfig(...)` not `sample_rate=...` | Step 2.2-2.3 |
| Test syntax error | Replaced `nonlocal_set()` with proper `nonlocal` pattern | Step 5.1 |
| Playback callback not wired | Wire in `set_callbacks()` via `set_playback_callbacks()` | Step 2.8 |
| Missing `provider_name` | Added to port and all adapters | Step 1.5, 2.1, 3.2 |
| Missing NullAdapter | Added `NullAudioStreamAdapter` to `adapters/null.py` | Step 4.4 |
| VADConfig field mismatch | Map `enabled=True` to `VADType.ENERGY_BASED` | Step 2.6 |
| VADetector missing audio_config | Pass `audio_config=self._to_vox_stream_config()` | Step 2.6 |
| Missing exception exports | Added all exceptions to port exports | Step 4.2 |

---

## After Implementation

1. Update `chatforge/ports/__init__.py` and `chatforge/adapters/__init__.py`
2. Run tests: `pytest tests/adapters/audio/ -v`
3. Test manually with microphone
4. Document in main README if needed
