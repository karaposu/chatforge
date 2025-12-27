# What's Missing in VoxStream

*Gaps between current implementation and production-ready audio abstraction layer.*

---

## Summary Table

| Category | Gap | Priority | Effort | Impact |
|----------|-----|----------|--------|--------|
| **Audio Quality** | Echo Cancellation (AEC) | Critical | High | Can't use speakers |
| **Audio Quality** | Proper Noise Suppression | Critical | Medium | Poor transcription |
| **Reliability** | Thread Safety Gaps | High | Medium | Race condition crashes |
| **Reliability** | Protected Audio Callbacks | High | Low | Thread crashes on error |
| **Interface** | Consistent Async API | High | Medium | Clean AudioStreamPort |
| **Interface** | Error Propagation | Medium | Low | Lost exceptions |
| **Operations** | Device Hot-Plug | Medium | Medium | Must restart on change |
| **Operations** | Health Check API | Medium | Low | Can't monitor system |
| **Code Quality** | Duplicate Implementations | Low | Low | Maintenance burden |
| **Performance** | O(n) in Hot Paths | Low | Low | Minor inefficiency |

---

## 1. Critical: Audio Quality

### 1.1 Echo Cancellation (AEC)

**What it is**: Removing the AI's voice from the microphone input when using speakers.

**Current state**: Not implemented.

**Impact**:
- Users MUST use headphones
- With speakers, AI hears itself → feedback loops
- Unusable for hands-free scenarios

**Why it matters**:
```
Without AEC:
User speaks → Mic captures user + speaker output → AI hears itself
           → AI responds to its own voice → Infinite loop

With AEC:
User speaks → Mic captures user + speaker output
           → AEC removes speaker output → AI hears only user
```

**Expected implementation**:
```python
class EchoCanceller:
    def process(
        self,
        mic_audio: bytes,      # What the mic captured
        speaker_audio: bytes,  # What we played to speakers
    ) -> bytes:
        # Remove speaker_audio from mic_audio
        # Return only the user's voice
        ...
```

**Options**:
- WebRTC's AEC (via aiortc or webrtc-audio-processing)
- SpeexDSP
- Commercial SDK (Krisp, etc.)

---

### 1.2 Proper Noise Suppression

**What it is**: Removing background noise (HVAC, traffic, keyboard) while preserving speech.

**Current state**: Placeholder stub with crude high-pass filtering.

```python
# core/processor.py:201-208 - Current implementation
def reduce_noise(self, audio_bytes: AudioBytes) -> AudioBytes:
    # This is a placeholder - just does basic filtering
    # Real implementation would use spectral subtraction or ML
    ...
```

**Impact**:
- Poor AI transcription in noisy environments
- User must be in quiet room
- Not usable for real-world scenarios

**Expected implementation**:
- FFT-based spectral subtraction
- RNNoise integration (ML-based)
- WebRTC noise suppression

---

## 2. High Priority: Reliability

### 2.1 Thread Safety Gaps

**What it is**: Race conditions when accessing shared state from multiple threads.

**Current state**: Inconsistent lock usage.

```python
# Problem: process_vad() accesses _vad without lock
def process_vad(self, audio_chunk: AudioBytes) -> Optional[str]:
    if not self._vad:        # Check without lock
        return None
    state = self._vad.process_chunk(audio_chunk)  # Use without lock
    # cleanup() could null _vad between check and use!

# But cleanup() uses lock
async def cleanup(self) -> None:
    with self._lock:
        self._vad = None     # Nulls reference under lock
```

**Impact**:
- `AttributeError` or `NoneType` exceptions during cleanup
- Crashes when stopping audio while processing
- Intermittent failures hard to debug

**Fix**:
```python
def process_vad(self, audio_chunk: AudioBytes) -> Optional[str]:
    with self._lock:
        vad = self._vad  # Grab reference under lock
    if vad is None:
        return None
    return vad.process_chunk(audio_chunk).value  # Use outside lock
```

---

### 2.2 Unprotected Audio Callbacks

**What it is**: Audio callbacks run in OS audio thread without try/except.

**Current state**: Exceptions crash the audio thread.

```python
# io/player.py - DirectAudioPlayer._audio_callback
def _audio_callback(self, outdata, frames, time_info, status):
    # No try/except wrapping
    # Any exception kills the audio thread
    # Rest of app may not even know audio died
    ...
```

**Impact**:
- Single exception kills audio stream
- No recovery possible
- Silent failure - app continues without audio

**Fix**:
```python
def _audio_callback(self, outdata, frames, time_info, status):
    try:
        # ... existing code ...
    except Exception as e:
        self.logger.error(f"Audio callback error: {e}")
        outdata.fill(0)  # Output silence on error
        self._error_count += 1
        if self._error_count > 10:
            self._request_restart = True
```

---

## 3. High Priority: Interface

### 3.1 Consistent Async API

**What it is**: Some methods are async, some are sync, mixing patterns.

**Current state**: Confusing mix.

```python
class VoxStream:
    def __init__(self):
        self._lock = threading.Lock()  # Sync lock

    async def initialize(self) -> None:  # Async method
        with self._lock:  # But uses sync lock!
            ...

    def play_audio(self, data) -> bool:  # Sync method
        ...

    async def cleanup(self) -> None:  # Async method
        with self._lock:  # Sync lock in async context
            ...
```

**Impact**:
- `threading.Lock` in async context blocks event loop
- Confusing API - caller doesn't know what to await
- Potential deadlocks

**For AudioStreamPort**:
```python
class AudioStreamPort(ABC):
    # All streaming methods should be async

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        ...

    async def stop_capture(self) -> None:
        ...

    async def play_chunk(self, chunk: bytes) -> None:
        ...

    async def stop_playback(self) -> None:
        ...
```

---

### 3.2 Error Propagation

**What it is**: Errors should bubble up to caller, not be silently swallowed.

**Current state**: Many errors logged but not raised.

```python
# Current pattern - errors hidden
def play_audio(self, audio_data: AudioBytes) -> bool:
    try:
        # ... play audio ...
        return True
    except Exception as e:
        self.logger.error(f"Playback error: {e}")
        return False  # Caller just sees False, no details
```

**Better pattern**:
```python
class AudioError(Exception):
    """Base class for audio errors."""
    pass

class PlaybackError(AudioError):
    """Playback failed."""
    pass

async def play_chunk(self, chunk: bytes) -> None:
    try:
        # ... play audio ...
    except SoundDeviceError as e:
        raise PlaybackError(f"Playback failed: {e}") from e
```

---

## 4. Medium Priority: Operations

### 4.1 Device Hot-Plug Detection

**What it is**: Detecting when audio devices are connected/disconnected.

**Current state**: Device queried once at initialization.

```python
# Current: Device set at init, never updated
def __init__(self, device: int = None):
    self.device = device or sd.default.device[0]
    # If user plugs in headphones later, we don't know
```

**Impact**:
- Must restart app when changing audio devices
- Poor UX for laptop users (dock/undock)
- Can't switch between headphones and speakers

**Expected**:
```python
class AudioStreamPort:
    def on_device_change(
        self,
        callback: Callable[[str, str], None],  # (event, device_name)
    ) -> None:
        """Register callback for device changes."""
        ...

    async def switch_device(
        self,
        input_device: int | str | None = None,
        output_device: int | str | None = None,
    ) -> None:
        """Switch to different audio device."""
        ...
```

---

### 4.2 Health Check API

**What it is**: Method to check if audio subsystem is healthy.

**Current state**: No health check interface.

**Expected**:
```python
@dataclass
class AudioHealth:
    capture_active: bool
    playback_active: bool
    input_level: float
    output_level: float
    error_count: int
    last_error: str | None

class AudioStreamPort:
    def get_health(self) -> AudioHealth:
        """Check audio subsystem health."""
        ...

    def is_healthy(self) -> bool:
        """Quick health check."""
        ...
```

---

## 5. Low Priority: Code Quality

### 5.1 Duplicate Implementations

**What it is**: Same code exists in multiple places.

**Current state**:

| Component | Location 1 | Location 2 |
|-----------|------------|------------|
| BufferPool | `core/processor.py:37` | `core/buffer.py:21` |
| StreamBuffer | `core/processor.py:628` | `core/buffer.py:52` |

**Impact**:
- Fix bug in one place, forget the other
- Confusion about which to use
- Maintenance burden

**Fix**: Delete duplicates, keep one canonical location.

---

### 5.2 O(n) Operations in Hot Paths

**What it is**: Linear-time operations where O(1) is possible.

**Current state**:

```python
# BufferPool.release() - O(n) scan
def release(self, buffer: bytearray) -> None:
    for idx, buf in enumerate(self.buffers):  # O(n)
        if buf is buffer:
            ...

# BufferedAudioPlayer - O(n) list pop
chunks_to_play.append(self.buffer.pop(0))  # O(n) pop from front
```

**Impact**: Minor - pool is small (10 items), chunks few (2-5).

**Fix if needed**:
```python
# Use dict for O(1) lookup
self._buffer_to_index = {id(buf): idx for idx, buf in enumerate(self.buffers)}

# Use deque for O(1) popleft
from collections import deque
self.buffer: deque[AudioBytes] = deque()
chunk = self.buffer.popleft()  # O(1)
```

---

## 6. Missing for AudioStreamPort Pattern

### 6.1 Clean Async Generator for Capture

**Current**:
```python
# VoxStream has this, but interface isn't clean
async def capture_stream(self):
    # Works, but mixed with sync internals
```

**Needed**:
```python
class AudioStreamPort(ABC):
    @abstractmethod
    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """
        Start capturing audio.

        Yields:
            Audio chunks as bytes (PCM16, 24kHz, mono).

        Raises:
            CaptureError: If capture fails to start.
        """
        ...
```

---

### 6.2 VAD Callbacks Interface

**Current**: VAD is internal, callbacks set via VoxStream.

**Needed for AudioStreamPort**:
```python
class AudioStreamPort(ABC):
    @abstractmethod
    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None] | None = None,
        on_speech_end: Callable[[bytes], None] | None = None,  # With audio
    ) -> None:
        """Register VAD event callbacks."""
        ...

    @abstractmethod
    def get_vad_state(self) -> Literal["silence", "speech"]:
        """Get current VAD state."""
        ...
```

---

### 6.3 Audio Level Observable

**Current**: Can get level, but not observe changes.

**Needed**:
```python
class AudioStreamPort(ABC):
    @abstractmethod
    def get_input_level(self) -> float:
        """Get current input level (0.0 to 1.0)."""
        ...

    @abstractmethod
    def set_level_callback(
        self,
        callback: Callable[[float], None],
        interval_ms: int = 100,
    ) -> None:
        """Register callback for level changes (for UI meters)."""
        ...
```

---

## Priority Order for Implementation

### Phase 1: Reliability (Before using in production)
1. Thread safety fixes
2. Protected audio callbacks
3. Error propagation

### Phase 2: Interface (For AudioStreamPort)
4. Consistent async API
5. Clean capture generator
6. VAD callbacks interface

### Phase 3: Operations
7. Health check API
8. Device hot-plug

### Phase 4: Audio Quality (Production features)
9. Noise suppression
10. Echo cancellation

### Phase 5: Cleanup
11. Remove duplicate code
12. O(1) optimizations (if needed)

---

## Validation Strategy

Each fix validated against VoiceEngine:

```
Fix VoxStream issue
       │
       ▼
Run VoiceEngine smoke tests
       │
       ├── Pass → Next fix
       │
       └── Fail → Debug, fix, retry
```

VoiceEngine provides real-world validation for each VoxStream improvement.

---

## Related Documents

| Document | Topic |
|----------|-------|
| `5_things_or_not.md` | Original improvement analysis |
| `missing_concepts_list.md` | Full missing concepts list |
| `chatforge_voxstream_high_level.md` | AudioStreamPort architecture |
| `chatforge_compatibility_analysis.md` | Integration analysis |
