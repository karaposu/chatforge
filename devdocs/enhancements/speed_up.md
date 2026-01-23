# Audio Playback Speed Control

## Overview

This document explores options for adding playback speed control to chatforge's audio system, allowing users to speed up (or slow down) AI voice responses.

## Architecture Context

Audio flows through two layers:

```
┌─────────────────────┐     ┌──────────────────────┐
│  Realtime Adapters  │     │  Playback Adapter    │
│  (OpenAI, Grok)     │ ──► │  (SoundDevice)       │ ──► Speaker
│  WebSocket layer    │     │  Audio output layer  │
└─────────────────────┘     └──────────────────────┘
       Receives                    Plays
       audio chunks                audio chunks
```

- **Realtime Adapters** (`chatforge/adapters/realtime/`) - Receive audio from AI APIs via WebSocket, emit `VoiceEvent` with `AUDIO_CHUNK` type
- **Playback Adapter** (`chatforge/adapters/audio_playback/`) - Takes audio bytes, outputs to speakers via `sounddevice`

## Where Speed Can Be Applied

### Option A: API-Level Speed

Some AI voice APIs may support a `speed` parameter in session configuration, causing the AI to generate audio already at the desired speed.

**Current Status:**
| Provider | Speed Support |
|----------|---------------|
| OpenAI Realtime | Not supported (as of Jan 2025) |
| Grok Realtime | Unknown - needs verification |

**Implementation (if/when supported):**

1. Add to `VoiceSessionConfig` in `ports/realtime_voice.py`:
```python
@dataclass
class VoiceSessionConfig:
    # ... existing fields ...
    speed: float = 1.0  # 0.5 to 2.0
```

2. Pass in `messages.session_update()`:
```python
def session_update(config: VoiceSessionConfig) -> dict:
    session = {
        # ... existing fields ...
    }
    if config.speed != 1.0:
        session["speed"] = config.speed
    return {"type": "session.update", "session": session}
```

**Pros:** Clean, no quality loss, no extra CPU
**Cons:** Provider must support it

---

### Option B: Playback-Level Speed (Recommended)

Process audio chunks before playback. Works regardless of API support.

#### B1: Simple Resampling (Changes Pitch)

Fastest, simplest approach. Play at higher sample rate = faster + higher pitch.

**Files to modify:**

1. `ports/audio_playback.py` - Add speed to config:
```python
@dataclass
class AudioPlaybackConfig:
    # ... existing fields ...
    speed: float = 1.0  # 0.5 to 2.0
```

2. `adapters/audio_playback/sounddevice_adapter.py` - Apply speed:
```python
# Line ~509, in _playback_loop()
# Before:
sd.play(audio_array, self._config.sample_rate, blocking=True)

# After:
effective_rate = int(self._config.sample_rate * self._config.speed)
sd.play(audio_array, effective_rate, blocking=True)
```

**Pros:** Simple, no dependencies, minimal CPU
**Cons:** Pitch changes (1.5x speed = chipmunk voice)

#### B2: Time-Stretching (Preserves Pitch)

Use audio processing to change speed without changing pitch.

**Dependencies (choose one):**
- `librosa` - Pure Python, easiest to install
- `pyrubberband` - Better quality, requires rubberband library
- `soundstretch` - CLI tool wrapper

**Implementation with librosa:**

```python
import librosa
import numpy as np

def time_stretch_audio(audio_bytes: bytes, speed: float, sample_rate: int) -> bytes:
    """Stretch audio without changing pitch."""
    # Convert bytes to float array
    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
    audio_float = audio_int16.astype(np.float32) / 32768.0

    # Time stretch
    stretched = librosa.effects.time_stretch(audio_float, rate=speed)

    # Convert back to int16 bytes
    stretched_int16 = (stretched * 32768.0).astype(np.int16)
    return stretched_int16.tobytes()
```

**Integration in SoundDevicePlaybackAdapter:**

```python
def _playback_loop(self) -> None:
    # ... existing code ...

    if chunks_to_play:
        audio_data = b"".join(chunks_to_play)

        # Apply time stretch if speed != 1.0
        if self._config.speed != 1.0:
            audio_data = time_stretch_audio(
                audio_data,
                self._config.speed,
                self._config.sample_rate
            )

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio_array, self._config.sample_rate, blocking=True)
```

**Pros:** Natural voice at any speed
**Cons:** Adds dependency, more CPU usage, slight latency

---

## Difficulty Assessment

| Approach | Difficulty | Quality | Dependencies |
|----------|------------|---------|--------------|
| API-level | Easy | Best | None (if supported) |
| B1: Resample | Easy | Poor (pitch change) | None |
| B2: librosa | Medium | Good | librosa (~50MB) |
| B2: rubberband | Medium | Best | pyrubberband + system lib |

---

## Recommended Implementation

**Phase 1: Simple resampling (B1)**
- Add `speed` param to `AudioPlaybackConfig`
- Multiply sample rate in playback
- Quick win, users can try it

**Phase 2: Optional time-stretch (B2)**
- Add optional `preserve_pitch: bool = False` param
- If True and librosa available, use time-stretch
- Graceful fallback to resampling if librosa not installed

---

## Files to Modify

| File | Change |
|------|--------|
| `ports/audio_playback.py:116` | Add `speed: float = 1.0` to `AudioPlaybackConfig` |
| `ports/audio_playback.py:153` | Add validation in `__post_init__` |
| `adapters/audio_playback/sounddevice_adapter.py:509` | Apply speed during playback |
| `adapters/audio_playback/file_sink.py` | Update WAV header sample rate if speed applied |
| `adapters/audio_playback/null_adapter.py` | No change needed |

---

## Usage Example (After Implementation)

```python
from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
from chatforge.ports.audio_playback import AudioPlaybackConfig

# 1.5x speed playback
config = AudioPlaybackConfig(
    sample_rate=24000,
    speed=1.5,  # NEW
)
player = SoundDevicePlaybackAdapter(config)

# Use with realtime voice
async for event in realtime.events():
    if event.type == VoiceEventType.AUDIO_CHUNK:
        player.play(event.data)  # Plays at 1.5x speed
```

---

## Open Questions

1. Should speed be configurable per-chunk or only at init?
2. Should we support real-time speed changes during playback?
3. Is librosa dependency acceptable, or should time-stretch be a separate optional package?
