# Audio Formats: VoxStream

**Date:** 2025-01-01
**Scope:** Local audio I/O only (AudioStreamPort)

---

## 1. What format does VoxStream use?

**Answer: PCM16, 24kHz, Mono by default**

From `config/types.py:50-63`:
```python
@dataclass
class StreamConfig:
    sample_rate: int = 24000      # 24kHz standard
    channels: int = 1             # Mono
    bit_depth: int = 16           # 16-bit
    format: AudioFormat = AudioFormat.PCM16
```

**Audio format enum:**
```python
class AudioFormat(Enum):
    PCM16 = "pcm16"
    G711_ULAW = "g711_ulaw"
    G711_ALAW = "g711_alaw"
```

---

## 2. Chunk size calculation

**Answer: Configurable via `chunk_duration_ms`**

From `config/types.py:103-108`:
```python
def chunk_size_bytes(self, duration_ms: int) -> int:
    """Calculate chunk size in bytes for given duration"""
    return int(duration_ms * self.bytes_per_ms)

# For 100ms at 24kHz mono 16-bit:
# 24000 samples/sec * 0.1 sec * 1 channel * 2 bytes = 4800 bytes
```

**Default chunk sizes by mode:**
```python
REALTIME:  20ms  = 960 bytes
BALANCED:  100ms = 4800 bytes
QUALITY:   200ms = 9600 bytes
```

---

## 3. Bytes per millisecond calculation

From `config/types.py:94-100`:
```python
@property
def bytes_per_second(self) -> int:
    """Bytes per second of audio"""
    return self.sample_rate * self.frame_size  # 24000 * 2 = 48000

@property
def bytes_per_ms(self) -> float:
    """Bytes per millisecond"""
    return self.bytes_per_second / 1000  # 48 bytes/ms
```

---

## 4. Supported sample rates

From `config/types.py:373`:
```python
SUPPORTED_SAMPLE_RATES = [8000, 16000, 24000, 44100, 48000]
```

---

## 5. Format configurability

VoxStream allows configuring:
- `sample_rate`: 8000, 16000, 24000, 44100, 48000
- `channels`: 1 (mono) or 2 (stereo)
- `bit_depth`: 8, 16, 24, 32
- `format`: PCM16, G711_ULAW, G711_ALAW

---

## Summary: VoxStream Default Format

| Property | Default Value |
|----------|---------------|
| Encoding | PCM16 |
| Sample Rate | 24000 Hz |
| Channels | 1 (Mono) |
| Bit Depth | 16 |
| Chunk Duration | 100ms |
| Bytes per Chunk | 4800 |

---

## Design Decision: AudioStreamPort Standard Format

**Recommendation:** Let adapters define their native format, expose via config.

```python
@dataclass
class AudioStreamConfig:
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100
```

AudioStreamPort is **format-agnostic** - it passes bytes. The consumer (e.g., RealtimeVoiceAPIPort) is responsible for any format conversion if needed.
