# VADPort Design Document

## Overview

**VADPort** (Voice Activity Detection Port) provides a platform-agnostic interface for detecting speech in audio streams. This enables consistent VAD behavior across desktop, web, and mobile platforms.

## Problem Statement

### Current State

VAD is currently embedded inside VoxStream:

```
voxstream/
  voice/
    vad.py  ← VADetector (energy-based)
```

This creates problems:

1. **Platform Lock-in**: Web/mobile can't use VoxStream's VAD
2. **Duplication**: Each platform would need its own VAD
3. **Inconsistency**: Different VAD behavior per platform
4. **Testing**: Can't test VAD without audio hardware

### Desired State

VAD as a separate, reusable component:

```
chatforge/
  ports/
    vad.py  ← Platform-agnostic interface
  adapters/
    vad/
      energy.py    ← Simple, fast
      silero.py    ← ML-based, accurate
      webrtc.py    ← Google's WebRTC VAD
```

---

## Use Cases

### 1. Desktop Voice Chat (VoxStream)

```python
async with VoxStreamAdapter(vad=EnergyVADAdapter()) as audio:
    audio.set_callbacks(AudioCallbacks(
        on_speech_start=lambda: print("Speaking..."),
        on_speech_end=lambda pre_buffer: process(pre_buffer),
    ))
    async for chunk in audio.start_capture():
        await send_to_ai(chunk)
```

### 2. Web Voice Chat (WebRTC)

```python
# Same VAD works for web!
async with WebRTCAudioAdapter(vad=EnergyVADAdapter()) as audio:
    audio.set_callbacks(AudioCallbacks(
        on_speech_start=handle_start,
        on_speech_end=handle_end,
    ))
    async for chunk in audio.capture_stream():
        await send_to_ai(chunk)
```

### 3. High-Accuracy VAD (ML-based)

```python
# Swap to ML-based VAD for better accuracy
vad = SileroVADAdapter(threshold=0.5)
async with VoxStreamAdapter(vad=vad) as audio:
    ...
```

### 4. Testing with Audio Files

```python
# Test VAD without hardware
vad = EnergyVADAdapter()
vad.set_callbacks(on_speech_start=..., on_speech_end=...)

with open("test_audio.raw", "rb") as f:
    while chunk := f.read(4800):  # 100ms chunks
        vad.process_chunk(chunk)
```

### 5. Server-Side VAD (Batch Processing)

```python
# Analyze recorded audio
vad = SileroVADAdapter()
segments = []

for chunk in audio_chunks:
    result = vad.process_chunk(chunk)
    if result.speech_probability > 0.7:
        segments.append(chunk)
```

---

## Architecture

### Port Interface

```
┌─────────────────────────────────────────────────────────┐
│                       VADPort                           │
│                   (Abstract Interface)                  │
├─────────────────────────────────────────────────────────┤
│  process_chunk(bytes) -> VADResult                      │
│  set_callbacks(on_speech_start, on_speech_end)          │
│  reset()                                                │
│  configure(VADConfig)                                   │
├─────────────────────────────────────────────────────────┤
│  Properties:                                            │
│    is_speaking: bool                                    │
│    pre_buffer: bytes                                    │
│    config: VADConfig                                    │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────┴───────┐ ┌──────┴──────┐ ┌────────┴───────┐
│ EnergyVAD      │ │  SileroVAD  │ │  WebRTCVAD     │
│ Adapter        │ │  Adapter    │ │  Adapter       │
├────────────────┤ ├─────────────┤ ├────────────────┤
│ RMS energy     │ │ Neural net  │ │ Google's VAD   │
│ Simple, fast   │ │ Accurate    │ │ Balanced       │
│ No deps        │ │ torch req'd │ │ webrtcvad req  │
└────────────────┘ └─────────────┘ └────────────────┘
```

### Integration with AudioStreamPort

```
┌─────────────────────────────────────────────────────────┐
│                   AudioStreamPort                        │
│              (Mic/Speaker Interface)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌─────────────┐                    │
│  │   Capture   │───►│   VADPort   │──► Events          │
│  │   Stream    │    │  (optional) │                    │
│  └─────────────┘    └─────────────┘                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    VoxStream         WebRTCAudio       TwilioAudio
    (desktop)           (web)            (phone)
```

---

## Port Interface Specification

### Core Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class SpeechState(Enum):
    """Current speech detection state."""
    SILENCE = "silence"
    SPEECH_START = "speech_start"
    SPEAKING = "speaking"
    SPEECH_END = "speech_end"


@dataclass
class VADConfig:
    """VAD configuration."""
    # Detection thresholds
    energy_threshold: float = 0.01      # RMS threshold (energy-based)
    speech_probability: float = 0.5     # ML threshold (0.0-1.0)

    # Timing (milliseconds)
    speech_start_ms: int = 100          # Consecutive speech to trigger start
    speech_end_ms: int = 500            # Consecutive silence to trigger end
    pre_buffer_ms: int = 300            # Audio to keep before speech start

    # Audio format (for buffer calculations)
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16


@dataclass
class VADResult:
    """Result from processing a chunk."""
    state: SpeechState
    is_speaking: bool
    speech_probability: float           # 0.0-1.0, confidence
    energy: float                       # RMS energy level


class VADPort(ABC):
    """
    Abstract interface for Voice Activity Detection.

    Platform-agnostic VAD that works with any audio source.

    Example:
        vad = EnergyVADAdapter()
        vad.set_callbacks(
            on_speech_start=lambda: print("Started"),
            on_speech_end=lambda audio: process(audio),
        )

        for chunk in audio_stream:
            result = vad.process_chunk(chunk)
            if result.is_speaking:
                send_to_ai(chunk)
    """

    # -------------------------------------------------------------------------
    # Abstract Properties
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def is_speaking(self) -> bool:
        """Whether speech is currently detected."""
        pass

    @property
    @abstractmethod
    def config(self) -> VADConfig:
        """Current VAD configuration."""
        pass

    # -------------------------------------------------------------------------
    # Abstract Methods
    # -------------------------------------------------------------------------

    @abstractmethod
    def process_chunk(self, chunk: bytes) -> VADResult:
        """
        Process audio chunk and detect speech.

        Args:
            chunk: PCM16 audio bytes

        Returns:
            VADResult with speech state and metrics

        Note:
            This method may trigger on_speech_start or on_speech_end
            callbacks based on state transitions.
        """
        pass

    @abstractmethod
    def set_callbacks(
        self,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[bytes], None]] = None,
    ) -> None:
        """
        Set speech event callbacks.

        Args:
            on_speech_start: Called when speech begins
            on_speech_end: Called when speech ends, receives pre-buffer audio
        """
        pass

    @abstractmethod
    def get_pre_buffer(self) -> bytes:
        """
        Get buffered audio from before speech was detected.

        Returns:
            Audio bytes captured before speech_start (up to pre_buffer_ms)
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset VAD state.

        Call between utterances or when starting fresh.
        Clears speech state and pre-buffer.
        """
        pass

    @abstractmethod
    def configure(self, config: VADConfig) -> None:
        """
        Update VAD configuration.

        Args:
            config: New configuration to apply
        """
        pass
```

---

## Adapter Implementations

### 1. EnergyVADAdapter (Simple, Fast)

```python
# chatforge/adapters/vad/energy.py

from collections import deque
import struct

class EnergyVADAdapter(VADPort):
    """
    Energy-based VAD using RMS amplitude.

    Simple and fast, no external dependencies.
    Good for: Low-latency, resource-constrained environments.

    Algorithm:
        1. Calculate RMS energy of chunk
        2. Compare to threshold
        3. Track consecutive speech/silence frames
        4. Trigger events based on timing thresholds
    """

    def __init__(self, config: VADConfig | None = None):
        self._config = config or VADConfig()
        self._is_speaking = False
        self._speech_frames = 0
        self._silence_frames = 0
        self._pre_buffer: deque[bytes] = deque()
        self._on_speech_start = None
        self._on_speech_end = None

        # Calculate frame counts from ms
        self._update_frame_counts()

    def _update_frame_counts(self):
        chunk_ms = 100  # Assuming 100ms chunks
        self._speech_start_frames = self._config.speech_start_ms // chunk_ms
        self._speech_end_frames = self._config.speech_end_ms // chunk_ms
        self._pre_buffer_frames = self._config.pre_buffer_ms // chunk_ms

    def _calculate_rms(self, chunk: bytes) -> float:
        """Calculate RMS energy of PCM16 audio."""
        samples = struct.unpack(f"<{len(chunk)//2}h", chunk)
        if not samples:
            return 0.0
        sum_squares = sum(s * s for s in samples)
        rms = (sum_squares / len(samples)) ** 0.5
        return rms / 32768.0  # Normalize to 0.0-1.0

    def process_chunk(self, chunk: bytes) -> VADResult:
        energy = self._calculate_rms(chunk)
        is_speech = energy > self._config.energy_threshold

        # Update pre-buffer (ring buffer)
        self._pre_buffer.append(chunk)
        while len(self._pre_buffer) > self._pre_buffer_frames:
            self._pre_buffer.popleft()

        # State machine
        old_speaking = self._is_speaking

        if is_speech:
            self._speech_frames += 1
            self._silence_frames = 0

            if not self._is_speaking and self._speech_frames >= self._speech_start_frames:
                self._is_speaking = True
                if self._on_speech_start:
                    self._on_speech_start()
        else:
            self._silence_frames += 1
            self._speech_frames = 0

            if self._is_speaking and self._silence_frames >= self._speech_end_frames:
                self._is_speaking = False
                if self._on_speech_end:
                    pre_buffer = self.get_pre_buffer()
                    self._on_speech_end(pre_buffer)

        # Determine state
        if not old_speaking and self._is_speaking:
            state = SpeechState.SPEECH_START
        elif old_speaking and not self._is_speaking:
            state = SpeechState.SPEECH_END
        elif self._is_speaking:
            state = SpeechState.SPEAKING
        else:
            state = SpeechState.SILENCE

        return VADResult(
            state=state,
            is_speaking=self._is_speaking,
            speech_probability=min(1.0, energy / self._config.energy_threshold),
            energy=energy,
        )

    # ... implement remaining methods
```

### 2. SileroVADAdapter (ML-Based, Accurate)

```python
# chatforge/adapters/vad/silero.py

class SileroVADAdapter(VADPort):
    """
    ML-based VAD using Silero VAD model.

    Highly accurate, handles noise well.
    Good for: Noisy environments, production use.

    Requirements:
        pip install torch torchaudio

    Model:
        Silero VAD (https://github.com/snakers4/silero-vad)
        ~1MB model, runs on CPU
    """

    def __init__(self, config: VADConfig | None = None):
        self._config = config or VADConfig()
        self._model = None
        self._load_model()
        # ... similar state tracking

    def _load_model(self):
        import torch
        self._model, _ = torch.hub.load(
            'snakers4/silero-vad',
            'silero_vad',
            force_reload=False
        )
        self._model.eval()

    def process_chunk(self, chunk: bytes) -> VADResult:
        import torch
        import numpy as np

        # Convert bytes to tensor
        audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        tensor = torch.from_numpy(audio)

        # Get speech probability
        with torch.no_grad():
            prob = self._model(tensor, self._config.sample_rate).item()

        is_speech = prob > self._config.speech_probability
        # ... similar state machine logic

        return VADResult(
            state=state,
            is_speaking=self._is_speaking,
            speech_probability=prob,
            energy=self._calculate_rms(chunk),
        )
```

### 3. WebRTCVADAdapter (Balanced)

```python
# chatforge/adapters/vad/webrtc.py

class WebRTCVADAdapter(VADPort):
    """
    Google's WebRTC VAD.

    Good balance of accuracy and speed.

    Requirements:
        pip install webrtcvad

    Aggressiveness levels:
        0: Least aggressive (more false positives)
        3: Most aggressive (may miss soft speech)
    """

    def __init__(
        self,
        config: VADConfig | None = None,
        aggressiveness: int = 2,  # 0-3
    ):
        import webrtcvad
        self._vad = webrtcvad.Vad(aggressiveness)
        self._config = config or VADConfig()
        # ...

    def process_chunk(self, chunk: bytes) -> VADResult:
        # WebRTC VAD needs specific frame sizes (10, 20, or 30ms)
        is_speech = self._vad.is_speech(chunk, self._config.sample_rate)
        # ... state machine
```

---

## Comparison

| Adapter | Accuracy | Speed | Dependencies | Best For |
|---------|----------|-------|--------------|----------|
| **EnergyVAD** | Medium | Very Fast | None | Low-latency, simple apps |
| **SileroVAD** | High | Medium | torch (~150MB) | Production, noisy envs |
| **WebRTCVAD** | Good | Fast | webrtcvad (~1MB) | Balanced performance |

---

## Integration Examples

### With VoxStreamAdapter

```python
from chatforge.adapters.audio import VoxStreamAdapter
from chatforge.adapters.vad import EnergyVADAdapter

# Create VAD
vad = EnergyVADAdapter(VADConfig(
    energy_threshold=0.02,
    speech_end_ms=800,
))

# Inject into audio adapter
async with VoxStreamAdapter(vad=vad) as audio:
    audio.set_callbacks(AudioCallbacks(
        on_speech_start=lambda: print("Speech started"),
        on_speech_end=lambda audio: print(f"Speech ended, {len(audio)} bytes"),
    ))

    async for chunk in audio.start_capture():
        await realtime.send_audio(chunk)
```

### Standalone VAD Processing

```python
from chatforge.adapters.vad import SileroVADAdapter

vad = SileroVADAdapter()

# Process audio file
with open("recording.raw", "rb") as f:
    while chunk := f.read(4800):  # 100ms @ 24kHz
        result = vad.process_chunk(chunk)
        print(f"Speaking: {result.is_speaking}, Prob: {result.speech_probability:.2f}")
```

### Dynamic VAD Switching

```python
# Start with fast VAD
vad = EnergyVADAdapter()

# Switch to accurate VAD if noisy
if ambient_noise_level > 0.1:
    vad = SileroVADAdapter()

async with VoxStreamAdapter(vad=vad) as audio:
    ...
```

---

## Migration Plan

### Phase 1: Extract from VoxStream

1. Copy VADetector logic to `chatforge/adapters/vad/energy.py`
2. Create VADPort interface in `chatforge/ports/vad.py`
3. Make EnergyVADAdapter implement VADPort

### Phase 2: Update VoxStreamAdapter

1. Add optional `vad: VADPort` parameter to VoxStreamAdapter
2. Default to EnergyVADAdapter for backward compatibility
3. Wire VAD callbacks through to AudioCallbacks

### Phase 3: Add Alternative Adapters

1. Implement SileroVADAdapter
2. Implement WebRTCVADAdapter
3. Add comparison tests

### Phase 4: Cross-Platform Support

1. Use VADPort in WebRTCAudioAdapter
2. Use VADPort in TwilioAudioAdapter
3. Document platform-specific considerations

---

## Open Questions

1. **Async vs Sync**: Should `process_chunk` be async for ML models?
   - Pro: ML inference can be slow
   - Con: Adds complexity, most VAD is fast

2. **Chunk Size Flexibility**: WebRTC VAD needs specific frame sizes
   - Option A: Require specific chunk sizes
   - Option B: Internal reframing in adapter

3. **GPU Support**: Should Silero adapter support GPU?
   - Pro: Faster for batch processing
   - Con: Overkill for real-time VAD

4. **Streaming vs Batch API**: Should there be a batch `process_audio(bytes)` method?
   - Useful for analyzing recorded audio
   - Could return list of speech segments

---

## References

- [Silero VAD](https://github.com/snakers4/silero-vad) - SOTA neural VAD
- [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) - Google's VAD
- [VoxStream VADetector](https://github.com/.../voxstream) - Current implementation
- [OpenAI Realtime VAD](https://platform.openai.com/docs/guides/realtime) - Server-side VAD
