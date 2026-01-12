# AudioCapturePort Critical Analysis

## Executive Summary

The AudioCapturePort step-by-step plan has **4 critical issues**, **5 major issues**, **4 moderate issues**, and **3 minor issues** that should be addressed before implementation. The most significant problems are the AsyncIterator pattern complexity, async/sync mismatches, device ID type, and missing lessons learned from AudioPlaybackPort implementation.

---

## Issues by Severity

### CRITICAL (4 issues) - Will cause implementation failures

#### Issue 1: AsyncIterator Pattern Breaks Stop Semantics

**Location**: `start() -> AsyncIterator[bytes]` interface

**Problem**: The proposed pattern is awkward and has unclear stop semantics:

```python
# Proposed usage
async for chunk in await capture.start():
    process(chunk)
    if should_stop:
        await capture.stop()  # How does this interact with the iterator?
        break
```

Issues:
1. `await capture.start()` returns iterator, then iterate - confusing syntax
2. If you `break` without calling `stop()`, does the stream close?
3. How does `stop()` signal the iterator to stop yielding?
4. What happens to chunks in flight when stop is called?

**Original VoxStream** returns a queue, which is cleaner:
```python
queue = await capture.start_async_capture()
while self.is_capturing:
    chunk = await queue.get()
    process(chunk)
# Just stop consuming - no iterator to break
```

**Recommendation**: Keep the queue pattern OR use context manager:
```python
# Option A: Queue pattern (matches original)
async def start(self) -> asyncio.Queue[bytes]:

# Option B: Context manager
async with capture.stream() as chunks:
    async for chunk in chunks:
        process(chunk)
# Cleanup happens automatically on exit
```

---

#### Issue 2: Async/Sync Mismatch for stop()

**Location**: `async def stop() -> None`

**Problem**: Plan proposes async stop:
```python
async def stop(self) -> None:
```

But original VoxStream is sync:
```python
def stop_capture(self):  # sync!
    self.is_capturing = False
    if self.stream:
        self.stream.stop()
        self.stream.close()
```

VoxStream calls `stop_capture()` from sync context in signal handlers and cleanup code. Making it async breaks compatibility.

**Risk**: Integration with VoxStream will require wrapping async in `asyncio.run()` everywhere, or major refactoring.

**Recommendation**: Provide both like AudioPlaybackPort:
```python
def stop(self) -> None:
    """Sync stop - immediate, may lose buffered data."""

async def stop_and_drain(self) -> None:
    """Async stop - drains remaining chunks first."""
```

---

#### Issue 3: Device ID Type Mismatch (Same as AudioPlaybackPort)

**Location**: `AudioCaptureConfig.device_id`

**Problem**: Plan defines:
```python
device_id: Optional[str] = None
```

But original and sounddevice use int indices:
```python
# Original VoxStream
device: Optional[Union[int, str]] = None

# sounddevice usage
sd.query_devices(self.device, 'input')  # Expects int
sd.default.device[0]  # Returns int
```

**Risk**: Same issue we fixed in AudioPlaybackPort. Device selection by name won't work without mapping logic.

**Recommendation**:
```python
device_id: Optional[Union[int, str]] = None

def _resolve_device_id(self) -> Optional[int]:
    """Resolve string device name to int index."""
    if isinstance(self._config.device_id, int):
        return self._config.device_id
    if isinstance(self._config.device_id, str):
        for i, dev in enumerate(sd.query_devices()):
            if self._config.device_id.lower() in dev['name'].lower():
                if dev['max_input_channels'] > 0:
                    return i
    return None
```

---

#### Issue 4: list_devices() as Abstract Class Method

**Location**: `AudioCapturePort` ABC

**Problem**: Interface requires:
```python
@classmethod
@abstractmethod
def list_devices(cls) -> List[AudioDevice]:
```

But `FileCaptureAdapter` and `NullCaptureAdapter` don't have "devices". They must implement a method that makes no semantic sense.

**Same issue we fixed in AudioPlaybackPort.**

**Recommendation**: Use DeviceEnumerable protocol:
```python
class DeviceEnumerable(Protocol):
    @classmethod
    def list_devices(cls) -> List[AudioDevice]: ...

class SoundDeviceCaptureAdapter(AudioCapturePort, DeviceEnumerable):
    # Has list_devices()

class FileCaptureAdapter(AudioCapturePort):
    # No list_devices()
```

---

### MAJOR (5 issues) - Will cause significant problems

#### Issue 5: Missing Callback Deduplication

**Location**: `set_callbacks()` in interface

**Problem**: Plan adds callbacks but doesn't mention deduplication:
```python
def set_callbacks(
    on_capture_started: Optional[Callable[[], None]] = None,
    on_capture_stopped: Optional[Callable[[], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
)
```

**Lesson from AudioPlaybackPort**: Without `_started_notified` and `_stopped_notified` flags, callbacks can fire multiple times, corrupting state machines that depend on exactly-once semantics.

**Recommendation**: Add to implementation requirements:
```python
# Required implementation pattern
self._started_notified = False
self._stopped_notified = False

# In capture start:
if not self._started_notified and self._on_capture_started:
    self._started_notified = True
    try:
        self._on_capture_started()
    except Exception as e:
        self.logger.error(f"Callback error: {e}")
```

---

#### Issue 6: Transfer Loop Doesn't Drain on Stop

**Location**: `_transfer_audio()` in SoundDeviceCaptureAdapter

**Problem**: Original implementation:
```python
async def _transfer_audio(self):
    while self.is_capturing:  # Exits immediately when flag is False
        try:
            audio_array = await loop.run_in_executor(...)
            await self.audio_queue.put(...)
        except queue.Empty:
            continue
```

When `is_capturing` becomes `False`, the loop exits but `callback_queue` may still have data. This data is lost.

**Risk**: Last few chunks of audio are silently dropped on every stop.

**Recommendation**:
```python
async def _transfer_audio(self):
    while self.is_capturing or not self.callback_queue.empty():
        try:
            audio_array = await loop.run_in_executor(
                None, self.callback_queue.get, True, 0.05
            )
            await self.audio_queue.put(...)
        except queue.Empty:
            if not self.is_capturing:
                break  # Only exit when stopped AND queue empty
            continue
```

---

#### Issue 7: State Machine Overcomplexity

**Location**: `CaptureState` enum

**Problem**: Plan proposes 5 states:
```python
IDLE, STARTING, CAPTURING, STOPPING, ERROR
```

Original VoxStream uses simple boolean:
```python
self.is_capturing = False  # That's it
```

STARTING and STOPPING are transient states that add complexity without clear value. What operations are valid in STARTING vs CAPTURING? What's the timeout for STARTING?

**Recommendation**: Simplify to 3 states:
```python
class CaptureState(Enum):
    IDLE = "idle"        # Not capturing
    CAPTURING = "capturing"  # Actively capturing
    ERROR = "error"      # Error occurred
```

The transition is atomic - either you're capturing or you're not.

---

#### Issue 8: Metrics Missing Dynamic Properties

**Location**: `CaptureMetrics` dataclass

**Problem**: Plan defines:
```python
@dataclass
class CaptureMetrics:
    capture_duration_seconds: float = 0.0  # Static field
```

But original computes dynamically:
```python
@property
def capture_duration(self) -> float:
    if self.start_time == 0:
        return 0.0
    return time.time() - self.start_time

@property
def capture_rate(self) -> float:
    duration = self.capture_duration
    return self.chunks_captured / duration if duration > 0 else 0.0
```

**Missing from plan**:
- `start_time` for dynamic calculation
- `capture_rate` property
- `avg_chunk_latency_ms` (time from callback to queue put)

**Recommendation**:
```python
@dataclass
class CaptureMetrics:
    chunks_captured: int = 0
    chunks_dropped: int = 0
    buffer_overruns: int = 0
    total_bytes: int = 0
    start_time: Optional[float] = None

    @property
    def capture_duration_seconds(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    @property
    def capture_rate(self) -> float:
        duration = self.capture_duration_seconds
        return self.chunks_captured / duration if duration > 0 else 0.0

    @property
    def drop_rate(self) -> float:
        total = self.chunks_captured + self.chunks_dropped
        return self.chunks_dropped / total if total > 0 else 0.0
```

---

#### Issue 9: No cleanup() Method

**Location**: `AudioCapturePort` ABC

**Problem**: Plan doesn't include explicit cleanup:
- No `cleanup()` method
- No context manager support
- Original relies on `stop_capture()` for cleanup

**Risk**: Resource leaks if consumer forgets to call stop().

**Recommendation**: Add to interface:
```python
@abstractmethod
def cleanup(self) -> None:
    """Release all resources. Safe to call multiple times."""
    pass

def __enter__(self) -> "AudioCapturePort":
    return self

def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self.cleanup()

async def __aenter__(self) -> "AudioCapturePort":
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
    await self.stop_and_drain()
    self.cleanup()
```

---

### MODERATE (4 issues) - Should be addressed

#### Issue 10: Back-pressure Handling Unclear

**Location**: Buffer management

**Problem**: Original has mismatched behavior:
```python
# callback_queue - drops on full
self.callback_queue.put_nowait(audio_copy)  # Raises Full, chunk dropped

# audio_queue - blocks on full
await self.audio_queue.put(audio_bytes)  # Blocks forever
```

If consumer is slow:
1. `audio_queue` fills up
2. `_transfer_audio` blocks on `put()`
3. `callback_queue` fills up
4. Audio callback starts dropping chunks

Plan mentions `buffer_size: int = 30` but doesn't clarify which queue or behavior.

**Recommendation**: Document clearly:
```python
@dataclass
class AudioCaptureConfig:
    # ...
    callback_buffer_size: int = 30  # Drops on overflow (metrics.chunks_dropped)
    async_buffer_size: int = 30     # Blocks on overflow (back-pressure)
```

---

#### Issue 11: FileCaptureAdapter Resampling Complexity

**Location**: Phase 3 (FileCaptureAdapter)

**Problem**: Plan casually mentions "Automatic resampling" but this requires:
- scipy (`scipy.signal.resample`) or
- librosa (`librosa.resample`) or
- Custom implementation

This adds significant dependencies and complexity.

**Recommendation**:
1. Make resampling optional
2. Require input file to match config sample rate by default
3. Add optional resampling with explicit dependency:
```python
class FileCaptureAdapter:
    def __init__(
        self,
        file_path: str,
        config: AudioCaptureConfig = None,
        resample: bool = False,  # Requires scipy
    ):
        if resample:
            try:
                from scipy.signal import resample
            except ImportError:
                raise ImportError("Resampling requires scipy")
```

---

#### Issue 12: Error State Recovery Undefined

**Location**: CaptureState.ERROR handling

**Problem**: Plan defines ERROR state but no recovery path:
- Can you call `start()` after ERROR?
- Is there a `reset()` method?
- Does ERROR auto-clear on next `start()`?

**Recommendation**: Define recovery:
```python
async def start(self) -> AsyncIterator[bytes]:
    # Auto-reset from ERROR state
    if self._state == CaptureState.ERROR:
        self._reset()
    # ... proceed with start

def _reset(self) -> None:
    """Reset adapter state for reuse."""
    self._state = CaptureState.IDLE
    self._started_notified = False
    self._stopped_notified = False
    self._metrics = CaptureMetrics()
```

---

#### Issue 13: is_capturing Thread Safety

**Location**: `is_capturing` flag

**Problem**: Original uses simple bool:
```python
self.is_capturing = False
```

Accessed from three contexts:
1. Audio callback thread (sounddevice)
2. Transfer asyncio task
3. Main consumer

While Python's GIL makes this "safe enough" for bools, it's not proper thread safety.

**Recommendation**: Use threading.Event for proper synchronization:
```python
self._capturing_event = threading.Event()

@property
def is_capturing(self) -> bool:
    return self._capturing_event.is_set()

def _start_capturing(self):
    self._capturing_event.set()

def _stop_capturing(self):
    self._capturing_event.clear()
```

---

### MINOR (3 issues) - Nice to fix

#### Issue 14: AudioDevice.supports_config Too Strict

**Location**: `AudioDevice.supports_config()`

**Problem**:
```python
def supports_config(self, config: AudioCaptureConfig) -> bool:
    return (
        config.channels <= self.channels and
        config.sample_rate in self.sample_rates
    )
```

`sample_rate in self.sample_rates` is too strict. sounddevice can often resample internally.

**Recommendation**: Make it a soft check or include supported range:
```python
def supports_config(self, config: AudioCaptureConfig) -> bool:
    # Channel check is strict
    if config.channels > self.channels:
        return False
    # Sample rate check is soft (sounddevice may resample)
    if self.sample_rates and config.sample_rate not in self.sample_rates:
        # Warn but allow
        pass
    return True
```

---

#### Issue 15: NullCaptureAdapter Signal Options Unclear

**Location**: Phase 6 (NullCaptureAdapter)

**Problem**: Plan mentions:
```python
signal: str = "silence",  # "silence", "sine", "noise"
```

But doesn't specify:
- What frequency/amplitude for sine?
- What type of noise (white, pink)?
- How long to generate before stopping?

**Recommendation**: Clarify in implementation:
```python
class NullCaptureAdapter:
    def __init__(
        self,
        config: AudioCaptureConfig = None,
        signal: str = "silence",
        frequency: int = 440,     # For sine
        amplitude: float = 0.5,   # 0.0-1.0
        duration_ms: int = 0,     # 0 = infinite
    ):
```

---

#### Issue 16: Missing on_chunk_captured Callback

**Location**: Callback interface

**Problem**: Plan has on_capture_started and on_capture_stopped but no per-chunk callback like AudioPlaybackPort's on_chunk_played.

**Recommendation**: Add for progress tracking:
```python
def set_callbacks(
    on_capture_started: Optional[Callable[[], None]] = None,
    on_capture_stopped: Optional[Callable[[], None]] = None,
    on_chunk_captured: Optional[Callable[[int], None]] = None,  # chunk_count
    on_error: Optional[Callable[[Exception], None]] = None,
)
```

---

## Summary Table

| # | Issue | Severity | Category |
|---|-------|----------|----------|
| 1 | AsyncIterator pattern breaks stop semantics | Critical | Interface |
| 2 | Async/Sync mismatch for stop() | Critical | Interface |
| 3 | Device ID type mismatch (str vs Union[int,str]) | Critical | Config |
| 4 | list_devices() as abstract class method | Critical | Interface |
| 5 | Missing callback deduplication | Major | Integration |
| 6 | Transfer loop doesn't drain on stop | Major | Data loss |
| 7 | State machine overcomplexity (5 states) | Major | Design |
| 8 | Metrics missing dynamic properties | Major | Observability |
| 9 | No cleanup() method | Major | Resources |
| 10 | Back-pressure handling unclear | Moderate | Documentation |
| 11 | FileCaptureAdapter resampling complexity | Moderate | Dependencies |
| 12 | Error state recovery undefined | Moderate | State |
| 13 | is_capturing thread safety | Moderate | Threading |
| 14 | AudioDevice.supports_config too strict | Minor | Validation |
| 15 | NullCaptureAdapter signal options unclear | Minor | Documentation |
| 16 | Missing on_chunk_captured callback | Minor | Observability |

---

## Recommended Fixes Priority

### Before Implementation (Must Fix)
1. **Issue 1**: Change to queue pattern or context manager
2. **Issue 2**: Add sync `stop()` alongside async `stop_and_drain()`
3. **Issue 3**: Fix device_id type to `Union[int, str]`
4. **Issue 4**: Use DeviceEnumerable protocol for list_devices()
5. **Issue 5**: Add callback deduplication requirement

### During Implementation (Should Fix)
6. **Issue 6**: Drain transfer loop on stop
7. **Issue 7**: Simplify state machine to 3 states
8. **Issue 8**: Add dynamic metrics properties
9. **Issue 9**: Add cleanup() and context manager support

### Post-Implementation (Could Fix)
10. **Issues 10-16**: Documentation and minor improvements

---

## Lessons Applied from AudioPlaybackPort

| AudioPlaybackPort Lesson | Applied to AudioCapturePort |
|--------------------------|----------------------------|
| Device ID as `Union[int, str]` | Issue 3: Same fix needed |
| Both sync and async wait methods | Issue 2: Need sync and async stop |
| Callback deduplication flags | Issue 5: Add requirement |
| DeviceEnumerable protocol | Issue 4: Same pattern |
| Simplified state machine | Issue 7: Reduce from 5 to 3 |
| cleanup() method | Issue 9: Add to interface |
| Dynamic metrics with properties | Issue 8: Add timing properties |

---

## VoxStream Integration Checklist

Before VoxStream integration, verify:

- [ ] `start()` returns queue or context manager (not raw iterator)
- [ ] `stop()` is sync (or provide sync version)
- [ ] Device ID accepts both int and string
- [ ] Callbacks fire exactly once per session
- [ ] Transfer loop drains remaining chunks on stop
- [ ] Metrics include capture_rate and dynamic duration
- [ ] Context manager / cleanup() available
- [ ] State transitions match VoxStream's expectations
- [ ] Thread-safe is_capturing flag
