# VADPort Step-by-Step Implementation Plan

## Overview

This plan extracts VAD from VoxStream into a reusable chatforge port, enabling cross-platform voice activity detection.

**Source**: `voxstream/voice/vad.py` (VADetector, AdaptiveVAD)
**Target**: `chatforge/ports/vad.py` + `chatforge/adapters/vad/`

---

## Phase 1: Create Port Interface

### Step 1.1: Create VADPort interface file

**File**: `chatforge/ports/vad.py`

```python
# Tasks:
# 1. Create SpeechState enum (SILENCE, SPEECH_STARTING, SPEECH, SPEECH_ENDING)
#    NOTE: Use SPEECH_STARTING/SPEECH_ENDING (accumulation states), NOT SPEECH_START/SPEECH_END (events)
# 2. Create VADConfig dataclass with validation
# 3. Create VADResult dataclass
# 4. Create VADMetrics dataclass
# 5. Create VADPort abstract base class
```

**Checklist**:
- [ ] Create `chatforge/ports/vad.py`
- [ ] Define `SpeechState` enum matching VoxStream exactly:
  - `SILENCE = "silence"`
  - `SPEECH_STARTING = "speech_starting"` (NOT "speech_start")
  - `SPEECH = "speech"` (NOT "speaking")
  - `SPEECH_ENDING = "speech_ending"` (NOT "speech_end")
- [ ] Define `VADConfig` dataclass with fields:
  - `energy_threshold: float = 0.02` (0.0-1.0 range)
  - `speech_start_ms: int = 100`
  - `speech_end_ms: int = 500`
  - `pre_buffer_ms: int = 300`
  - `sample_rate: int = 24000`
  - `channels: int = 1`
  - `bit_depth: int = 16`
  - Add `__post_init__` validation
- [ ] Define `VADResult` dataclass with fields:
  - `state: SpeechState`
  - `is_speech: bool` (current chunk has speech)
  - `is_speaking: bool` (in confirmed speech state)
  - `energy: float` (RMS energy 0.0-1.0)
  - `state_duration_ms: float` (time in current state)
- [ ] Define `VADMetrics` dataclass with fields:
  - `total_chunks: int = 0`
  - `speech_chunks: int = 0`
  - `silence_chunks: int = 0`
  - `speech_starting_chunks: int = 0`
  - `speech_ending_chunks: int = 0`
  - `transitions: int = 0`
  - `speech_segments: int = 0`
  - `total_speech_ms: float = 0.0`
  - `total_silence_ms: float = 0.0`
  - `avg_processing_ms: float = 0.0`
- [ ] Define `VADPort` ABC with:
  - `@property state: SpeechState`
  - `@property is_speaking: bool`
  - `@property config: VADConfig`
  - `process_chunk(chunk: bytes) -> VADResult`
  - `set_callbacks(on_speech_start, on_speech_end)` (both are `Callable[[], None]`)
  - `get_pre_buffer() -> bytes`
  - `get_metrics() -> VADMetrics`
  - `reset() -> None`
  - `configure(config: VADConfig) -> None`

### Step 1.2: Add exceptions

**In same file** `chatforge/ports/vad.py`:

```python
class VADError(Exception):
    """Base exception for VAD errors."""
    pass

class VADConfigError(VADError):
    """Invalid VAD configuration."""
    pass
```

**Checklist**:
- [ ] Define `VADError` base exception
- [ ] Define `VADConfigError` for invalid configuration

### Step 1.3: Export from ports package

**File**: `chatforge/ports/__init__.py`

**Checklist**:
- [ ] Add exports: `VADPort`, `VADConfig`, `VADResult`, `VADMetrics`, `SpeechState`
- [ ] Add exceptions: `VADError`, `VADConfigError`
- [ ] Add to `__all__` list

---

## Phase 2: Implement EnergyVADAdapter

### Step 2.1: Create adapters directory structure

```bash
mkdir -p chatforge/adapters/vad
touch chatforge/adapters/vad/__init__.py
touch chatforge/adapters/vad/energy.py
```

**Checklist**:
- [ ] Create `chatforge/adapters/vad/` directory
- [ ] Create `__init__.py`
- [ ] Create `energy.py`

### Step 2.2: Extract core logic from VoxStream

**File**: `chatforge/adapters/vad/energy.py`

**Source reference**: `voxstream/voice/vad.py` lines 47-286 (VADetector class)

```python
# Key components to extract:
# 1. _calculate_energy() - RMS energy calculation
# 2. process_chunk() - State machine logic (use current implementation, not old_process_chunk)
# 3. Pre-buffer management (deque with maxlen)
# 4. Energy history smoothing (ring buffer of 5 samples)
# 5. Callback handling
# 6. Metrics tracking
# 7. reset() method

# THREAD SAFETY REQUIREMENTS:
# - process_chunk() may run in audio callback thread
# - Must complete in <10ms with minimal allocations
# - Callbacks must be non-blocking
# - Use pre-allocated numpy buffers where possible
```

**Checklist**:
- [ ] Create `EnergyVADAdapter` class implementing `VADPort`
- [ ] Implement `__init__(config: VADConfig | None = None)`
  - Initialize state to `SpeechState.SILENCE`
  - Initialize `state_duration_ms = 0.0`
  - Create pre-buffer deque with `maxlen` based on `pre_buffer_ms`
  - Create energy history ring buffer (size 5) for smoothing
  - Calculate `_bytes_per_ms` for variable chunk handling
  - Initialize metrics
- [ ] Implement `_calculate_rms(chunk: bytes) -> float`
  - Convert bytes to numpy array (int16)
  - Normalize to -1.0 to 1.0
  - Calculate RMS energy
  - Return normalized 0.0-1.0 value
- [ ] Implement `_get_smoothed_energy(energy: float) -> float`
  - Add to ring buffer
  - Return mean of buffer
- [ ] Implement `process_chunk(chunk: bytes) -> VADResult`
  - Handle empty chunks (return current state)
  - Calculate chunk_duration_ms from `len(chunk) / self._bytes_per_ms`
  - Calculate energy and smooth it
  - Update pre-buffer (append chunk)
  - Run state machine:
    - `SILENCE` + speech → `SPEECH_STARTING`, reset duration
    - `SPEECH_STARTING` + speech → accumulate, if >= speech_start_ms → `SPEECH`, fire callback
    - `SPEECH_STARTING` + silence → `SILENCE` (false start)
    - `SPEECH` + silence → `SPEECH_ENDING`, reset duration
    - `SPEECH_ENDING` + silence → accumulate, if >= speech_end_ms → `SILENCE`, fire callback
    - `SPEECH_ENDING` + speech → `SPEECH` (speech resumed)
  - Update metrics based on state
  - Return VADResult with all fields
- [ ] Implement `set_callbacks(on_speech_start, on_speech_end)`
  - Both callbacks are `Callable[[], None]` (no arguments)
  - Store callbacks
- [ ] Implement `get_pre_buffer() -> bytes`
  - Return `b''.join(self._pre_buffer)`
  - Document: returns copy, internal buffer keeps rolling
- [ ] Implement `get_metrics() -> VADMetrics`
  - Return current metrics snapshot
- [ ] Implement `reset() -> None`
  - Reset state to SILENCE
  - Clear state_duration_ms
  - Clear pre_buffer
  - Clear energy_history
  - Reset metrics
- [ ] Implement `configure(config: VADConfig) -> None`
  - Validate config
  - Check sample_rate hasn't changed (raise VADConfigError if it has)
  - Update config
  - Recalculate internal values
- [ ] Implement `@property state -> SpeechState`
- [ ] Implement `@property is_speaking -> bool`
  - Return `self._state in (SpeechState.SPEECH, SpeechState.SPEECH_STARTING, SpeechState.SPEECH_ENDING)`
  - Or stricter: `self._state == SpeechState.SPEECH`
- [ ] Implement `@property config -> VADConfig`

### Step 2.3: Add AdaptiveEnergyVADAdapter

**File**: `chatforge/adapters/vad/energy.py`

**Source reference**: `voxstream/voice/vad.py` lines 419-504 (AdaptiveVAD class)

**Checklist**:
- [ ] Create `AdaptiveEnergyVADAdapter` extending `EnergyVADAdapter`
- [ ] Add `noise_floor: float` tracking
- [ ] Add `is_calibrating: bool` property
- [ ] Add 1-second calibration period on startup
- [ ] Override `process_chunk()`:
  - During calibration: collect noise samples, update noise_floor
  - After calibration: set threshold to `max(0.02, noise_floor * 3)`
  - During silence: slowly adapt threshold
- [ ] Add `recalibrate() -> None` method to force recalibration

### Step 2.4: Export from adapters package

**File**: `chatforge/adapters/vad/__init__.py`

```python
from chatforge.adapters.vad.energy import EnergyVADAdapter, AdaptiveEnergyVADAdapter

__all__ = ["EnergyVADAdapter", "AdaptiveEnergyVADAdapter"]
```

**Checklist**:
- [ ] Export adapters from `__init__.py`

---

## Phase 3: Write Tests

### Step 3.1: Create test file structure

```bash
mkdir -p tests/adapters/vad
touch tests/adapters/vad/__init__.py
touch tests/adapters/vad/test_energy_vad.py
touch tests/adapters/vad/fixtures.py
```

**Checklist**:
- [ ] Create test directory `tests/adapters/vad/`
- [ ] Create `__init__.py`
- [ ] Create `test_energy_vad.py`
- [ ] Create `fixtures.py`

### Step 3.2: Create test audio fixtures

**File**: `tests/adapters/vad/fixtures.py`

```python
# Helpers:
# 1. generate_silence(duration_ms, sample_rate=24000) -> bytes
# 2. generate_tone(duration_ms, frequency=440, amplitude=0.5, sample_rate=24000) -> bytes
# 3. generate_speech_sequence(silence_ms, speech_ms, trailing_silence_ms, chunk_ms=100) -> List[bytes]
# 4. chunk_audio(audio: bytes, chunk_ms, sample_rate=24000) -> List[bytes]
```

**Checklist**:
- [ ] Create `generate_silence()` helper
- [ ] Create `generate_tone()` helper
- [ ] Create `generate_speech_sequence()` helper for timing tests
- [ ] Create `chunk_audio()` helper

### Step 3.3: Unit tests for EnergyVADAdapter

**File**: `tests/adapters/vad/test_energy_vad.py`

```python
# Test cases:
# 1. test_initial_state - Starts in SILENCE
# 2. test_silence_detection - Low energy returns SILENCE
# 3. test_speech_detection - High energy triggers state transitions
# 4. test_speech_start_timing - Requires speech_start_ms to confirm
# 5. test_speech_end_timing - Requires speech_end_ms to end
# 6. test_false_start - Brief speech returns to SILENCE
# 7. test_speech_resume - Speech during SPEECH_ENDING returns to SPEECH
# 8. test_callback_on_speech_start - Callback fires when SPEECH confirmed
# 9. test_callback_on_speech_end - Callback fires when SILENCE confirmed
# 10. test_pre_buffer_contains_audio - Pre-buffer has recent audio
# 11. test_metrics_tracking - Metrics update correctly
# 12. test_reset_clears_state - Reset returns to initial state
# 13. test_configure_updates_thresholds - Config changes work
# 14. test_configure_rejects_sample_rate_change - Sample rate change raises error
# 15. test_variable_chunk_sizes - Works with different chunk sizes
# 16. test_energy_smoothing - Energy history prevents false triggers
```

**Checklist**:
- [ ] Test initial state is SILENCE
- [ ] Test silence detection (low energy → SILENCE)
- [ ] Test state transitions with proper timing:
  - [ ] SILENCE → SPEECH_STARTING (on first speech frame)
  - [ ] SPEECH_STARTING → SPEECH (after speech_start_ms)
  - [ ] SPEECH → SPEECH_ENDING (on first silence frame)
  - [ ] SPEECH_ENDING → SILENCE (after speech_end_ms)
- [ ] Test false start (SPEECH_STARTING → SILENCE on silence)
- [ ] Test speech resume (SPEECH_ENDING → SPEECH on speech)
- [ ] Test on_speech_start callback fires at right time
- [ ] Test on_speech_end callback fires at right time
- [ ] Test get_pre_buffer() returns correct audio
- [ ] Test metrics update correctly
- [ ] Test reset() clears state
- [ ] Test configure() with valid config
- [ ] Test configure() rejects sample_rate change
- [ ] Test with variable chunk sizes (50ms, 100ms, 200ms)

---

## Phase 4: Integrate with VoxStream

### Step 4.1: Update VoxStream to accept VADPort

**File**: `voxstream/core/stream.py`

**Current**: VAD is created internally via `VADetector`
**Target**: Accept optional `vad: VADPort` parameter

```python
class VoxStream:
    def __init__(
        self,
        config: Optional[StreamConfig] = None,
        vad_config: Optional[VADConfig] = None,
        vad: Optional[VADPort] = None,  # NEW: Inject VAD
        ...
    ):
        # If vad is provided, use it
        # Otherwise, create default EnergyVADAdapter
        if vad:
            self._vad = vad
        elif vad_config:
            self._vad = EnergyVADAdapter(vad_config)
        else:
            self._vad = None
```

**Checklist**:
- [ ] Add `vad: VADPort | None = None` parameter to `__init__`
- [ ] Import `VADPort` from chatforge
- [ ] Import `EnergyVADAdapter` from chatforge
- [ ] Create default VAD if not provided but vad_config given
- [ ] Wire VAD callbacks to VoxStream's internal handlers
- [ ] Maintain backward compatibility with existing code

### Step 4.2: Update VAD usage in VoxStream

**File**: `voxstream/core/stream.py`

**Checklist**:
- [ ] Replace `from voxstream.voice.vad import VADetector` usage
- [ ] Use VADPort interface methods:
  - `process_chunk()` instead of direct call
  - `get_pre_buffer()` when needed
  - `reset()` on session reset
- [ ] Update callback wiring:
  ```python
  if self._vad:
      self._vad.set_callbacks(
          on_speech_start=self._on_speech_start_internal,
          on_speech_end=self._on_speech_end_internal,
      )
  ```

### Step 4.3: Update AudioManager

**File**: `voxstream/io/manager.py`

**Checklist**:
- [ ] Accept optional `vad: VADPort` parameter
- [ ] Pass VAD to VoxStream or use directly
- [ ] Maintain backward compatibility

### Step 4.4: Verify voxterm still works

**Checklist**:
- [ ] Run voxterm with default adapter
- [ ] Test speech detection works
- [ ] Test pre-buffer functionality
- [ ] Verify metrics are available
- [ ] Test reset between sessions

---

## Phase 5: Add Alternative Adapters (Optional)

### Step 5.1: Implement SileroVADAdapter

**File**: `chatforge/adapters/vad/silero.py`

**Dependencies**: `pip install torch torchaudio` (optional, heavy)

**IMPORTANT**: Silero VAD requires 16kHz audio, not 24kHz. Must resample.

```python
class SileroVADAdapter(VADPort):
    """ML-based VAD using Silero."""

    def __init__(
        self,
        config: VADConfig | None = None,
        model_path: str | None = None,  # Optional local model path
    ):
        import torch
        self._config = config or VADConfig()

        # Silero expects 16kHz - we'll resample
        self._silero_sample_rate = 16000
        self._resample_ratio = 16000 / self._config.sample_rate

        # Load model
        if model_path:
            self._model = torch.jit.load(model_path)
        else:
            self._model, _ = torch.hub.load(
                'snakers4/silero-vad', 'silero_vad',
                force_reload=False
            )
        self._model.eval()
        ...

    def _resample_to_16k(self, chunk: bytes) -> np.ndarray:
        """Resample from config.sample_rate to 16kHz for Silero."""
        # Use scipy.signal.resample or torchaudio
        ...
```

**Checklist**:
- [ ] Create `silero.py`
- [ ] Implement `SileroVADAdapter`
- [ ] Add resampling to 16kHz
- [ ] Handle lazy model loading
- [ ] Support local model path (no internet required)
- [ ] Implement same state machine as EnergyVADAdapter
- [ ] Add to `__init__.py` exports (optional import with try/except)
- [ ] Add tests (skip if torch not installed)

### Step 5.2: Note on WebRTC VAD

**WebRTC VAD is NOT recommended** due to sample rate constraints:
- Only supports: 8kHz, 16kHz, 32kHz, 48kHz
- Does NOT support 24kHz (OpenAI Realtime API standard)
- Would require resampling which adds latency and complexity

If needed later, create `chatforge/adapters/vad/webrtc.py` with:
- Resampling to 16kHz
- Frame size handling (10, 20, or 30ms only)
- Internal buffering for frame alignment

**Recommendation**: Skip WebRTC VAD for initial implementation.

---

## Phase 6: Documentation and Examples

### Step 6.1: Update flow_diagrams.md

**File**: `voxterm/flow_diagrams.md`

Add VAD state machine diagram:

```
## VAD State Machine

┌─────────┐  speech detected   ┌──────────────────┐
│ SILENCE │──────────────────►│ SPEECH_STARTING  │
└─────────┘                    └──────────────────┘
     ▲                                │
     │                                │ speech_start_ms elapsed
     │                                ▼
     │ speech_end_ms elapsed   ┌──────────────────┐
     │◄────────────────────────│     SPEECH       │
     │                         └──────────────────┘
     │                                │
     │                                │ silence detected
     │                                ▼
     │                         ┌──────────────────┐
     └─────────────────────────│ SPEECH_ENDING    │──► speech resumes → SPEECH
                               └──────────────────┘
```

**Checklist**:
- [ ] Add VAD state machine diagram
- [ ] Add VAD callback flow
- [ ] Document pre-buffer behavior

### Step 6.2: Create usage examples

**File**: `chatforge/adapters/vad/README.md`

```markdown
# VAD Adapters

## Usage

### Basic Usage
```python
from chatforge.adapters.vad import EnergyVADAdapter
from chatforge.ports.vad import VADConfig

vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))

# Callbacks are called with no arguments
vad.set_callbacks(
    on_speech_start=lambda: print("Speech started"),
    on_speech_end=lambda: print("Speech ended"),
)

for chunk in audio_stream:
    result = vad.process_chunk(chunk)
    if result.is_speaking:
        send_to_ai(chunk)
```

### Getting Pre-buffer
```python
def handle_speech_start():
    # Get audio captured before speech was detected
    pre_buffer = vad.get_pre_buffer()
    print(f"Pre-buffer: {len(pre_buffer)} bytes")

vad.set_callbacks(on_speech_start=handle_speech_start)
```

### With VoxStream
```python
from voxstream import VoxStream
from chatforge.adapters.vad import EnergyVADAdapter

vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))
stream = VoxStream(vad=vad)
```

### Metrics
```python
metrics = vad.get_metrics()
print(f"Speech segments: {metrics.speech_segments}")
print(f"Total speech: {metrics.total_speech_ms}ms")
```
```

**Checklist**:
- [ ] Create README.md with examples
- [ ] Document each adapter
- [ ] Document configuration options
- [ ] Document thread safety requirements
- [ ] Document pre-buffer behavior

---

## Verification Checklist

### Phase 1 Complete
- [ ] `chatforge/ports/vad.py` exists with full interface
- [ ] SpeechState uses correct names (SPEECH_STARTING, not SPEECH_START)
- [ ] VADMetrics included in interface
- [ ] Exports work: `from chatforge.ports import VADPort, VADConfig, VADMetrics`

### Phase 2 Complete
- [ ] `chatforge/adapters/vad/energy.py` exists
- [ ] EnergyVADAdapter implements VADPort
- [ ] State machine matches VoxStream behavior
- [ ] Energy smoothing implemented (ring buffer)
- [ ] Metrics tracking implemented
- [ ] Exports work: `from chatforge.adapters.vad import EnergyVADAdapter`

### Phase 3 Complete
- [ ] All unit tests pass
- [ ] State transition timing tests pass
- [ ] Test coverage > 80%

### Phase 4 Complete
- [ ] VoxStream accepts `vad: VADPort`
- [ ] Backward compatibility maintained
- [ ] voxterm works with new VAD

### Phase 5 Complete (Optional)
- [ ] SileroVADAdapter works (if torch available)
- [ ] Resampling to 16kHz implemented

### Phase 6 Complete
- [ ] Documentation updated
- [ ] Examples work

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `chatforge/ports/vad.py` | VADPort interface, VADConfig, VADResult, VADMetrics, SpeechState |
| `chatforge/adapters/vad/__init__.py` | Adapter exports |
| `chatforge/adapters/vad/energy.py` | EnergyVADAdapter, AdaptiveEnergyVADAdapter |
| `chatforge/adapters/vad/silero.py` | SileroVADAdapter (optional) |
| `tests/adapters/vad/test_energy_vad.py` | Unit tests |
| `tests/adapters/vad/fixtures.py` | Test helpers |

### Modified Files

| File | Changes |
|------|---------|
| `chatforge/ports/__init__.py` | Add VADPort exports |
| `voxstream/core/stream.py` | Accept `vad: VADPort` param |
| `voxstream/io/manager.py` | Use VADPort |
| `voxterm/flow_diagrams.md` | Add VAD flow |

---

## Dependencies

### Required
- numpy (already in voxstream)

### Optional
- torch, torchaudio (~150MB+) - for SileroVADAdapter

### NOT Recommended
- webrtcvad - incompatible with 24kHz sample rate

---

## Thread Safety Requirements

**CRITICAL**: VAD may run in audio callback thread.

1. `process_chunk()` must complete in <10ms
2. Minimize allocations in hot path:
   - Use pre-allocated numpy buffers
   - Use deque with maxlen for pre-buffer
   - Use fixed-size ring buffer for energy history
3. Callbacks must be non-blocking:
   - Document that callbacks run in audio thread
   - Users should queue work, not process inline
4. State access should be atomic or read-only in callbacks

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| State machine behavior mismatch | Use exact VoxStream state names, comprehensive tests |
| Performance regression | Benchmark before/after, ensure <10ms latency |
| Breaking VoxStream | Maintain backward compatibility with default VAD |
| Silero 16kHz mismatch | Implement resampling in adapter |
| Thread safety issues | Document requirements, use pre-allocated buffers |
| Variable chunk sizes | Calculate duration from bytes, not assume fixed size |
