# VoxStream API: Resolved Questions

**Date:** 2025-01-01
**Source:** VoxStream source code inspection

---

## 1. What is VoxStream's exact public API?

**Answer: VoxStream class in `core/stream.py`**

```python
from voxstream import VoxStream
from voxstream.config.types import StreamConfig, VADConfig, ProcessingMode

vs = VoxStream(
    mode=ProcessingMode.REALTIME,  # or BALANCED, QUALITY
    config=StreamConfig(),
    buffer_config=BufferConfig()
)
```

---

## 2. What does `start_capture_stream()` return?

**Answer: `asyncio.Queue[AudioBytes]`**

From `core/stream.py:446-471`:
```python
async def start_capture_stream(self) -> Any:
    """Start audio capture and return an async stream."""
    from voxstream.io.manager import AudioManager, AudioManagerConfig

    # Creates AudioManager internally
    self._audio_manager = AudioManager(config, logger=self.logger)
    await self._audio_manager.initialize()

    # Returns asyncio.Queue
    return await self._audio_manager.start_capture()
```

From `io/manager.py:107-119`:
```python
async def start_capture(self) -> asyncio.Queue[AudioBytes]:
    """Start audio capture and return queue"""
    self._capture_queue = await self._capture.start_async_capture()
    return self._capture_queue
```

**Usage:**
```python
queue = await vs.start_capture_stream()
while True:
    chunk = await queue.get()  # Returns bytes (AudioBytes = bytes)
```

---

## 3. What format is the captured audio?

**Answer: PCM16, 24kHz, Mono by default**

From `config/types.py:50-63`:
```python
@dataclass
class StreamConfig:
    sample_rate: int = 24000      # 24kHz standard
    channels: int = 1             # Mono
    bit_depth: int = 16           # 16-bit
    format: AudioFormat = AudioFormat.PCM16
    chunk_duration_ms: int = 100  # Default chunk size
```

From `io/capture.py:196-204`:
```python
self.stream = sd.InputStream(
    samplerate=self.config.sample_rate,
    channels=self.config.channels,
    dtype='int16',  # 16-bit signed integer
    blocksize=self.chunk_samples,
    device=self.device,
    callback=self._audio_callback,
    latency='low'
)
```

**Chunk is converted to bytes:**
```python
# io/capture.py:233
audio_bytes = audio_array.astype(np.int16).tobytes()
```

---

## 4. How does VAD callback registration work?

**Answer: Via VADetector constructor**

From `voice/vad.py:54-73`:
```python
class VADetector:
    def __init__(
        self,
        config: Optional[VADConfig] = None,
        audio_config: Optional[StreamConfig] = None,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[], None]] = None
    ):
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
```

**Callbacks are called in `process_chunk()`:**
```python
# voice/vad.py:198-205
if self.state_duration_ms >= self.config.speech_start_ms:
    self.state = VoiceState.SPEECH
    if self.on_speech_start:
        self.on_speech_start()

# voice/vad.py:229-234
if self.state_duration_ms >= self.config.speech_end_ms:
    self.state = VoiceState.SILENCE
    if self.on_speech_end:
        self.on_speech_end()
```

**Note:** Callbacks receive NO arguments. `on_speech_end` does NOT pass audio bytes (different from our earlier assumption).

---

## 5. What is the VAD state machine?

**Answer: 4-state machine**

From `voice/vad.py:18-24`:
```python
class VoiceState(Enum):
    SILENCE = "silence"
    SPEECH_STARTING = "speech_starting"
    SPEECH = "speech"
    SPEECH_ENDING = "speech_ending"
```

**State transitions:**
```
SILENCE ──(energy > threshold)──> SPEECH_STARTING
                                       │
                   (sustained for speech_start_ms)
                                       │
                                       v
SPEECH <──(energy > threshold)── SPEECH_ENDING
   │                                   │
   └──(energy < threshold)────────────>┘
                                       │
                   (sustained for speech_end_ms)
                                       │
                                       v
                                    SILENCE
```

---

## 6. How does `play_audio()` vs `queue_playback()` work?

**Answer: They're the same - both use BufferedAudioPlayer**

From `core/stream.py:478-501`:
```python
def play_audio(self, audio_data: AudioBytes) -> bool:
    """Play audio data immediately"""
    try:
        self.queue_playback(audio_data)  # Just calls queue_playback!
        return True
    except Exception as e:
        return False

def queue_playback(self, audio_data: AudioBytes):
    """Queue audio for playback through buffered player"""
    from voxstream.io.player import BufferedAudioPlayer

    if not hasattr(self, '_buffered_player'):
        self._buffered_player = BufferedAudioPlayer(...)

    self._buffered_player.play(audio_data)
```

**Note:** There's no "immediate" playback mode - both use buffered playback.

---

## 7. How does `interrupt_playback()` work?

**Answer: Calls stop() on BufferedAudioPlayer**

From `core/stream.py:508-512`:
```python
def interrupt_playback(self, force: bool = True):
    """Interrupt current audio playback"""
    if hasattr(self, '_buffered_player'):
        self._buffered_player.stop(force=force)
```

---

## 8. What is `mark_playback_complete()`?

**Answer: Signals no more audio coming**

From `core/stream.py:503-506`:
```python
def mark_playback_complete(self):
    """Mark that all audio has been received for playback"""
    if hasattr(self, '_buffered_player'):
        self._buffered_player.mark_complete()
```

---

## 9. How to configure VAD?

**Answer: Via `configure_vad()` method**

From `core/stream.py:438-444`:
```python
def configure_vad(self, vad_config: Optional[VADConfig] = None):
    """Configure Voice Activity Detection"""
    self._vad_config = vad_config
```

VADConfig from `config/types.py:203-227`:
```python
@dataclass
class VADConfig:
    type: VADType = VADType.ENERGY_BASED
    energy_threshold: float = 0.02
    zcr_threshold: float = 0.1
    speech_start_ms: int = 100      # Time before confirming speech
    speech_end_ms: int = 500        # Silence before ending speech
    pre_buffer_ms: int = 300        # Buffer before speech starts
    adaptive: bool = False
    noise_reduction: bool = False
```

---

## 10. What errors does VoxStream raise?

**Answer: VoxStreamError and AudioError**

From `exceptions.py`:
```python
class VoxStreamError(Exception):
    """Base exception for VoxStream"""
    pass

class AudioError(VoxStreamError):
    """Audio-related errors"""
    def __init__(self, message: str, error_type: AudioErrorType = None):
        ...
```

Error types from `config/types.py:341-352`:
```python
class AudioErrorType(Enum):
    FORMAT_ERROR = "format_error"
    VALIDATION_ERROR = "validation_error"
    CONVERSION_ERROR = "conversion_error"
    BUFFER_OVERFLOW = "buffer_overflow"
    BUFFER_UNDERFLOW = "buffer_underflow"
    QUALITY_ERROR = "quality_error"
    DEVICE_ERROR = "device_error"
    TIMEOUT = "timeout"
    UNSUPPORTED_OPERATION = "unsupported_operation"
```

---

## 11. How to list/select audio devices?

**Answer: Via DirectAudioCapture.list_devices() or configure_devices()**

From `io/capture.py:281-294`:
```python
@staticmethod
def list_devices():
    """List available audio devices"""
    devices = []
    for i, device in enumerate(sd.query_devices()):
        if device['max_input_channels'] > 0:
            devices.append({
                "index": i,
                "name": device['name'],
                "channels": device['max_input_channels'],
                "default": i == sd.default.device[0]
            })
    return devices
```

From `core/stream.py:432-436`:
```python
def configure_devices(self, input_device: Optional[int] = None, output_device: Optional[int] = None):
    """Configure audio input/output devices"""
    self._input_device = input_device
    self._output_device = output_device
```

---

## 12. What is `is_playing` property?

**Answer: Checks BufferedAudioPlayer state**

From `core/stream.py:532-537`:
```python
@property
def is_playing(self) -> bool:
    """Check if audio is currently playing"""
    if hasattr(self, '_buffered_player'):
        return self._buffered_player.is_actively_playing
    return False
```

---

## 13. How to cleanup?

**Answer: Use `cleanup_async()` for full cleanup**

From `core/stream.py:580-591`:
```python
async def cleanup_async(self):
    """Async cleanup for audio components"""
    if hasattr(self, '_audio_manager'):
        await self._audio_manager.cleanup()

    if hasattr(self, '_buffered_player'):
        self._buffered_player.stop(force=True)

    self.cleanup()  # Sync cleanup
```

---

## Summary: VoxStream API for AudioStreamPort

```python
from voxstream import VoxStream
from voxstream.config.types import StreamConfig, VADConfig, ProcessingMode

# Initialize
vs = VoxStream(mode=ProcessingMode.REALTIME)
vs.configure_vad(VADConfig(energy_threshold=0.02, speech_end_ms=500))
vs.configure_devices(input_device=None, output_device=None)

# Capture (returns asyncio.Queue[bytes])
queue = await vs.start_capture_stream()
async for chunk in queue:  # chunk is bytes (PCM16, 24kHz, mono)
    process(chunk)

# Playback
vs.queue_playback(audio_bytes)
vs.mark_playback_complete()
vs.interrupt_playback()

# State
vs.is_playing  # bool

# Cleanup
await vs.cleanup_async()
```

---

## Key Findings for AudioStreamPort Design

1. **Return type confirmed:** `asyncio.Queue[bytes]` - we need `async for` or `queue.get()`
2. **Audio format confirmed:** PCM16, 24kHz, mono by default (matches OpenAI)
3. **VAD callbacks:** Take NO arguments (different from our assumed design)
4. **No separate immediate playback:** `play_audio()` just calls `queue_playback()`
5. **Pre-buffer exists:** VAD has `get_pre_buffer()` to get audio before speech
