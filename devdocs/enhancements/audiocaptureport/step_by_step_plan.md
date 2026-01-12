# AudioCapturePort Step-by-Step Implementation Plan

## Overview

This plan extracts audio capture from VoxStream into a reusable chatforge port, enabling cross-platform microphone input.

**Source**: `voxstream/io/capture.py` (DirectAudioCapture)
**Target**: `chatforge/ports/audio_capture.py` + `chatforge/adapters/audio_capture/`

---

## Key Design Decisions

Based on critical analysis and lessons from AudioPlaybackPort:

1. **Queue Pattern over AsyncIterator**: Return `asyncio.Queue[bytes]` from `start()` instead of `AsyncIterator[bytes]`. Cleaner stop semantics, matches original VoxStream.

2. **Both Sync and Async Stop**: Provide `stop()` (sync, immediate) and `stop_and_drain()` (async, drains buffers). VoxStream needs sync stop for signal handlers.

3. **Device ID Type**: Use `Union[int, str]` not just `str`. sounddevice uses int indices.

4. **DeviceEnumerable Protocol**: Move `list_devices()` to separate protocol. FileCaptureAdapter and NullCaptureAdapter don't have devices.

5. **Simplified State Machine**: 3 states (IDLE, CAPTURING, ERROR) not 5. STARTING/STOPPING are transient and add complexity.

6. **Callback Deduplication**: Require `_started_notified` and `_stopped_notified` flags. Callbacks must fire exactly once per session.

7. **Drain on Stop**: Transfer loop must drain remaining chunks before exiting.

8. **Dynamic Metrics**: Use properties for `capture_duration_seconds` and `capture_rate`, computed from `start_time`.

9. **Cleanup and Context Manager**: Add `cleanup()` method and both sync/async context manager support.

---

## Phase 1: Create Port Interface

### Step 1.1: Create AudioCapturePort interface file

**File**: `chatforge/ports/audio_capture.py`

```python
# Key components:
# 1. CaptureState enum (3 states: IDLE, CAPTURING, ERROR)
# 2. AudioCaptureConfig dataclass
# 3. AudioDevice dataclass (for input devices)
# 4. CaptureMetrics dataclass with dynamic properties
# 5. DeviceEnumerable protocol
# 6. AudioCapturePort abstract base class
```

**Checklist**:
- [ ] Create `chatforge/ports/audio_capture.py`
- [ ] Define `CaptureState` enum with 3 states:
  ```python
  class CaptureState(Enum):
      IDLE = "idle"        # Not capturing
      CAPTURING = "capturing"  # Actively capturing
      ERROR = "error"      # Error occurred
  ```
- [ ] Define `AudioCaptureConfig` dataclass with fields:
  - `sample_rate: int = 24000`
  - `channels: int = 1`
  - `bit_depth: int = 16`
  - `chunk_duration_ms: int = 100`
  - `device_id: Optional[Union[int, str]] = None`  # FIXED: Union type
  - `callback_buffer_size: int = 30`  # Drops on overflow
  - `async_buffer_size: int = 30`     # Blocks on overflow
- [ ] Define `AudioDevice` dataclass with fields:
  - `id: int`  # Device index (sounddevice uses int)
  - `name: str`
  - `channels: int`
  - `sample_rates: List[int]`
  - `is_default: bool = False`
- [ ] Define `CaptureMetrics` dataclass with:
  - `chunks_captured: int = 0`
  - `chunks_dropped: int = 0`
  - `buffer_overruns: int = 0`
  - `total_bytes: int = 0`
  - `start_time: Optional[float] = None`
  - `@property capture_duration_seconds` (computed dynamically)
  - `@property capture_rate` (chunks per second)
  - `@property drop_rate` (percentage dropped)
- [ ] Define `DeviceEnumerable` Protocol:
  ```python
  class DeviceEnumerable(Protocol):
      @classmethod
      def list_devices(cls) -> List[AudioDevice]: ...
  ```
- [ ] Define `AudioCapturePort` ABC with:
  - `@property state: CaptureState`
  - `@property config: AudioCaptureConfig`
  - `@property is_capturing: bool`
  - `async start() -> asyncio.Queue[bytes]`  # Returns queue, not iterator
  - `stop() -> None`  # Sync, immediate
  - `async stop_and_drain() -> None`  # Async, drains buffers
  - `get_metrics() -> CaptureMetrics`
  - `get_device_info() -> Optional[AudioDevice]`
  - `cleanup() -> None`
  - `set_callbacks(on_started, on_stopped, on_error, on_chunk_captured)`
  - Context manager support (`__enter__`, `__exit__`, `__aenter__`, `__aexit__`)

### Step 1.2: Add exceptions

**In same file** `chatforge/ports/audio_capture.py`:

```python
class AudioCaptureError(Exception):
    """Base exception for audio capture errors."""
    pass

class DeviceNotFoundError(AudioCaptureError):
    """Requested device not found."""
    pass

class DeviceInUseError(AudioCaptureError):
    """Device is in use by another application."""
    pass

class UnsupportedConfigError(AudioCaptureError):
    """Device doesn't support requested configuration."""
    pass

class CaptureTimeoutError(AudioCaptureError):
    """Capture operation timed out."""
    pass
```

**Checklist**:
- [ ] Define `AudioCaptureError` base exception
- [ ] Define `DeviceNotFoundError`
- [ ] Define `DeviceInUseError`
- [ ] Define `UnsupportedConfigError`
- [ ] Define `CaptureTimeoutError`

### Step 1.3: Export from ports package

**File**: `chatforge/ports/__init__.py`

**Checklist**:
- [ ] Add AudioCapturePort exports to `__init__.py`
- [ ] Add to `__all__` list:
  - `AudioCapturePort`
  - `AudioCaptureConfig`
  - `AudioDevice` (note: different from playback's OutputDevice)
  - `CaptureMetrics`
  - `CaptureState`
  - `DeviceEnumerable` (shared with playback or capture-specific)
  - All exceptions

---

## Phase 2: Implement SoundDeviceCaptureAdapter

### Step 2.1: Create adapters directory structure

```bash
mkdir -p chatforge/adapters/audio_capture
touch chatforge/adapters/audio_capture/__init__.py
touch chatforge/adapters/audio_capture/sounddevice_adapter.py
```

**Checklist**:
- [ ] Create `chatforge/adapters/audio_capture/` directory
- [ ] Create `__init__.py`
- [ ] Create `sounddevice_adapter.py`

### Step 2.2: Implement SoundDeviceCaptureAdapter

**File**: `chatforge/adapters/audio_capture/sounddevice_adapter.py`

**Source reference**: `voxstream/io/capture.py` lines 61-295 (DirectAudioCapture class)

```python
class SoundDeviceCaptureAdapter(AudioCapturePort, DeviceEnumerable):
    """
    Audio capture using sounddevice library.

    Features:
        - Queue-based async interface (not iterator)
        - Triple-buffered capture for zero drops
        - Both sync and async stop methods
        - Callback deduplication
        - Proper drain on stop

    Thread Safety:
        - Audio callback runs in sounddevice thread
        - Transfer loop runs in asyncio
        - State protected by threading.Event
    """
```

**Checklist**:
- [ ] Create `SoundDeviceCaptureAdapter` class implementing `AudioCapturePort` and `DeviceEnumerable`
- [ ] Implement `__init__(config: AudioCaptureConfig | None = None, latency: str = "low")`
  - Initialize state variables
  - Calculate chunk size in samples
  - Create queues (sync `callback_queue`, async `audio_queue`)
  - Use `threading.Event` for `_capturing_event` (thread-safe)
  - Initialize callback deduplication flags:
    ```python
    self._started_notified = False
    self._stopped_notified = False
    ```
  - Setup device via `_resolve_device_id()`
- [ ] Implement `_resolve_device_id() -> Optional[int]`
  - Handle `None` → default device
  - Handle `int` → direct index
  - Handle `str` → name matching (case-insensitive substring)
  - Raise `DeviceNotFoundError` if not found
- [ ] Implement `_audio_callback(indata, frames, time_info, status)`
  - Handle callback status (overflow detection → `metrics.buffer_overruns`)
  - Copy audio data (prevent overwrite)
  - Put in `callback_queue` (non-blocking, `put_nowait`)
  - On `queue.Full`: increment `metrics.chunks_dropped`, continue
  - Update `metrics.chunks_captured`
- [ ] Implement `async start() -> asyncio.Queue[bytes]`
  - Validate not already capturing
  - Create and start `sd.InputStream`
  - Set `_capturing_event`
  - Record `metrics.start_time`
  - Fire `on_started` callback (with deduplication)
  - Start transfer task via `asyncio.create_task(_transfer_audio())`
  - Return `audio_queue`
- [ ] Implement `async _transfer_audio()`
  - **CRITICAL**: Drain on stop pattern:
    ```python
    while self._capturing_event.is_set() or not self.callback_queue.empty():
        try:
            audio_array = await loop.run_in_executor(
                None, self.callback_queue.get, True, 0.05
            )
            audio_bytes = audio_array.astype(np.int16).tobytes()
            self.metrics.total_bytes += len(audio_bytes)
            await self.audio_queue.put(audio_bytes)

            # Fire on_chunk_captured callback
            if self._on_chunk_captured:
                try:
                    self._on_chunk_captured(self.metrics.chunks_captured)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")

        except queue.Empty:
            if not self._capturing_event.is_set():
                break  # Only exit when stopped AND queue empty
            continue
    ```
- [ ] Implement `stop() -> None` (sync, immediate)
  - Clear `_capturing_event`
  - Stop and close stream
  - Fire `on_stopped` callback (with deduplication)
  - Log metrics
- [ ] Implement `async stop_and_drain() -> None`
  - Clear `_capturing_event`
  - Wait for transfer task to complete (drains queues)
  - Stop and close stream
  - Fire `on_stopped` callback (with deduplication)
- [ ] Implement `get_metrics() -> CaptureMetrics`
  - Return copy of metrics (dynamic properties computed on access)
- [ ] Implement `get_device_info() -> Optional[AudioDevice]`
- [ ] Implement `cleanup() -> None`
  - Call `stop()` if capturing
  - Clear queues
  - Reset state for reuse
- [ ] Implement `@classmethod list_devices() -> List[AudioDevice]`
  - Query sounddevice for input devices (`max_input_channels > 0`)
  - Convert to `AudioDevice` objects
  - Mark default device
- [ ] Implement properties: `state`, `config`, `is_capturing`
- [ ] Implement context managers:
  ```python
  def __enter__(self) -> "SoundDeviceCaptureAdapter":
      return self

  def __exit__(self, exc_type, exc_val, exc_tb) -> None:
      self.cleanup()

  async def __aenter__(self) -> "SoundDeviceCaptureAdapter":
      return self

  async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
      await self.stop_and_drain()
      self.cleanup()
  ```
- [ ] Implement `set_callbacks()` with all callbacks:
  ```python
  def set_callbacks(
      self,
      on_started: Optional[Callable[[], None]] = None,
      on_stopped: Optional[Callable[[], None]] = None,
      on_error: Optional[Callable[[Exception], None]] = None,
      on_chunk_captured: Optional[Callable[[int], None]] = None,
  ) -> None:
  ```

### Step 2.3: Callback Deduplication Pattern

**CRITICAL**: Apply this pattern for all callbacks:

```python
# In start():
if not self._started_notified and self._on_started:
    self._started_notified = True
    try:
        self._on_started()
    except Exception as e:
        self.logger.error(f"on_started callback error: {e}")

# In stop()/stop_and_drain():
if not self._stopped_notified and self._on_stopped:
    self._stopped_notified = True
    try:
        self._on_stopped()
    except Exception as e:
        self.logger.error(f"on_stopped callback error: {e}")

# Reset flags in cleanup() or start():
self._started_notified = False
self._stopped_notified = False
```

### Step 2.4: Export from adapters package

**File**: `chatforge/adapters/audio_capture/__init__.py`

```python
from chatforge.adapters.audio_capture.sounddevice_adapter import SoundDeviceCaptureAdapter

__all__ = ["SoundDeviceCaptureAdapter"]
```

**Checklist**:
- [ ] Export adapter from `__init__.py`

---

## Phase 3: Implement FileCaptureAdapter

### Step 3.1: Create file adapter

**File**: `chatforge/adapters/audio_capture/file_adapter.py`

```python
class FileCaptureAdapter(AudioCapturePort):
    """
    Audio capture from WAV file.

    For testing without real microphone.
    Does NOT implement DeviceEnumerable (no devices).

    Features:
        - Load WAV file
        - Chunk into appropriate sizes
        - Optional real-time timing simulation
        - Optional loop mode
        - Optional resampling (requires scipy)
    """
```

**Checklist**:
- [ ] Create `FileCaptureAdapter` class implementing `AudioCapturePort` only (no DeviceEnumerable)
- [ ] Implement `__init__(file_path, config, loop=False, realtime=True, resample=False)`
  - Validate file exists
  - If `resample=True`, check scipy availability
  - Load WAV file on init or lazily on start
- [ ] Implement `async start() -> asyncio.Queue[bytes]`
  - Open WAV file
  - Validate sample rate (or resample if enabled)
  - Start async task to chunk and enqueue audio
  - If `realtime=True`, use `asyncio.sleep()` between chunks
  - If `loop=True`, restart from beginning when done
- [ ] Implement `stop()` and `stop_and_drain()`
- [ ] Implement `get_device_info() -> None` (no device)
- [ ] Implement other required methods
- [ ] Add to `__init__.py` exports

**Note on Resampling**:
```python
def __init__(self, ..., resample: bool = False):
    if resample:
        try:
            from scipy.signal import resample as scipy_resample
            self._resample_fn = scipy_resample
        except ImportError:
            raise ImportError(
                "Resampling requires scipy. Install with: pip install scipy"
            )
```

---

## Phase 4: Implement NullCaptureAdapter

### Step 4.1: Create null adapter

**File**: `chatforge/adapters/audio_capture/null_adapter.py`

```python
class NullCaptureAdapter(AudioCapturePort):
    """
    Null audio capture for testing.

    Generates silence or configurable test signals.
    Does NOT implement DeviceEnumerable (no devices).
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        signal: str = "silence",  # "silence", "sine", "noise"
        frequency: int = 440,     # For sine wave
        amplitude: float = 0.5,   # 0.0-1.0
        duration_ms: int = 0,     # 0 = infinite until stop()
    ):
```

**Checklist**:
- [ ] Create `NullCaptureAdapter` implementing `AudioCapturePort` only
- [ ] Implement signal generation (silence, sine, white noise)
- [ ] Implement timing simulation
- [ ] Implement duration limit
- [ ] Add to `__init__.py` exports
- [ ] Add tests

---

## Phase 5: Write Tests

### Step 5.1: Create test file structure

```bash
mkdir -p tests/adapters/audio_capture
touch tests/adapters/audio_capture/__init__.py
touch tests/adapters/audio_capture/test_sounddevice_adapter.py
touch tests/adapters/audio_capture/test_file_adapter.py
touch tests/adapters/audio_capture/test_null_adapter.py
touch tests/adapters/audio_capture/fixtures.py
```

**Checklist**:
- [ ] Create test directory `tests/adapters/audio_capture/`
- [ ] Create `__init__.py`
- [ ] Create test files

### Step 5.2: Create test fixtures

**File**: `tests/adapters/audio_capture/fixtures.py`

```python
# Helpers:
# 1. generate_test_wav(path, duration_ms, frequency) - Create test WAV file
# 2. MockInputStream - Mock sd.InputStream for unit tests
# 3. create_test_config() - Standard test config
```

**Checklist**:
- [ ] Create `generate_test_wav()` helper
- [ ] Create `MockInputStream` for unit testing without hardware
- [ ] Create `create_test_config()` helper

### Step 5.3: Unit tests for SoundDeviceCaptureAdapter

**File**: `tests/adapters/audio_capture/test_sounddevice_adapter.py`

**Test cases**:
```python
# Basic state tests
- test_initial_state_is_idle
- test_start_returns_queue
- test_start_transitions_to_capturing
- test_stop_transitions_to_idle
- test_stop_and_drain_waits_for_transfer

# Callback tests
- test_on_started_fires_once
- test_on_stopped_fires_once
- test_on_chunk_captured_fires_for_each_chunk
- test_callback_exception_caught

# Device tests (hardware marker)
- test_list_devices_returns_list
- test_device_by_index
- test_device_by_name
- test_device_not_found_raises

# Metrics tests
- test_chunks_captured_increments
- test_chunks_dropped_on_overflow
- test_capture_duration_computed
- test_capture_rate_computed

# Context manager tests
- test_context_manager_cleanup
- test_async_context_manager_drains

# Error recovery tests
- test_start_after_error_resets_state
```

**Checklist**:
- [ ] Test start() returns asyncio.Queue
- [ ] Test stop() is sync and immediate
- [ ] Test stop_and_drain() waits for transfer
- [ ] Test callbacks fire exactly once
- [ ] Test metrics update correctly
- [ ] Test device resolution (int and string)
- [ ] Test DeviceNotFoundError for invalid device
- [ ] Test buffer overflow handling
- [ ] Test context manager cleanup

### Step 5.4: Unit tests for NullCaptureAdapter

**File**: `tests/adapters/audio_capture/test_null_adapter.py`

**Test cases**:
```python
- test_generates_silence
- test_generates_sine_wave
- test_generates_noise
- test_respects_duration
- test_no_device_info
- test_metrics_tracked
```

### Step 5.5: Unit tests for FileCaptureAdapter

**File**: `tests/adapters/audio_capture/test_file_adapter.py`

**Test cases**:
```python
- test_load_wav_file
- test_chunk_sizes_match_config
- test_loop_mode
- test_realtime_timing
- test_file_not_found
- test_sample_rate_mismatch_error
- test_resample_requires_scipy
```

---

## Phase 6: Integrate with VoxStream

### Step 6.1: Update VoxStream to accept AudioCapturePort

**File**: `voxstream/core/stream.py`

```python
from chatforge.ports.audio_capture import AudioCapturePort
from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter

class VoxStream:
    def __init__(
        self,
        ...
        capture: Optional[AudioCapturePort] = None,  # NEW: Inject capture
        ...
    ):
        if capture:
            self._capture = capture
        else:
            self._capture = SoundDeviceCaptureAdapter(
                AudioCaptureConfig(
                    device_id=self.config.input_device,
                    sample_rate=self._audio_config.sample_rate,
                    channels=self._audio_config.channels,
                    chunk_duration_ms=self._audio_config.chunk_duration_ms,
                )
            )
```

**Checklist**:
- [ ] Add `capture: AudioCapturePort | None = None` parameter
- [ ] Import types from chatforge
- [ ] Create default adapter if not provided
- [ ] Update `start_capture_stream()` to use queue pattern:
  ```python
  async def start_capture_stream(self):
      self._audio_queue = await self._capture.start()
      # Consume from queue instead of iterator
  ```
- [ ] Update `stop_capture_stream()` to call sync `stop()`:
  ```python
  def stop_capture_stream(self):
      self._capture.stop()  # Sync!
  ```
- [ ] Maintain backward compatibility

### Step 6.2: Verify voxterm still works

**Checklist**:
- [ ] Run voxterm with default adapter
- [ ] Test microphone capture works
- [ ] Test start/stop functionality
- [ ] Verify metrics are reported correctly
- [ ] Test with FileCaptureAdapter for automated testing

---

## Phase 7: Documentation

### Step 7.1: Create usage examples

**File**: `chatforge/adapters/audio_capture/README.md`

```markdown
# Audio Capture Adapters

## Quick Start

```python
from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
from chatforge.ports.audio_capture import AudioCaptureConfig

# Create adapter
capture = SoundDeviceCaptureAdapter()

# Start capture - returns a queue
audio_queue = await capture.start()

# Consume audio
while capture.is_capturing:
    chunk = await audio_queue.get()
    process_audio(chunk)

    if should_stop:
        capture.stop()  # Sync stop
        break

# Or use context manager
async with SoundDeviceCaptureAdapter() as capture:
    audio_queue = await capture.start()
    async for chunk in iter_queue(audio_queue):
        process_audio(chunk)
# Automatically drains and cleans up
```

## Device Selection

```python
# List devices
devices = SoundDeviceCaptureAdapter.list_devices()
for device in devices:
    print(f"{device.id}: {device.name} ({'DEFAULT' if device.is_default else ''})")

# By index
config = AudioCaptureConfig(device_id=2)

# By name (substring match)
config = AudioCaptureConfig(device_id="MacBook")
```

## Testing with Files

```python
from chatforge.adapters.audio_capture import FileCaptureAdapter

capture = FileCaptureAdapter(
    file_path="test_audio.wav",
    realtime=True,  # Simulate real-time speed
    loop=True,      # Loop forever
)
```
```

**Checklist**:
- [ ] Create README.md with examples
- [ ] Document queue pattern usage
- [ ] Document device discovery
- [ ] Document context manager usage
- [ ] Document testing patterns

---

## Verification Checklist

### Phase 1 Complete
- [ ] `chatforge/ports/audio_capture.py` exists with full interface
- [ ] `CaptureState` has 3 states (IDLE, CAPTURING, ERROR)
- [ ] `start()` returns `asyncio.Queue[bytes]`
- [ ] Both `stop()` (sync) and `stop_and_drain()` (async) exist
- [ ] `DeviceEnumerable` is a separate protocol
- [ ] `device_id` is `Union[int, str]`
- [ ] Exports work: `from chatforge.ports import AudioCapturePort`

### Phase 2 Complete
- [ ] `SoundDeviceCaptureAdapter` implements both `AudioCapturePort` and `DeviceEnumerable`
- [ ] Callback deduplication implemented
- [ ] Transfer loop drains on stop
- [ ] Device resolution handles int and string
- [ ] Context managers work

### Phase 3-4 Complete
- [ ] `FileCaptureAdapter` works without DeviceEnumerable
- [ ] `NullCaptureAdapter` generates test signals

### Phase 5 Complete
- [ ] All unit tests pass
- [ ] Test coverage > 80%

### Phase 6 Complete
- [ ] VoxStream accepts `capture: AudioCapturePort`
- [ ] Backward compatibility maintained
- [ ] voxterm works with new capture

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `chatforge/ports/audio_capture.py` | AudioCapturePort interface |
| `chatforge/adapters/audio_capture/__init__.py` | Adapter exports |
| `chatforge/adapters/audio_capture/sounddevice_adapter.py` | SoundDevice adapter |
| `chatforge/adapters/audio_capture/file_adapter.py` | File-based adapter |
| `chatforge/adapters/audio_capture/null_adapter.py` | Null adapter for testing |
| `tests/adapters/audio_capture/test_*.py` | Unit tests |
| `tests/adapters/audio_capture/fixtures.py` | Test helpers |

### Modified Files

| File | Changes |
|------|---------|
| `chatforge/ports/__init__.py` | Add AudioCapturePort exports |
| `voxstream/core/stream.py` | Accept `capture: AudioCapturePort` param |

---

## Dependencies

### Required
- numpy (already in voxstream)

### Per Adapter
| Adapter | Dependencies |
|---------|-------------|
| SoundDevice | `sounddevice`, `numpy` |
| File | `wave` (built-in), optionally `scipy` for resampling |
| Null | None |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking VoxStream audio capture | Maintain backward compatibility with default adapter |
| Data loss on stop | Transfer loop drains before exiting |
| Callback fires multiple times | Deduplication flags |
| Device selection by name fails | Support both int index and string name |
| Thread safety issues | Use `threading.Event` for `is_capturing` |
| Async iterator complexity | **Avoided**: Use queue pattern instead |
