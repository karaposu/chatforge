# WebRTCCaptureAdapter - Critical Analysis

## Executive Summary

**The step-by-step plan contains a FUNDAMENTAL API ASSUMPTION ERROR.** The plan assumes aiortc uses an event-based pattern (`@track.on("frame")`), but aiortc actually uses a **pull-based `recv()` coroutine pattern**. This invalidates Steps 3-6 and requires significant redesign.

Additionally, there are issues with audio format handling, resampling approach, and the mock design.

---

## Critical Flaw #1: Wrong aiortc API Model

### The Assumption (WRONG)

```python
# Plan assumes this event-based pattern:
@track.on("frame")
async def on_frame(frame):
    await self._process_frame(frame)

@track.on("ended")
def on_ended():
    self._handle_track_ended()
```

### The Reality

According to [aiortc documentation](https://aiortc.readthedocs.io/en/latest/api.html) and [source code](https://github.com/aiortc/aiortc/blob/main/src/aiortc/mediastreams.py):

```python
# aiortc uses a pull-based recv() pattern:
class MediaStreamTrack:
    async def recv(self) -> Union[AudioFrame, VideoFrame]:
        """Receive the next frame."""
        ...

# You must LOOP and call recv():
async def consume_track(track):
    while True:
        try:
            frame = await track.recv()
            process(frame)
        except MediaStreamError:
            break  # Track ended
```

### Impact

- **Steps 4-6 are wrong** - The `start()` implementation is completely incorrect
- **MockAudioTrack is wrong** - It simulates an API that doesn't exist
- **The adapter needs a consumer task** - Must spawn an async task that loops on `recv()`

### Correct Approach

```python
async def start(self) -> asyncio.Queue[bytes]:
    # ...

    # Spawn consumer task that loops on recv()
    self._consumer_task = asyncio.create_task(self._consume_track())

    return self._audio_queue

async def _consume_track(self) -> None:
    """Consume frames from track in a loop."""
    try:
        while self._state == CaptureState.CAPTURING:
            try:
                frame = await self._track.recv()
                await self._process_frame(frame)
            except MediaStreamError:
                # Track ended
                break
    finally:
        self._handle_track_ended()
```

---

## Critical Flaw #2: Wrong AudioFrame Format Assumption

### The Assumption (WRONG)

```python
# Plan assumes int16:
audio_bytes = bytes(frame.planes[0])
samples = np.frombuffer(audio_bytes, dtype=np.int16)
```

### The Reality

According to [PyAV documentation](https://pyav.org/docs/stable/api/audio.html), AudioFrame format varies:

| Format | Description | dtype | Planes |
|--------|-------------|-------|--------|
| `s16` | Signed 16-bit int, packed | `np.int16` | 1 |
| `s32` | Signed 32-bit int, packed | `np.int32` | 1 |
| `flt` | Float 32-bit, packed | `np.float32` | 1 |
| `fltp` | Float 32-bit, planar | `np.float32` | N (per channel) |
| `dbl` | Float 64-bit, packed | `np.float64` | 1 |

**WebRTC typically uses `s16` or `fltp` depending on codec/decoder configuration.**

### Impact

- Code will crash or produce garbage if format isn't `s16`
- Planar formats (`fltp`) have separate planes per channel - can't just read `planes[0]`

### Correct Approach

```python
def _process_frame(self, frame) -> None:
    # Check format and convert appropriately
    if frame.format.name == 's16':
        samples = np.frombuffer(bytes(frame.planes[0]), dtype=np.int16)
    elif frame.format.name == 'flt':
        samples = np.frombuffer(bytes(frame.planes[0]), dtype=np.float32)
        samples = (samples * 32767).astype(np.int16)
    elif frame.format.name == 'fltp':
        # Planar: each channel in separate plane
        channels = [np.frombuffer(bytes(p), dtype=np.float32) for p in frame.planes]
        samples = np.stack(channels, axis=-1)  # Interleave
        samples = (samples * 32767).astype(np.int16).flatten()
    else:
        raise CodecError(f"Unsupported format: {frame.format.name}")
```

**Or better: use PyAV's reformat() to normalize:**

```python
def _process_frame(self, frame) -> None:
    # Reformat to consistent s16 mono
    frame = frame.reformat(format='s16', layout='mono')
    samples = np.frombuffer(bytes(frame.planes[0]), dtype=np.int16)
```

---

## Critical Flaw #3: Resampling Causes Aliasing

### The Assumption (WRONG)

```python
# Simple decimation:
if from_rate == 48000 and to_rate == 24000:
    return samples[::2]  # Take every other sample
```

### The Reality

**Decimation without anti-aliasing filter causes aliasing artifacts.**

When you have a 48kHz signal with content up to 24kHz (Nyquist), and you decimate to 24kHz, frequencies above 12kHz will alias back into the audible range as distortion.

For voice (fundamentals up to ~4kHz, harmonics up to ~8kHz), this might be "acceptable" but is technically wrong.

### Correct Approach

```python
from scipy import signal

def _resample(self, samples, from_rate, to_rate):
    if from_rate == to_rate:
        return samples

    # Use scipy.signal.resample_poly for proper anti-aliasing
    # It applies a low-pass filter before decimation
    gcd = np.gcd(from_rate, to_rate)
    up = to_rate // gcd
    down = from_rate // gcd

    return signal.resample_poly(samples, up, down).astype(np.int16)
```

Or use `samplerate` library (libsamplerate) for high-quality resampling:

```python
import samplerate

def _resample(self, samples, from_rate, to_rate):
    ratio = to_rate / from_rate
    return samplerate.resample(samples.astype(np.float32), ratio, 'sinc_best').astype(np.int16)
```

### Mitigation

For voice-only applications, simple decimation is "good enough" but should be documented as a known trade-off. Add a `resample_quality` config option:

```python
resample_quality: str = "fast"  # "fast" (decimation) or "high" (scipy)
```

---

## Flaw #4: MockAudioTrack Doesn't Match Real API

### The Problem

The mock uses a non-existent event-based API:

```python
# Mock (WRONG):
class MockAudioTrack:
    def on(self, event: str):  # This doesn't exist in aiortc
        ...

    async def emit_frame(self, frame):  # This doesn't exist
        ...
```

### Correct Mock

```python
class MockAudioTrack:
    """Mock that matches aiortc's recv() pattern."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._stopped = False
        self.kind = "audio"
        self.readyState = "live"

    async def recv(self) -> MockAudioFrame:
        """Match aiortc's recv() signature."""
        if self._stopped:
            raise MediaStreamError("Track ended")

        frame = await self._queue.get()
        if frame is None:
            self._stopped = True
            raise MediaStreamError("Track ended")

        return frame

    # Test helper methods
    async def feed_frame(self, frame: MockAudioFrame) -> None:
        """Feed a frame (for tests)."""
        await self._queue.put(frame)

    def stop(self) -> None:
        """End the track."""
        self._queue.put_nowait(None)
        self.readyState = "ended"
```

---

## Flaw #5: Missing Consumer Task Lifecycle Management

### The Problem

With the `recv()` pattern, we need a background task that continuously consumes frames. The plan doesn't address:

1. **Task creation** - When/how to spawn the consumer
2. **Task cancellation** - How to cleanly stop the consumer
3. **Exception handling** - What happens if consumer crashes
4. **Backpressure** - What if consumer can't keep up

### Correct Approach

```python
class WebRTCCaptureAdapter:
    def __init__(self, ...):
        self._consumer_task: Optional[asyncio.Task] = None

    async def start(self) -> asyncio.Queue[bytes]:
        # ...
        self._consumer_task = asyncio.create_task(
            self._consume_track(),
            name=f"webrtc-consumer-{self._session_id}"
        )
        # Don't await - let it run in background
        return self._audio_queue

    async def _consume_track(self) -> None:
        try:
            while self._state == CaptureState.CAPTURING:
                frame = await self._track.recv()
                await self._process_frame(frame)
        except MediaStreamError:
            pass  # Normal end
        except asyncio.CancelledError:
            pass  # Cancelled by stop()
        except Exception as e:
            self._fire_error_callback(e)
        finally:
            self._handle_track_ended()

    def stop(self) -> None:
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
        # ...

    async def stop_and_drain(self) -> None:
        self.stop()
        if self._consumer_task:
            try:
                await asyncio.wait_for(self._consumer_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
```

---

## Flaw #6: track.stop() Ownership Confusion

### The Problem

The plan calls `self._track.stop()` in the adapter's `stop()` method:

```python
def stop(self) -> None:
    # ...
    self._track.stop()  # Is this correct?
```

### The Reality

- The track belongs to the `RTCPeerConnection`, not the adapter
- Stopping the track may affect other consumers
- The connection might want to keep the track for other purposes

### Correct Approach

**Don't stop the track - just stop consuming it:**

```python
def stop(self) -> None:
    """Stop consuming the track (doesn't stop the track itself)."""
    if self._state != CaptureState.CAPTURING:
        return

    self._state = CaptureState.IDLE

    # Cancel consumer task (will cause recv() to stop)
    if self._consumer_task:
        self._consumer_task.cancel()

    # Send sentinel
    # ...
```

The connection owner should decide when to close tracks.

---

## Flaw #7: No Handling of RTCPeerConnection State

### The Problem

The adapter only watches the track, but the connection can close independently:

- `RTCPeerConnection.connectionState` can become `"failed"`, `"closed"`
- This would cause `recv()` to fail in unexpected ways

### Correct Approach

Either:
1. **Accept peer_connection in constructor** and watch its state
2. **Catch connection-related errors** in the consumer loop
3. **Document the limitation** - adapter doesn't watch connection state

```python
async def _consume_track(self) -> None:
    try:
        while self._state == CaptureState.CAPTURING:
            frame = await self._track.recv()
            # ...
    except MediaStreamError as e:
        # Includes connection failures
        self._logger.info(f"Track/connection ended: {e}")
    except Exception as e:
        self._logger.error(f"Unexpected error: {e}")
        self._fire_error_callback(e)
```

---

## Flaw #8: Integration Test Creates Incomplete Connection

### The Problem

The integration test does SDP exchange but skips ICE:

```python
# Test code:
offer = await browser_pc.createOffer()
await browser_pc.setLocalDescription(offer)
await server_pc.setRemoteDescription(offer)
# ... missing ICE candidate exchange
await asyncio.sleep(0.5)  # "Wait for connection" - unreliable
```

### The Reality

Without proper ICE exchange, the connection may not actually establish. The `sleep(0.5)` is a race condition.

### Correct Approach

```python
async def test_full_webrtc_connection():
    browser_pc = RTCPeerConnection()
    server_pc = RTCPeerConnection()

    # ICE candidate exchange
    @browser_pc.on("icecandidate")
    async def on_browser_ice(candidate):
        if candidate:
            await server_pc.addIceCandidate(candidate)

    @server_pc.on("icecandidate")
    async def on_server_ice(candidate):
        if candidate:
            await browser_pc.addIceCandidate(candidate)

    # Wait for connection to establish
    connected = asyncio.Event()

    @server_pc.on("connectionstatechange")
    def on_state():
        if server_pc.connectionState == "connected":
            connected.set()

    # SDP exchange
    # ...

    # Wait for actual connection (not arbitrary sleep)
    await asyncio.wait_for(connected.wait(), timeout=5.0)
```

---

## Flaw #9: CaptureMetrics Missing WebRTC-Specific Fields

### The Problem

The plan uses the base `CaptureMetrics` but mentions WebRTC-specific metrics:

```python
# In desc.md:
packets_received: int = 0
packets_lost: int = 0
jitter_ms: float = 0.0
```

But the implementation doesn't actually fetch these from RTCStats.

### Correct Approach

Either:
1. **Create WebRTCCaptureMetrics** extending base class
2. **Periodically fetch RTCStats** and update metrics
3. **Or remove the claim** - don't promise features we don't implement

```python
@dataclass
class WebRTCCaptureMetrics(CaptureMetrics):
    """Extended metrics with WebRTC stats."""
    packets_received: int = 0
    packets_lost: int = 0
    jitter_ms: float = 0.0
    # etc.

async def _update_stats_periodically(self) -> None:
    """Background task to fetch RTCStats."""
    while self._state == CaptureState.CAPTURING:
        await asyncio.sleep(self._config.stats_interval_ms / 1000)
        # Need peer_connection reference to call getStats()
        # But we only have track - design issue!
```

**Problem:** We'd need `RTCPeerConnection` to get stats, but constructor only takes track.

---

## Flaw #10: Missing Error - MediaStreamError Import

### The Problem

The plan references `MediaStreamError` but doesn't import it:

```python
except MediaStreamError:
    break  # Track ended
```

### Correct Import

```python
from aiortc.mediastreams import MediaStreamError
```

Or define our own if we want to avoid direct aiortc import in the adapter:

```python
# In exceptions
class TrackEndedError(WebRTCCaptureError):
    """Track ended (wraps MediaStreamError)."""
    pass
```

---

## Summary of Required Changes

| Step | Issue | Severity | Fix |
|------|-------|----------|-----|
| 3 | MockAudioTrack uses wrong API | **CRITICAL** | Redesign to use recv() pattern |
| 5 | start() uses non-existent events | **CRITICAL** | Use consumer task with recv() loop |
| 6 | Assumes s16 format | **HIGH** | Handle multiple formats or reformat() |
| 7 | Decimation causes aliasing | **MEDIUM** | Use proper resampling or document trade-off |
| 8 | track.stop() ownership | **MEDIUM** | Don't stop track, just stop consuming |
| 11 | Integration test race condition | **MEDIUM** | Proper ICE exchange and state waiting |
| 9 | WebRTC metrics not implemented | **LOW** | Either implement or remove from docs |

---

## Revised High-Level Design

```python
class WebRTCCaptureAdapter(AudioCapturePort):
    def __init__(
        self,
        audio_track: MediaStreamTrack,  # From aiortc
        session_id: str,
        config: WebRTCCaptureConfig = None,
    ):
        self._track = audio_track
        self._consumer_task: Optional[asyncio.Task] = None
        # ...

    async def start(self) -> asyncio.Queue[bytes]:
        # Create queue
        self._audio_queue = asyncio.Queue(maxsize=self._config.queue_size)

        # Spawn consumer task
        self._consumer_task = asyncio.create_task(self._consume_track())

        self._state = CaptureState.CAPTURING
        return self._audio_queue

    async def _consume_track(self) -> None:
        """Pull frames from track in a loop."""
        try:
            while self._state == CaptureState.CAPTURING:
                frame = await self._track.recv()  # This is the real API
                self._process_frame(frame)
        except MediaStreamError:
            pass  # Normal termination
        except asyncio.CancelledError:
            pass
        finally:
            self._handle_track_ended()

    def _process_frame(self, frame) -> None:
        # Normalize to s16 mono
        frame = frame.reformat(format='s16', layout='mono')
        samples = np.frombuffer(bytes(frame.planes[0]), dtype=np.int16)

        # Resample if needed
        if self._config.resample_to:
            samples = self._resample(samples, frame.sample_rate, self._config.resample_to)

        # Queue
        try:
            self._audio_queue.put_nowait(samples.tobytes())
        except asyncio.QueueFull:
            pass  # Drop

    def stop(self) -> None:
        self._state = CaptureState.IDLE
        if self._consumer_task:
            self._consumer_task.cancel()
```

---

## Sources

- [aiortc API Reference](https://aiortc.readthedocs.io/en/latest/api.html)
- [aiortc mediastreams.py source](https://github.com/aiortc/aiortc/blob/main/src/aiortc/mediastreams.py)
- [PyAV Audio Documentation](https://pyav.org/docs/stable/api/audio.html)
- [PyAV AudioFrame tests](https://github.com/PyAV-Org/PyAV/blob/main/tests/test_audioframe.py)
