# Trace 16: VAD, Audio Capture, and Audio Playback Ports

The new granular audio ports for voice activity detection, microphone capture, and speaker output.

---

## VADPort (Voice Activity Detection)

**File:** `chatforge/ports/vad.py`
**Interface:** `VADPort` (Abstract Base Class)

### Methods

```python
def configure(config: VADConfig) -> None
def process_audio(chunk: bytes) -> VADResult
def reset() -> None
def get_metrics() -> VADMetrics
```

### Execution Path: VAD Processing

```
Audio chunk from capture
    │
    ├─► vad.process_audio(chunk)
    │   │
    │   │   [Inside VAD implementation]
    │   │
    │   ├─1─► Calculate energy level
    │   │     └── rms = sqrt(mean(samples^2))
    │   │
    │   ├─2─► Compare to threshold
    │   │     └── is_speech = rms > config.energy_threshold
    │   │
    │   ├─3─► Apply temporal smoothing
    │   │     ├── Speech must persist for speech_start_ms
    │   │     └── Silence must persist for speech_end_ms
    │   │
    │   ├─4─► Update state machine
    │   │     ├── SILENCE → SPEECH (if speech detected)
    │   │     └── SPEECH → SILENCE (if silence detected)
    │   │
    │   └─5─► Return VADResult
    │         └── VADResult(
    │                 state=SpeechState.SPEAKING,
    │                 is_speech=True,
    │                 energy_level=0.15,
    │                 speech_duration_ms=1500,
    │                 silence_duration_ms=0,
    │             )
    │
    └─► Caller acts on state change
        ├── SILENCE → SPEAKING: Start sending to AI
        └── SPEAKING → SILENCE: Commit audio, get response
```

### Data Types

```python
class SpeechState(str, Enum):
    SILENCE = "silence"
    SPEAKING = "speaking"

@dataclass
class VADConfig:
    energy_threshold: float = 0.02  # 0.0 - 1.0
    speech_start_ms: int = 100      # Debounce for start
    speech_end_ms: int = 500        # Debounce for end
    pre_buffer_ms: int = 300        # Audio before speech

@dataclass
class VADResult:
    state: SpeechState
    is_speech: bool
    energy_level: float
    speech_duration_ms: int
    silence_duration_ms: int

@dataclass
class VADMetrics:
    total_chunks: int
    speech_chunks: int
    state_changes: int
```

### Implementation: EnergyVADAdapter

**File:** `chatforge/adapters/vad/energy.py`

Simple energy-based detection:
- Compute RMS of audio samples
- Compare to threshold
- Apply temporal smoothing
- Fast, no ML required

---

## AudioCapturePort

**File:** `chatforge/ports/audio_capture.py`
**Interface:** `AudioCapturePort` (Abstract Base Class)

### Methods

```python
async def start() -> None
async def stop() -> None
async def read_chunk() -> bytes
def list_devices() -> list[AudioDevice]
def select_device(device_id: int | None) -> None
def get_metrics() -> CaptureMetrics
```

### Execution Path: Microphone Capture

```
async with SounddeviceCaptureAdapter(config) as capture:
    │
    ├─► __aenter__()
    │   ├── Query audio devices
    │   ├── Initialize sounddevice
    │   └── Allocate buffers
    │
    ├─► await capture.start()
    │   │
    │   ├── Open sounddevice.InputStream
    │   │   └── Parameters from AudioCaptureConfig:
    │   │       - sample_rate: 24000
    │   │       - channels: 1
    │   │       - dtype: int16
    │   │       - blocksize: based on chunk_duration_ms
    │   │
    │   ├── Start capture callback
    │   │   └── _callback(indata, frames, time, status)
    │   │       └── Push to ring buffer
    │   │
    │   └── Set state = CAPTURING
    │
    ├─► Loop: chunk = await capture.read_chunk()
    │   │
    │   ├── Wait for data in buffer
    │   │   └── asyncio.Event for signaling
    │   │
    │   ├── Read chunk from ring buffer
    │   │
    │   └── Return bytes (PCM16)
    │
    └─► await capture.stop()
        │
        ├── Stop sounddevice stream
        ├── Clear buffers
        └── Set state = STOPPED
```

### Data Types

```python
class CaptureState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    CAPTURING = "capturing"
    STOPPING = "stopping"

@dataclass
class AudioCaptureConfig:
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100
    buffer_duration_ms: int = 500
    device_id: int | None = None

@dataclass
class AudioDevice:
    id: int
    name: str
    channels: int
    default_sample_rate: float
    is_default: bool

@dataclass
class CaptureMetrics:
    chunks_captured: int
    bytes_captured: int
    buffer_overflows: int
    capture_duration_ms: int
```

### Implementations

- **SounddeviceCaptureAdapter** - Desktop via sounddevice/portaudio
- **FileCaptureAdapter** - Read from audio file (testing)
- **NullCaptureAdapter** - No-op (testing without audio)

---

## AudioPlaybackPort

**File:** `chatforge/ports/audio_playback.py`
**Interface:** `AudioPlaybackPort` (Abstract Base Class)

### Methods

```python
async def start() -> None
async def stop() -> None
async def write_chunk(chunk: bytes) -> None
async def flush() -> None
async def clear() -> None  # Barge-in support
def list_devices() -> list[OutputDevice]
def select_device(device_id: int | None) -> None
def get_metrics() -> PlaybackMetrics
```

### Execution Path: Speaker Output

```
async with SounddevicePlaybackAdapter(config) as playback:
    │
    ├─► __aenter__()
    │   ├── Query output devices
    │   └── Initialize sounddevice
    │
    ├─► await playback.start()
    │   │
    │   ├── Open sounddevice.OutputStream
    │   ├── Start playback callback
    │   │   └── _callback(outdata, frames, time, status)
    │   │       └── Pull from playback buffer
    │   │
    │   └── Set state = PLAYING
    │
    ├─► Loop: await playback.write_chunk(audio_bytes)
    │   │
    │   ├── Add to playback buffer
    │   │
    │   └── [If buffer was empty]
    │       └── Signal callback to start pulling
    │
    ├─► await playback.flush()
    │   │
    │   └── Wait for buffer to drain completely
    │
    └─► await playback.stop()
        │
        ├── Stop sounddevice stream
        └── Clear buffers

Barge-in scenario:
    │
    └─► await playback.clear()
        │
        ├── Clear playback buffer immediately
        └── Audio output stops (no drain)
```

### Data Types

```python
class PlaybackState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    PLAYING = "playing"
    STOPPING = "stopping"

@dataclass
class AudioPlaybackConfig:
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    buffer_duration_ms: int = 500
    device_id: int | None = None

@dataclass
class OutputDevice:
    id: int
    name: str
    channels: int
    default_sample_rate: float
    is_default: bool

@dataclass
class PlaybackMetrics:
    chunks_played: int
    bytes_played: int
    buffer_underruns: int
    playback_duration_ms: int
```

### Implementations

- **SounddevicePlaybackAdapter** - Desktop via sounddevice
- **FileSinkAdapter** - Write to audio file (testing)
- **NullPlaybackAdapter** - No-op (testing without audio)

---

## Interaction: Full Voice Pipeline

```
                    ┌─────────────────────────────────────────┐
                    │          Voice Application               │
                    └─────────────────────────────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           ▼                            ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  AudioCapturePort   │    │      VADPort        │    │  AudioPlaybackPort  │
│  (microphone)       │    │  (speech detect)    │    │  (speaker)          │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                            │                            ▲
           │        chunk               │                            │
           └────────────────────►       │                            │
                                        │                            │
                    VADResult ◄─────────┘                            │
                        │                                            │
                        ▼                                            │
              ┌─────────────────────┐                                │
              │ RealtimeVoiceAPIPort │                               │
              │ (OpenAI Realtime)   │                                │
              └─────────────────────┘                                │
                        │                                            │
                        │ AUDIO_CHUNK events                         │
                        └────────────────────────────────────────────┘
```

---

## Resource Management

| Port | Key Resources | Release |
|------|---------------|---------|
| VADPort | State buffers | reset() |
| AudioCapturePort | Sound device, ring buffer | __aexit__, stop() |
| AudioPlaybackPort | Sound device, playback buffer | __aexit__, stop() |

**Thread model:**
- sounddevice uses callback threads
- Async interface via queues/events
- Thread-safe ring buffers

---

## What Feels Incomplete

1. **No format conversion:**
   - PCM16 24kHz only
   - No resampling
   - Mismatch with device = error

2. **No automatic device recovery:**
   - Device disconnect = error
   - No hot-plug handling
   - Must restart manually

3. **No volume control:**
   - Fixed gain
   - Can't adjust in software
   - Common need

4. **VAD is energy-only:**
   - No ML-based VAD
   - No WebRTC VAD option
   - Less accurate

5. **No echo cancellation:**
   - Playback heard by capture
   - Must handle externally
   - Critical for full-duplex

---

## What Feels Vulnerable

1. **Ring buffer overflow:**
   - Slow consumer = dropped audio
   - No notification
   - Silent data loss

2. **Device permissions:**
   - OS permission checks
   - Error message unclear
   - Should detect and explain

3. **Buffer sizing:**
   - Too small = choppy
   - Too large = latency
   - No auto-tuning

4. **Callback thread exceptions:**
   - sounddevice catches some
   - Others may crash
   - Hard to debug

---

## What Feels Bad Design

1. **Three ports for audio:**
   - Capture, Playback, VAD separate
   - Could be unified AudioPort
   - Lots of wiring needed

2. **Config naming collision:**
   - `VADConfig` in audio_stream
   - `VADPortConfig` in vad
   - Same concept, different types

3. **Metrics not unified:**
   - Each port has own metrics
   - No aggregate view
   - Should have common base

4. **State enums duplicated:**
   - CaptureState, PlaybackState
   - Same states
   - Should share

5. **No streaming interface:**
   - read_chunk/write_chunk are one-at-a-time
   - No async iterator pattern like AudioStreamPort
   - Inconsistent with older port
