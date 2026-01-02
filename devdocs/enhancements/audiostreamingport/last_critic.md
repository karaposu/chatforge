# AudioStreamPort: Final Validation Critique

**Date:** 2025-01-01
**Scope:** Cross-validation of `step_by_step_implementation.md` against actual chatforge and voxstream codebases
**Status:** Issues found - must fix before implementation

---

## Summary

After reading the full chatforge codebase and voxstream source code, I found **12 issues** with the implementation plan. Some are blocking, others are pattern inconsistencies.

---

## Critical Issues (Must Fix)

### Issue 1: Missing Exception Hierarchy

**Problem:** All chatforge ports define custom exception hierarchies. AudioStreamPort has none.

**chatforge pattern (from TTSPort):**
```python
class TTSError(Exception): pass
class TTSNetworkError(TTSError): pass
class TTSAuthenticationError(TTSError): pass
class TTSRateLimitError(TTSError): pass
# ... more
```

**Fix required:** Add to `ports/audio_stream.py`:
```python
class AudioStreamError(Exception):
    """Base exception for AudioStreamPort."""
    pass

class AudioStreamDeviceError(AudioStreamError):
    """Device not found or disconnected."""
    pass

class AudioStreamBufferError(AudioStreamError):
    """Buffer overflow or underflow."""
    pass

class AudioStreamNotInitializedError(AudioStreamError):
    """Adapter used before initialization."""
    pass
```

---

### Issue 2: VoxStream Constructor Signature Mismatch

**Problem:** Our plan passes `sample_rate` directly, but VoxStream expects a `StreamConfig` object.

**Our plan (WRONG):**
```python
self._voxstream = VoxStream(
    mode=mode_map.get(self._mode, ProcessingMode.REALTIME),
    sample_rate=self._config.sample_rate,  # ❌ This parameter doesn't exist
)
```

**Actual VoxStream signature:**
```python
def __init__(
    self,
    mode: ProcessingMode = ProcessingMode.BALANCED,
    config: StreamConfig = None,  # ✅ Pass config here
    buffer_config: BufferConfig = None,
    logger: Optional[logging.Logger] = None
)
```

**Fix required:**
```python
from voxstream.config.types import StreamConfig as VoxStreamConfig

vox_config = VoxStreamConfig(
    sample_rate=self._config.sample_rate,
    channels=self._config.channels,
    bit_depth=self._config.bit_depth,
    chunk_duration_ms=self._config.chunk_duration_ms,
)

self._voxstream = VoxStream(
    mode=mode_map.get(self._mode, ProcessingMode.REALTIME),
    config=vox_config,
)
```

---

### Issue 3: Test Code Syntax Error

**Problem:** Test uses non-existent `nonlocal_set` function.

**Our plan (WRONG):**
```python
mock.set_callbacks(AudioCallbacks(
    on_playback_complete=lambda: nonlocal_set('completed', True),  # ❌ Not valid Python
))
```

**Fix required:**
```python
completed = False

def on_complete():
    nonlocal completed
    completed = True

mock.set_callbacks(AudioCallbacks(
    on_playback_complete=on_complete,
))
```

---

### Issue 4: Playback Complete Callback Not Wired

**Problem:** VoxStream has `set_playback_callbacks()` but we never call it. The `on_playback_complete` callback won't fire.

**VoxStream API:**
```python
def set_playback_callbacks(
    self,
    completion_callback: Optional[Callable] = None,
    chunk_played_callback: Optional[Callable[[int], None]] = None
) -> None
```

**Fix required in `__aenter__` or `set_callbacks`:**
```python
def set_callbacks(self, callbacks: AudioCallbacks) -> None:
    self._callbacks = callbacks

    # Wire playback completion to VoxStream
    if self._voxstream and callbacks.on_playback_complete:
        self._voxstream.set_playback_callbacks(
            completion_callback=callbacks.on_playback_complete
        )
```

---

## Pattern Issues (Should Fix)

### Issue 5: Missing `provider_name` Property

**Problem:** All chatforge ports have a `provider_name` property. Our AudioStreamPort doesn't.

**chatforge pattern:**
```python
class TTSPort(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the TTS provider."""
        ...
```

**Fix required in AudioStreamPort:**
```python
@property
@abstractmethod
def provider_name(self) -> str:
    """Human-readable name of the audio provider."""
    ...
```

**In VoxStreamAdapter:**
```python
@property
def provider_name(self) -> str:
    return "voxstream"
```

**In MockAudioStreamAdapter:**
```python
@property
def provider_name(self) -> str:
    return "mock"
```

---

### Issue 6: Missing NullAdapter

**Problem:** chatforge has `NullMessagingAdapter`, `NullKnowledgeAdapter`, etc. in `adapters/null.py`. We should add `NullAudioStreamAdapter`.

**Fix required in `adapters/null.py`:**
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

    # ... other no-op methods
```

---

### Issue 7: VADConfig Field Mismatch

**Problem:** Our `VADConfig` has `enabled: bool` but VoxStream's `VADConfig` uses `type: VADType` where `VADType.NONE` disables VAD.

**Our config:**
```python
@dataclass
class VADConfig:
    enabled: bool = True
    energy_threshold: float = 0.02
    ...
```

**VoxStream config:**
```python
@dataclass
class VADConfig:
    type: VADType = VADType.ENERGY_BASED  # VADType.NONE to disable
    energy_threshold: float = 0.02
    ...
```

**Fix required:** Map `enabled=False` to `type=VADType.NONE`:
```python
def _setup_vad(self):
    from voxstream.config.types import VADConfig as VoxVADConfig, VADType

    vox_config = VoxVADConfig(
        type=VADType.ENERGY_BASED if self._vad_config.enabled else VADType.NONE,
        energy_threshold=self._vad_config.energy_threshold,
        ...
    )
```

---

## Minor Issues (Nice to Fix)

### Issue 8: `stop_capture()` Should Be Sync

**Problem:** Our `stop_capture()` is async but only sets a flag. VoxStream's internal `stop_capture()` is sync.

**Current (unnecessary async):**
```python
async def stop_capture(self) -> None:
    self._capturing = False
```

**Should be (consistent with pattern):**
```python
def stop_capture(self) -> None:
    self._capturing = False
```

**Impact:** Low - works either way, but async for sync operations is misleading.

**Decision:** Keep as async for interface consistency since other methods are async.

---

### Issue 9: Config Conversion Boilerplate

**Problem:** We have `AudioStreamConfig` and VoxStream has `StreamConfig`. Need conversion logic.

**Fix required:** Add conversion helper:
```python
def _to_vox_config(self) -> "StreamConfig":
    from voxstream.config.types import StreamConfig as VoxStreamConfig
    return VoxStreamConfig(
        sample_rate=self._config.sample_rate,
        channels=self._config.channels,
        bit_depth=self._config.bit_depth,
        chunk_duration_ms=self._config.chunk_duration_ms,
    )
```

---

### Issue 10: Device Key Mapping

**Problem:** VoxStream returns `default` but our AudioDevice has `is_default`.

**Our mapping (currently correct):**
```python
AudioDevice(
    id=d["index"],
    name=d["name"],
    channels=d["channels"],
    is_default=d["default"],  # ✅ Key is "default", field is "is_default"
)
```

**Status:** Already correct, just noting the discrepancy for awareness.

---

### Issue 11: Missing Audio Format in Exports

**Problem:** We have format constants but don't export them from ports/__init__.py.

**Fix required:** Add to exports:
```python
from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    VADConfig,
    AudioDevice,
    AudioCallbacks,
    # Add:
    AudioStreamError,
    AudioStreamDeviceError,
    AudioStreamBufferError,
)
```

---

### Issue 12: VADetector audio_config Parameter

**Problem:** VADetector accepts `audio_config: Optional[StreamConfig]` for byte calculations. We don't pass it.

**Current (missing audio_config):**
```python
self._vad = VADetector(
    config=vox_config,
    on_speech_start=self._on_speech_start,
    on_speech_end=self._on_speech_end,
)
```

**Should be:**
```python
self._vad = VADetector(
    config=vox_config,
    audio_config=self._to_vox_config(),  # Pass for correct byte/sample calculations
    on_speech_start=self._on_speech_start,
    on_speech_end=self._on_speech_end,
)
```

---

## Fixes Summary

### Must Fix Before Implementation:

| Issue | Severity | Fix Location |
|-------|----------|--------------|
| #1 Missing exception hierarchy | **Critical** | `ports/audio_stream.py` |
| #2 VoxStream constructor mismatch | **Critical** | `adapters/audio/voxstream.py` |
| #3 Test syntax error | **Critical** | `tests/adapters/audio/test_mock.py` |
| #4 Playback callback not wired | **High** | `adapters/audio/voxstream.py` |

### Should Fix:

| Issue | Severity | Fix Location |
|-------|----------|--------------|
| #5 Missing `provider_name` | **Medium** | `ports/audio_stream.py`, adapters |
| #6 Missing NullAdapter | **Medium** | `adapters/null.py` |
| #7 VADConfig field mismatch | **Medium** | `adapters/audio/voxstream.py` |

### Nice to Fix:

| Issue | Severity | Fix Location |
|-------|----------|--------------|
| #8 `stop_capture` sync/async | **Low** | Keep as-is for consistency |
| #9 Config conversion | **Low** | `adapters/audio/voxstream.py` |
| #10 Device key mapping | **Low** | Already correct |
| #11 Export exceptions | **Low** | `ports/__init__.py` |
| #12 VADetector audio_config | **Low** | `adapters/audio/voxstream.py` |

---

## Recommended Action

1. **Update `step_by_step_implementation.md`** with fixes for issues #1-7
2. **Fix test code** for issue #3
3. **Proceed with implementation** after fixes

The core design is sound. These are integration details that need alignment with the actual APIs.
