# Trace 11: AudioStreamPort (Audio I/O)

Abstract interface for real-time audio capture and playback. Enables voice applications.

---

## Entry Point

**File:** `chatforge/ports/audio_stream.py:179`
**Interface:** `AudioStreamPort` (Abstract Base Class)

**Implementations:**
- `chatforge/adapters/audio/voxstream.py` - Desktop audio via sounddevice
- `chatforge/adapters/null.py:NullAudioStreamAdapter` - No-op for testing

**Primary Methods:**
```python
async def start_capture() -> AsyncGenerator[bytes, None]
async def stop_capture() -> None
async def play(chunk: bytes) -> None
async def end_playback() -> None
async def stop_playback() -> None  # Barge-in
def set_callbacks(callbacks: AudioCallbacks) -> None
```

**Callers:**
- Voice assistant applications
- Real-time voice pipelines
- Audio processing chains

---

## Execution Path: Audio Capture Loop

```
async with VoxStreamAdapter() as audio:
    │
    ├─► __aenter__()
    │   │
    │   ├── Initialize sounddevice stream (lazy)
    │   ├── Allocate buffers
    │   └── Return self
    │
    ├─► audio.set_callbacks(AudioCallbacks(...))
    │   │
    │   └── Store callbacks for events:
    │       ├── on_speech_start: Callable[[], None]
    │       ├── on_speech_end: Callable[[bytes], None]
    │       ├── on_playback_complete: Callable[[], None]
    │       └── on_error: Callable[[Exception], None]
    │
    ├─► async for chunk in audio.start_capture():
    │   │
    │   │   [Inside start_capture]
    │   │
    │   ├─1─► Start sounddevice input stream
    │   │     └── sd.InputStream(
    │   │             samplerate=24000,
    │   │             channels=1,
    │   │             dtype='int16',
    │   │             callback=_audio_callback,
    │   │         )
    │   │
    │   ├─2─► Main capture loop
    │   │     │
    │   │     └── while capturing:
    │   │         │
    │   │         ├── chunk = await _get_from_buffer()
    │   │         │   └── Read from ring buffer (thread-safe queue)
    │   │         │
    │   │         ├── [VAD enabled?]
    │   │         │   │
    │   │         │   ├── Process chunk through VAD
    │   │         │   │
    │   │         │   ├── [Speech started]
    │   │         │   │   └── Fire on_speech_start callback
    │   │         │   │
    │   │         │   └── [Speech ended]
    │   │         │       ├── Collect pre-buffer audio
    │   │         │       └── Fire on_speech_end(pre_buffer)
    │   │         │
    │   │         └── yield chunk
    │   │
    │   └─3─► [On stop or error]
    │         ├── Stop sounddevice stream
    │         └── Generator exits
    │
    └─► __aexit__()
        │
        ├── await stop_capture()
        ├── await stop_playback()
        └── Release resources
```

---

## Execution Path: Audio Playback

```
play(chunk: bytes) -> None
    │
    ├─1─► Buffer chunk for playback
    │     └── _playback_buffer.put(chunk)
    │
    ├─2─► [If not playing, start playback stream]
    │     │
    │     └── sd.OutputStream(
    │             samplerate=24000,
    │             channels=1,
    │             dtype='int16',
    │             callback=_playback_callback,
    │         )
    │
    └─3─► Playback callback drains buffer
        │
        └── _playback_callback reads from buffer, writes to audio

end_playback() -> None
    │
    ├── Signal no more chunks coming
    ├── Wait for buffer to drain
    └── Fire on_playback_complete callback

stop_playback() -> None  # Barge-in
    │
    ├── Clear playback buffer
    ├── Stop output stream immediately
    └── (No callback - interrupted)
```

---

## Audio Format

```
Standard: PCM16, 24kHz, Mono

- Sample rate: 24000 Hz
- Bit depth: 16 bits (int16)
- Channels: 1 (mono)
- Chunk duration: 100ms (configurable)
- Bytes per chunk: 24000 * 0.1 * 2 = 4800 bytes
```

Compatible with OpenAI Realtime API requirements.

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Input stream | start_capture() | stop_capture() or __aexit__ | Audio device busy |
| Output stream | play() | stop_playback() or __aexit__ | Audio device busy |
| Audio buffers | __init__ | __aexit__ | Memory leak |
| Sound device | sounddevice library | Process exit | Device locked |

**Thread safety:**
- sounddevice uses callback threads
- Queue-based communication
- Lock-free ring buffers

---

## Error Path

```
AudioStreamError hierarchy:
    │
    ├── AudioStreamDeviceError
    │   ├── Device not found
    │   ├── Device disconnected
    │   └── Device busy
    │
    ├── AudioStreamBufferError
    │   ├── Buffer overflow (capture)
    │   └── Buffer underflow (playback)
    │
    └── AudioStreamNotInitializedError
        └── Used before __aenter__

Error handling:
    │
    ├── Device error during capture
    │   ├── Fire on_error callback
    │   └── Generator raises exception
    │
    └── Device error during playback
        ├── Fire on_error callback
        └── Silently stop (don't crash)
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Capture latency | 5-20ms | From mic to yield |
| Playback latency | 10-50ms | From play() to speaker |
| Buffer size | ~500ms | Configurable |
| Memory | ~50KB | Buffers |
| CPU | Low | Just copying bytes |

**Latency factors:**
1. Chunk duration (100ms default)
2. OS audio buffer
3. sounddevice callback frequency
4. Queue waiting time

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Microphone access | OS | start_capture() |
| Speaker output | OS | play() |
| Callback: on_speech_start | Caller | VAD detects speech |
| Callback: on_speech_end | Caller | VAD detects silence |
| Callback: on_playback_complete | Caller | Buffer drained |
| Callback: on_error | Caller | Device error |

---

## Why This Design

**Async generator for capture:**
- Natural iteration pattern
- Backpressure via queue
- Clean resource cleanup

**Callback for events:**
- Non-blocking notifications
- Decouple detection from consumption
- Enable UI updates

**Buffer-based playback:**
- Smooth audio output
- Handle network jitter
- Simple API (just call play())

**PCM16 24kHz standard:**
- Matches OpenAI Realtime
- Good quality/size balance
- Simple format

---

## What Feels Incomplete

1. **No echo cancellation:**
   - Mic picks up speaker output
   - No AEC built in
   - Must use hardware or external

2. **No noise suppression:**
   - Background noise passes through
   - No built-in filter
   - Relies on API's VAD

3. **No audio level monitoring:**
   - No VU meter
   - No clipping detection
   - No auto-gain

4. **No device hot-plug:**
   - Device disconnect = error
   - No automatic recovery
   - Must restart capture

5. **No format conversion:**
   - Only PCM16 24kHz
   - Other formats need external conversion
   - Should offer resampling

---

## What Feels Vulnerable

1. **Device enumeration timing:**
   - list_input_devices() snapshots
   - Device may disconnect after
   - No validation at capture start

2. **Buffer overflow policy:**
   - What happens when buffer full?
   - Docs don't specify
   - Could drop audio or block

3. **Callback exceptions:**
   - If callback throws?
   - Likely crashes capture
   - Should catch and log

4. **No permission handling:**
   - Microphone permission is OS-level
   - Just fails with device error
   - Should check permissions first

5. **Thread/async mixing:**
   - sounddevice callbacks are threaded
   - asyncio operations in callbacks?
   - Need careful synchronization

---

## What Feels Bad Design

1. **VADConfig in two places:**
   - audio_stream.VADConfig
   - vad.VADPortConfig
   - Naming conflict resolved with alias
   - Confusing

2. **Callbacks set separately:**
   - set_callbacks() after construction
   - Could miss early events
   - Should be constructor param

3. **start_capture is async generator:**
   - Can't check state without iterating
   - No is_capturing property shown
   - State inspection awkward

4. **stop_playback vs end_playback:**
   - Similar names, different semantics
   - stop = cancel, end = finish
   - Confusing which to use

5. **No volume control:**
   - Fixed gain
   - Can't adjust in software
   - Common need unaddressed
