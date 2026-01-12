# AudioPlaybackPort Step-by-Step Implementation Plan

## Overview

This plan extracts audio playback from VoxStream into a reusable chatforge port, enabling cross-platform speaker output.

**Source**: `voxstream/io/player.py` (BufferedAudioPlayer), `voxstream/io/capture.py` (DirectAudioPlayer)
**Target**: `chatforge/ports/audio_playback.py` + `chatforge/adapters/audio_playback/`

### Key Design Decisions (from critic.md analysis)

1. **Primary Adapter**: `SoundDevicePlaybackAdapter` uses the **buffered/batching pattern** (like VoxStream's BufferedAudioPlayer), NOT callback-based
2. **Sync/Async**: Both `wait_until_complete()` (async) AND `wait_until_complete_sync()` (sync) provided
3. **Callback Safety**: Explicit deduplication via `_started_notified` and `_complete_notified` flags
4. **State Machine**: Simplified to 5 states (IDLE, BUFFERING, PLAYING, DRAINING, ERROR)
5. **Device ID**: Accepts both `int` (index) and `str` (name match)

---

## Phase 1: Create Port Interface

### Step 1.1: Create AudioPlaybackPort interface file

**File**: `chatforge/ports/audio_playback.py`

**Checklist**:
- [ ] Create `chatforge/ports/audio_playback.py`
- [ ] Define `PlaybackState` enum with 5 states:
  - `IDLE` - No playback active
  - `BUFFERING` - Collecting chunks before playback starts
  - `PLAYING` - Actively outputting audio
  - `DRAINING` - mark_complete() called, finishing buffer
  - `ERROR` - Error occurred
- [ ] Define `AudioPlaybackConfig` dataclass with fields:
  - `sample_rate: int = 24000`
  - `channels: int = 1`
  - `bit_depth: int = 16`
  - `device_id: Optional[Union[int, str]] = None` - int for index, str for name match
  - `min_buffer_chunks: int = 2` - Start playback after this many chunks
  - `max_buffer_ms: int = 5000` - Maximum buffer size
  - `latency: Union[str, float] = "low"` - "low", "high", or float seconds
  - Property: `bytes_per_ms` (derived from sample_rate, channels, bit_depth)
- [ ] Define `OutputDevice` dataclass with fields:
  - `id: int` - Device index (sounddevice uses int)
  - `name: str` - Human-readable name
  - `channels: int` - Max output channels
  - `sample_rates: List[int]` - Supported sample rates
  - `is_default: bool = False`
- [ ] Define `PlaybackMetrics` dataclass with fields:
  - `chunks_received: int = 0`
  - `chunks_played: int = 0`
  - `chunks_buffered: int = 0`
  - `total_bytes_received: int = 0`
  - `total_bytes_played: int = 0`
  - `buffer_duration_ms: float = 0.0`
  - `playback_duration_seconds: float = 0.0`
  - `underruns: int = 0`
  - `first_chunk_time: Optional[float] = None` - Timestamp of first chunk received
  - `playback_start_time: Optional[float] = None` - Timestamp of first audio output
  - Property: `initial_latency_ms` - Time from first chunk to first output
  - Property: `buffer_health` - 0.0-1.0 (1.0 = healthy)
- [ ] Define `AudioPlaybackPort` ABC with:
  - `@property state: PlaybackState`
  - `@property config: AudioPlaybackConfig`
  - `@property is_playing: bool` - True if in PLAYING or DRAINING state
  - `@property is_actively_outputting: bool` - True if audio actually outputting now
  - `@property buffer_duration_ms: float`
  - `play(audio_data: bytes) -> bool` - Returns False if buffer full
  - `mark_complete() -> None`
  - `stop(force: bool = False) -> None`
  - `wait_until_complete_sync(timeout: float = 30.0) -> bool` - **SYNC version for VoxStream**
  - `async wait_until_complete(timeout: float = 30.0) -> bool` - Async version
  - `get_metrics() -> PlaybackMetrics`
  - `get_device_info() -> Optional[OutputDevice]`
  - `set_callbacks(on_started, on_complete, on_buffer_low, on_error, on_chunk_played)`
  - `cleanup() -> None` - Release resources (stream, files, etc.)

**Note on list_devices()**: This is NOT in the ABC. Adapters that support device enumeration implement the `DeviceEnumerable` protocol separately.

```python
class DeviceEnumerable(Protocol):
    """Protocol for adapters that can enumerate audio devices."""
    @classmethod
    def list_devices(cls) -> List[OutputDevice]: ...
```

### Step 1.2: Add exceptions

**In same file** `chatforge/ports/audio_playback.py`:

**Checklist**:
- [ ] Define `AudioPlaybackError` base exception
- [ ] Define `DeviceNotFoundError` - Device ID not found
- [ ] Define `DeviceInUseError` - Device locked by another application
- [ ] Define `PlaybackTimeoutError` - Operation timed out

**Note**: `BufferOverflowError` removed. Buffer full condition returns `False` from `play()`, not an exception. Exceptions are for unexpected errors only.

### Step 1.3: Export from ports package

**File**: `chatforge/ports/__init__.py`

**Checklist**:
- [ ] Add AudioPlaybackPort exports to `__init__.py`
- [ ] Add to `__all__` list
- [ ] Include DeviceEnumerable protocol

---

## Phase 2: Implement SoundDevicePlaybackAdapter (Primary)

This is the **primary adapter** using the buffered/batching pattern that VoxStream expects.

### Step 2.1: Create adapters directory structure

```bash
mkdir -p chatforge/adapters/audio_playback
touch chatforge/adapters/audio_playback/__init__.py
touch chatforge/adapters/audio_playback/sounddevice_adapter.py
```

**Checklist**:
- [ ] Create `chatforge/adapters/audio_playback/` directory
- [ ] Create `__init__.py`
- [ ] Create `sounddevice_adapter.py`

### Step 2.2: Implement SoundDevicePlaybackAdapter

**File**: `chatforge/adapters/audio_playback/sounddevice_adapter.py`

**Source reference**: `voxstream/io/player.py` (BufferedAudioPlayer class)

This adapter uses:
- Thread-based playback loop (like BufferedAudioPlayer)
- Smart buffering with min_buffer_chunks threshold
- Batch playback via `sd.play()` blocking calls
- Proper completion detection and callbacks

**Checklist**:
- [ ] Create `SoundDevicePlaybackAdapter` class implementing `AudioPlaybackPort` and `DeviceEnumerable`
- [ ] Implement `__init__(config: AudioPlaybackConfig | None = None)`
  - Initialize config with defaults
  - Initialize `_bytes_per_ms` from config
  - Initialize buffer list with lock (`_buffer: List[bytes]`, `_buffer_lock`)
  - Initialize state variables (`_state`, `_is_complete`)
  - Initialize playback thread variables (`_play_thread`, `_stop_flag`)
  - Initialize metrics (`_metrics: PlaybackMetrics`)
  - **Initialize callback deduplication flags** (`_started_notified`, `_complete_notified`)
  - Initialize callbacks to None
  - Resolve and validate device ID
- [ ] Implement `_resolve_device_id() -> Optional[int]`
  - If config.device_id is int: return it
  - If config.device_id is str: search devices by name match
  - If None: return None (use default)
- [ ] Implement `_get_device_info() -> Optional[OutputDevice]`
  - Query sounddevice for device info
  - Return OutputDevice or None
- [ ] Implement `play(audio_data: bytes) -> bool`
  - Check if buffer would exceed max_buffer_ms → return False
  - Lock buffer, append data
  - Update metrics (first_chunk_time on first chunk, chunks_received, bytes)
  - Start playback thread if not running
  - Return True
- [ ] Implement `_start_playback() -> None`
  - Set state to BUFFERING
  - Clear stop flag
  - **Reset deduplication flags** (`_started_notified = False`, `_complete_notified = False`)
  - Create and start playback thread
- [ ] Implement `_playback_loop() -> None`
  - Set device if specified
  - Loop while not stopped:
    - Check buffer: `can_play = buffer_size >= min_buffer_chunks or (is_complete and buffer_size > 0)`
    - If can_play:
      - Extract chunks (all if complete, else up to max_batch)
      - **On first playback**: Record `playback_start_time`, set state to PLAYING
      - **Fire on_started callback ONCE** (check `_started_notified` flag)
      - Combine chunks, convert to numpy
      - Call `sd.play(audio_array, sample_rate, blocking=True)`
      - Update metrics (chunks_played, bytes_played)
      - Fire on_chunk_played callback if set
    - Check completion: `is_complete and buffer empty`
      - Set state to IDLE
      - Record `playback_end_time`
      - **Fire on_complete callback ONCE** (check `_complete_notified` flag)
      - Set completion event
      - Break loop
    - If not enough to play: sleep 20ms
  - Finally: ensure state cleanup
- [ ] Implement `mark_complete() -> None`
  - Set `_is_complete = True`
  - Set state to DRAINING
- [ ] Implement `stop(force: bool = False) -> None`
  - Set stop flag
  - If force: call `sd.stop()`, clear buffer immediately
  - Wait for thread to finish (join with timeout)
  - Clear buffer
  - Set state to IDLE
  - **Reset deduplication flags for next session**
- [ ] Implement `wait_until_complete_sync(timeout: float = 30.0) -> bool`
  - Wait on completion event with timeout
  - Return True if completed, False if timeout
- [ ] Implement `async wait_until_complete(timeout: float = 30.0) -> bool`
  - Use `asyncio.to_thread()` or `asyncio.wait_for()` with event
  - Return True if completed, False if timeout
- [ ] Implement `get_metrics() -> PlaybackMetrics`
  - Return copy of metrics with current buffer state
- [ ] Implement `get_device_info() -> Optional[OutputDevice]`
- [ ] Implement `@classmethod list_devices(cls) -> List[OutputDevice]`
  - Query sounddevice for output devices
  - Convert to OutputDevice objects
- [ ] Implement `cleanup() -> None`
  - Stop playback if running
  - Clear buffer
  - Release any resources
- [ ] Implement all properties (`state`, `config`, `is_playing`, `is_actively_outputting`, `buffer_duration_ms`)
- [ ] Implement `set_callbacks(...)` with all callback types

### Step 2.3: Export from adapters package

**File**: `chatforge/adapters/audio_playback/__init__.py`

```python
from chatforge.adapters.audio_playback.sounddevice_adapter import SoundDevicePlaybackAdapter

__all__ = ["SoundDevicePlaybackAdapter"]
```

---

## Phase 3: Implement DirectPlaybackAdapter (Optional Low-Latency)

This is an **optional** adapter for ultra-low-latency scenarios using callback-based streaming.

### Step 3.1: Create direct adapter

**File**: `chatforge/adapters/audio_playback/direct_adapter.py`

**Source reference**: `voxstream/io/capture.py` (DirectAudioPlayer class)

**Checklist**:
- [ ] Create `DirectPlaybackAdapter` class implementing `AudioPlaybackPort` and `DeviceEnumerable`
- [ ] Implement callback-based streaming with `sd.OutputStream`
- [ ] Implement `_audio_callback(outdata, frames, time_info, status)`
  - Lock buffer
  - Pull bytes_needed from buffer
  - If buffer has data: copy to outdata
  - If buffer empty: output silence, increment underruns
- [ ] Implement pre-initialization option (`pre_initialize: bool = True`)
- [ ] Implement proper cleanup to stop continuous stream
- [ ] Document battery/CPU impact of pre-initialization
- [ ] Add to `__init__.py` exports

**Use Case**: Only for applications requiring <20ms latency where battery impact is acceptable.

---

## Phase 4: Implement FileSinkAdapter

**Note**: Renamed from FilePlaybackAdapter to clarify it's a **sink** not a player.

### Step 4.1: Create file adapter

**File**: `chatforge/adapters/audio_playback/file_sink.py`

**Checklist**:
- [ ] Create `FileSinkAdapter` class implementing `AudioPlaybackPort`
- [ ] Implement `__init__(file_path: Union[str, Path], config: AudioPlaybackConfig | None = None)`
  - Validate file path is writable
  - Store config
  - Initialize state
- [ ] Implement `_open_file() -> None`
  - Create wave.Wave_write
  - Set channels, sample width, frame rate
- [ ] Implement `play(audio_data: bytes) -> bool`
  - Reject if already complete (return False)
  - Open file if not open
  - Write frames
  - Update metrics
  - Return True
- [ ] Implement `mark_complete() -> None`
  - Close WAV file properly
  - Set state to IDLE
  - Fire on_complete callback
- [ ] Implement `stop(force: bool = False) -> None`
  - Close file (truncate if force)
- [ ] Implement `cleanup() -> None`
  - Ensure file is closed
- [ ] Implement remaining interface methods
- [ ] **Do NOT implement list_devices()** - not applicable
- [ ] Add to `__init__.py` exports

---

## Phase 5: Write Tests

### Step 5.1: Create test file structure

```bash
mkdir -p tests/adapters/audio_playback
touch tests/adapters/audio_playback/__init__.py
touch tests/adapters/audio_playback/test_sounddevice_adapter.py
touch tests/adapters/audio_playback/test_file_sink.py
touch tests/adapters/audio_playback/fixtures.py
```

### Step 5.2: Create test fixtures

**File**: `tests/adapters/audio_playback/fixtures.py`

**Checklist**:
- [ ] Create `generate_test_audio(duration_ms, frequency, sample_rate) -> bytes`
- [ ] Create `MockSoundDevice` for unit testing without hardware
- [ ] Create `create_test_config() -> AudioPlaybackConfig`
- [ ] Create `TemporaryWavFile` context manager

### Step 5.3: Unit tests for SoundDevicePlaybackAdapter

**File**: `tests/adapters/audio_playback/test_sounddevice_adapter.py`

**Checklist**:
- [ ] Test `list_devices()` returns OutputDevice objects
- [ ] Test `play()` adds to buffer and returns True
- [ ] Test `play()` returns False when buffer full
- [ ] Test `stop()` transitions to IDLE
- [ ] Test `stop(force=True)` clears buffer immediately and calls `sd.stop()`
- [ ] Test `mark_complete()` sets state to DRAINING
- [ ] Test `wait_until_complete_sync()` returns True on completion
- [ ] Test `wait_until_complete_sync()` returns False on timeout
- [ ] Test `on_started` callback fires **exactly once**
- [ ] Test `on_complete` callback fires **exactly once**
- [ ] Test callbacks don't fire on false starts
- [ ] Test `buffer_duration_ms` property accuracy
- [ ] Test `initial_latency_ms` metric is recorded
- [ ] Test device resolution by name (string device_id)
- [ ] Test device resolution by index (int device_id)
- [ ] Test `cleanup()` releases resources
- [ ] Test state transitions: IDLE → BUFFERING → PLAYING → DRAINING → IDLE

### Step 5.4: Unit tests for FileSinkAdapter

**File**: `tests/adapters/audio_playback/test_file_sink.py`

**Checklist**:
- [ ] Test creates valid WAV file
- [ ] Test WAV format matches config (sample_rate, channels, bit_depth)
- [ ] Test `play()` after `mark_complete()` returns False
- [ ] Test file is closed on `mark_complete()`
- [ ] Test file is closed on `cleanup()`
- [ ] Test metrics are tracked correctly
- [ ] Test `list_devices()` is not available (AttributeError or NotImplementedError)

---

## Phase 6: Integrate with VoxStream

### Step 6.1: Update VoxStream to accept AudioPlaybackPort

**File**: `voxstream/core/stream.py`

**Checklist**:
- [ ] Add `playback: AudioPlaybackPort | None = None` parameter to `__init__`
- [ ] Import `AudioPlaybackPort` and `SoundDevicePlaybackAdapter`
- [ ] Create default adapter if not provided:
  ```python
  if playback:
      self._player = playback
  else:
      self._player = SoundDevicePlaybackAdapter(
          AudioPlaybackConfig(
              sample_rate=self.config.sample_rate,
              channels=self.config.channels,
              device_id=self._output_device,
          )
      )
  ```
- [ ] Wire callbacks using `set_callbacks()`:
  ```python
  self._player.set_callbacks(
      on_started=self._on_playback_started_callback,
      on_complete=self._on_playback_complete_callback,
  )
  ```
- [ ] Update `queue_playback()` to use `self._player.play()`
- [ ] Update `mark_playback_complete()` to use `self._player.mark_complete()`
- [ ] Update `interrupt_playback()` to use `self._player.stop(force=True)`
- [ ] Ensure cleanup on VoxStream shutdown: `self._player.cleanup()`
- [ ] Maintain backward compatibility (default behavior unchanged)

### Step 6.2: Update AudioManager

**File**: `voxstream/io/manager.py`

**Checklist**:
- [ ] Update AudioManager to accept AudioPlaybackPort
- [ ] Remove direct BufferedAudioPlayer dependency where possible
- [ ] Use port interface instead

### Step 6.3: Verify voxterm still works

**Checklist**:
- [ ] Run voxterm with default adapter
- [ ] Test audio playback works
- [ ] Test start callback fires (state transitions to PLAYING)
- [ ] Test complete callback fires (turn-taking works)
- [ ] Test interrupt (barge-in) works - `stop(force=True)`
- [ ] Test metrics are reported correctly
- [ ] Test no duplicate callbacks fire

---

## Phase 7: Add NullPlaybackAdapter (Testing)

### Step 7.1: Implement NullPlaybackAdapter

**File**: `chatforge/adapters/audio_playback/null_adapter.py`

```python
class NullPlaybackAdapter(AudioPlaybackPort):
    """
    Null adapter for testing - discards audio, optionally simulates timing.

    Use for:
    - Unit tests without audio hardware
    - CI/CD pipelines
    - Benchmarking without actual playback
    """

    def __init__(
        self,
        config: AudioPlaybackConfig | None = None,
        simulate_timing: bool = False,  # If True, delays based on audio duration
    ):
        ...
```

**Checklist**:
- [ ] Create `null_adapter.py`
- [ ] Implement `NullPlaybackAdapter`
- [ ] Support `simulate_timing` mode for realistic test timing
- [ ] Track all metrics as if playing
- [ ] Fire callbacks at appropriate times
- [ ] Add to exports
- [ ] Add tests

---

## Phase 8: Documentation

### Step 8.1: Create usage examples

**File**: `chatforge/adapters/audio_playback/README.md`

**Checklist**:
- [ ] Document which adapter to use for VoxStream (SoundDevicePlaybackAdapter)
- [ ] Document DirectPlaybackAdapter use case and trade-offs
- [ ] Document callback contract (fires exactly once per session)
- [ ] Document error handling (return value vs exceptions)
- [ ] Document device selection (int index vs string name)
- [ ] Example: Basic usage
- [ ] Example: Streaming from API
- [ ] Example: Interrupt/Barge-in pattern
- [ ] Example: Recording to file
- [ ] Example: Testing with NullPlaybackAdapter

---

## Verification Checklist

### Phase 1 Complete
- [ ] `chatforge/ports/audio_playback.py` exists with full interface
- [ ] PlaybackState has 5 states (not 7)
- [ ] Both sync and async wait methods defined
- [ ] PlaybackMetrics includes initial_latency_ms
- [ ] DeviceEnumerable protocol defined separately
- [ ] Exports work: `from chatforge.ports import AudioPlaybackPort`

### Phase 2 Complete
- [ ] SoundDevicePlaybackAdapter uses buffered/batching pattern
- [ ] Callback deduplication implemented (_started_notified, _complete_notified)
- [ ] Device ID resolution handles both int and str
- [ ] cleanup() method implemented
- [ ] Exports work: `from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter`

### Phase 3 Complete (Optional)
- [ ] DirectPlaybackAdapter works for low-latency scenarios
- [ ] Battery/CPU impact documented

### Phase 4 Complete
- [ ] FileSinkAdapter creates valid WAV files
- [ ] Properly named (not FilePlaybackAdapter)
- [ ] Rejects play() after mark_complete()

### Phase 5 Complete
- [ ] All unit tests pass
- [ ] Callback deduplication tested
- [ ] State transitions tested
- [ ] Test coverage > 80%

### Phase 6 Complete
- [ ] VoxStream accepts `playback: AudioPlaybackPort`
- [ ] Backward compatibility maintained
- [ ] voxterm works with new playback
- [ ] Barge-in (interrupt) works correctly
- [ ] No duplicate callbacks fire

### Phase 7 Complete
- [ ] NullPlaybackAdapter works for testing

### Phase 8 Complete
- [ ] Documentation complete
- [ ] Examples work

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `chatforge/ports/audio_playback.py` | AudioPlaybackPort interface, DeviceEnumerable protocol |
| `chatforge/adapters/audio_playback/__init__.py` | Adapter exports |
| `chatforge/adapters/audio_playback/sounddevice_adapter.py` | Primary adapter (buffered pattern) |
| `chatforge/adapters/audio_playback/direct_adapter.py` | Low-latency adapter (optional) |
| `chatforge/adapters/audio_playback/file_sink.py` | File recording sink |
| `chatforge/adapters/audio_playback/null_adapter.py` | Testing adapter |
| `tests/adapters/audio_playback/test_sounddevice_adapter.py` | Unit tests |
| `tests/adapters/audio_playback/test_file_sink.py` | Unit tests |
| `tests/adapters/audio_playback/fixtures.py` | Test helpers |

### Modified Files

| File | Changes |
|------|---------|
| `chatforge/ports/__init__.py` | Add AudioPlaybackPort exports |
| `voxstream/core/stream.py` | Accept `playback: AudioPlaybackPort` param |
| `voxstream/io/manager.py` | Use AudioPlaybackPort instead of BufferedAudioPlayer |

---

## Dependencies

### Required
- numpy (already in voxstream)

### Per Adapter
| Adapter | Dependencies |
|---------|-------------|
| SoundDevicePlaybackAdapter | `sounddevice`, `numpy` |
| DirectPlaybackAdapter | `sounddevice`, `numpy` |
| FileSinkAdapter | `wave` (built-in) |
| NullPlaybackAdapter | None |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking VoxStream playback | Use buffered pattern matching original BufferedAudioPlayer |
| Duplicate callback fires | Explicit deduplication with _started_notified/_complete_notified flags |
| Async/sync mismatch | Provide both wait_until_complete() and wait_until_complete_sync() |
| Device ID confusion | Accept both int (index) and str (name match) |
| State machine mismatch | Simplified 5-state machine matching original boolean patterns |
| Resource leaks | Explicit cleanup() method, context manager support |
| Barge-in not working | Test stop(force=True) explicitly with sd.stop() call |

---

## State Machine Reference

```
State Transitions (5 states):

                     play()
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
┌──────┐    ┌───────────┐    ┌─────────┐  │
│ IDLE │───►│ BUFFERING │───►│ PLAYING │──┘
└──────┘    └───────────┘    └─────────┘
    ▲         (waiting for      │
    │          min_buffer)      │ mark_complete()
    │                           ▼
    │                      ┌──────────┐
    │                      │ DRAINING │
    │                      └──────────┘
    │                           │
    │                           │ buffer empty
    └───────────────────────────┘

ERROR state can occur from any state.
stop() from any state → IDLE

Key transitions:
- IDLE + play() → BUFFERING
- BUFFERING + buffer ready → PLAYING (fire on_started ONCE)
- PLAYING + mark_complete() → DRAINING
- DRAINING + buffer empty → IDLE (fire on_complete ONCE)
- Any + stop() → IDLE
- Any + error → ERROR
```

---

## Callback Contract

**Critical**: Callbacks must fire **exactly once** per playback session.

```python
# Implementation pattern:
class SoundDevicePlaybackAdapter:
    def __init__(self):
        self._started_notified = False
        self._complete_notified = False

    def _start_playback(self):
        # Reset flags for new session
        self._started_notified = False
        self._complete_notified = False

    def _playback_loop(self):
        # Fire on_started ONCE
        if not self._started_notified and self._on_started:
            self._started_notified = True
            try:
                self._on_started()
            except Exception as e:
                self._log_error(f"on_started callback error: {e}")

        # ... playback logic ...

        # Fire on_complete ONCE
        if not self._complete_notified and self._on_complete:
            self._complete_notified = True
            try:
                self._on_complete()
            except Exception as e:
                self._log_error(f"on_complete callback error: {e}")

    def stop(self, force: bool = False):
        # Reset flags for next session
        self._started_notified = False
        self._complete_notified = False
```

This prevents VoxStream's state machine from corrupting due to duplicate transitions.
