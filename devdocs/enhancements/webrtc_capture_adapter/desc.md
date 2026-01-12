# WebRTCCaptureAdapter

## Overview

Adapter that implements `AudioCapturePort` to receive audio from browser clients via WebRTC. Works with `WebRTCSignalingServer` (infrastructure) which handles connection establishment.

## Position in Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AudioCapturePort                              │
│                      (Interface)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ implements
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────┴───────┐  ┌──────────┴────────┐  ┌────────┴────────┐
│ SoundDevice   │  │   WebRTCCapture   │  │   FileCapture   │
│ Adapter       │  │   Adapter         │  │   Adapter       │
│ (microphone)  │  │   (browser)       │  │   (testing)     │
└───────────────┘  └───────────────────┘  └─────────────────┘
```

## Why a Separate Adapter?

| Concern | SoundDeviceCaptureAdapter | WebRTCCaptureAdapter |
|---------|---------------------------|----------------------|
| Audio source | Local microphone | Remote browser |
| Transport | OS audio driver | SRTP over UDP |
| Format | PCM (configurable) | Opus → PCM |
| Lifecycle | Start/stop on demand | Tied to WebRTC session |
| Latency source | Buffer size | Network + jitter buffer |

Same interface (`AudioCapturePort`), completely different implementation.

## Interface Compliance

```python
class WebRTCCaptureAdapter(AudioCapturePort):
    """Capture audio from a WebRTC peer connection."""

    @property
    def state(self) -> CaptureState: ...

    @property
    def is_capturing(self) -> bool: ...

    async def start(self) -> asyncio.Queue[bytes]: ...

    def stop(self) -> None: ...

    async def stop_and_drain(self) -> None: ...

    def get_metrics(self) -> CaptureMetrics: ...

    def set_callbacks(
        self,
        on_started: Callable[[], None] = None,
        on_stopped: Callable[[], None] = None,
        on_error: Callable[[Exception], None] = None,
    ) -> None: ...

    def cleanup(self) -> None: ...
```

## Constructor

```python
class WebRTCCaptureAdapter(AudioCapturePort):
    def __init__(
        self,
        audio_track: MediaStreamTrack,
        session_id: str,
        config: AudioCaptureConfig = None,
        resample_to: int = 24000,  # OpenAI Realtime API expects 24kHz
    ):
        """
        Initialize WebRTC audio capture.

        Args:
            audio_track: The audio track from RTCPeerConnection.
                Obtained via peer_connection.getReceivers()[0].track

            session_id: Unique identifier for this WebRTC session.
                Used for logging and metrics correlation.

            config: Audio capture configuration.
                Note: sample_rate is determined by WebRTC negotiation,
                typically 48kHz for Opus. Use resample_to to convert.

            resample_to: Target sample rate for output.
                WebRTC typically delivers 48kHz Opus.
                Set to 24000 for OpenAI Realtime API compatibility.
                Set to None to preserve original rate.
        """
```

## Audio Flow

```
Browser Microphone
        │
        ▼
┌─────────────────┐
│ getUserMedia()  │  48kHz, Opus-ready
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RTCPeerConn     │  Opus encoding, 20ms frames
│ (browser)       │
└────────┬────────┘
         │ SRTP/UDP
         ▼
┌─────────────────┐
│ RTCPeerConn     │  Opus decoding
│ (aiortc)        │
└────────┬────────┘
         │ AudioFrame (48kHz, float32)
         ▼
┌─────────────────────────────────────────┐
│         WebRTCCaptureAdapter            │
│  ┌─────────────────────────────────┐    │
│  │ 1. Receive AudioFrame           │    │
│  │ 2. Convert float32 → int16      │    │
│  │ 3. Resample 48kHz → 24kHz       │    │
│  │ 4. Put bytes in queue           │    │
│  └─────────────────────────────────┘    │
└────────────────────┬────────────────────┘
                     │ asyncio.Queue[bytes]
                     ▼
              VAD / AI Pipeline
```

## Implementation Details

### 1. Track Event Handling

```python
async def start(self) -> asyncio.Queue[bytes]:
    """Start receiving audio from the WebRTC track."""
    if self._state != CaptureState.IDLE:
        raise AudioCaptureError("Already capturing")

    self._state = CaptureState.STARTING
    self._audio_queue = asyncio.Queue(maxsize=self._config.queue_size)

    # Subscribe to track frames
    @self._audio_track.on("frame")
    async def on_frame(frame: AudioFrame):
        await self._process_frame(frame)

    @self._audio_track.on("ended")
    def on_ended():
        self._handle_track_ended()

    self._state = CaptureState.CAPTURING
    self._fire_started_callback()

    return self._audio_queue
```

### 2. Frame Processing

```python
async def _process_frame(self, frame: AudioFrame) -> None:
    """Process incoming WebRTC audio frame."""
    try:
        # Convert to numpy array
        # aiortc AudioFrame contains s16 samples in .planes[0]
        samples = np.frombuffer(frame.planes[0], dtype=np.int16)

        # Resample if needed (48kHz → 24kHz)
        if self._resample_to and frame.sample_rate != self._resample_to:
            samples = self._resample(samples, frame.sample_rate, self._resample_to)

        # Convert to bytes
        audio_bytes = samples.tobytes()

        # Put in queue (non-blocking with timeout)
        try:
            self._audio_queue.put_nowait(audio_bytes)
            self._metrics.chunks_captured += 1
        except asyncio.QueueFull:
            self._metrics.chunks_dropped += 1
            self._metrics.buffer_overruns += 1

    except Exception as e:
        self._fire_error_callback(e)
```

### 3. Resampling

```python
def _resample(
    self,
    samples: np.ndarray,
    from_rate: int,
    to_rate: int,
) -> np.ndarray:
    """Resample audio using linear interpolation or scipy."""
    if from_rate == to_rate:
        return samples

    # Simple case: 48kHz → 24kHz (2:1 decimation)
    if from_rate == 48000 and to_rate == 24000:
        # Take every other sample (fast, good enough for voice)
        return samples[::2]

    # General case: use scipy.signal.resample
    num_samples = int(len(samples) * to_rate / from_rate)
    return scipy.signal.resample(samples, num_samples).astype(np.int16)
```

### 4. Session Lifecycle

```python
def _handle_track_ended(self) -> None:
    """Handle WebRTC track ending (browser disconnected)."""
    if self._state == CaptureState.CAPTURING:
        self._state = CaptureState.IDLE
        self._fire_stopped_callback()

        # Signal end-of-stream to consumers
        try:
            self._audio_queue.put_nowait(None)  # Sentinel
        except asyncio.QueueFull:
            pass

def stop(self) -> None:
    """Stop capturing (sync, for signal handlers)."""
    if self._state != CaptureState.CAPTURING:
        return

    self._state = CaptureState.IDLE

    # Detach from track
    self._audio_track.stop()

    self._fire_stopped_callback()
```

## Metrics

```python
@dataclass
class CaptureMetrics:
    chunks_captured: int = 0
    chunks_dropped: int = 0
    buffer_overruns: int = 0
    total_bytes: int = 0
    start_time: Optional[float] = None

    # WebRTC-specific
    packets_received: int = 0
    packets_lost: int = 0
    jitter_ms: float = 0.0
    round_trip_time_ms: float = 0.0

    @property
    def packet_loss_rate(self) -> float:
        total = self.packets_received + self.packets_lost
        return self.packets_lost / total if total > 0 else 0.0
```

WebRTC stats can be obtained from the peer connection:

```python
async def _update_webrtc_stats(self) -> None:
    """Fetch WebRTC stats for metrics."""
    stats = await self._peer_connection.getStats()

    for report in stats.values():
        if report.type == "inbound-rtp" and report.kind == "audio":
            self._metrics.packets_received = report.packetsReceived
            self._metrics.packets_lost = report.packetsLost
            self._metrics.jitter_ms = report.jitter * 1000
```

## Error Handling

### Connection Errors

```python
class WebRTCCaptureError(AudioCaptureError):
    """Base error for WebRTC capture issues."""
    pass

class TrackEndedError(WebRTCCaptureError):
    """Remote track ended unexpectedly."""
    pass

class ConnectionLostError(WebRTCCaptureError):
    """WebRTC connection was lost."""
    pass

class CodecError(WebRTCCaptureError):
    """Failed to decode audio codec."""
    pass
```

### Graceful Degradation

```python
async def _process_frame(self, frame: AudioFrame) -> None:
    try:
        # ... normal processing
    except CodecError as e:
        # Log but don't crash - skip corrupted frame
        self.logger.warning(f"Skipping corrupted frame: {e}")
        self._metrics.frames_skipped += 1
    except Exception as e:
        # Unexpected error - notify via callback
        self._fire_error_callback(e)
```

## Integration Example

```python
from chatforge.infrastructure.webrtc import WebRTCSignalingServer
from chatforge.adapters.audio_capture import WebRTCCaptureAdapter
from chatforge.adapters.vad import EnergyVADAdapter
from chatforge.ports.audio_capture import AudioCaptureConfig

# Infrastructure: signaling server
signaling = WebRTCSignalingServer(port=8765)

# Handler for new WebRTC sessions
async def handle_session(session_id: str, peer_connection: RTCPeerConnection):
    """Called when browser establishes WebRTC connection."""

    # Get audio track from peer connection
    audio_track = None
    for receiver in peer_connection.getReceivers():
        if receiver.track.kind == "audio":
            audio_track = receiver.track
            break

    if not audio_track:
        raise ValueError("No audio track in peer connection")

    # Create adapter (implements AudioCapturePort)
    capture = WebRTCCaptureAdapter(
        audio_track=audio_track,
        session_id=session_id,
        config=AudioCaptureConfig(
            sample_rate=48000,  # WebRTC native
            channels=1,
            chunk_duration_ms=20,  # Opus frame size
        ),
        resample_to=24000,  # For OpenAI Realtime API
    )

    # Set up callbacks
    capture.set_callbacks(
        on_started=lambda: print(f"Session {session_id}: capture started"),
        on_stopped=lambda: print(f"Session {session_id}: capture stopped"),
        on_error=lambda e: print(f"Session {session_id}: error {e}"),
    )

    # Start capture - same interface as SoundDeviceCaptureAdapter!
    audio_queue = await capture.start()

    # Process audio with VAD
    vad = EnergyVADAdapter()

    while capture.is_capturing:
        try:
            chunk = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
            if chunk is None:  # End sentinel
                break

            result = vad.process_chunk(chunk)
            if result.is_speaking:
                await send_to_ai(session_id, chunk)

        except asyncio.TimeoutError:
            continue

    # Cleanup
    capture.cleanup()
    print(f"Session {session_id}: ended")

# Register handler and start
signaling.on_session_created(handle_session)
await signaling.start()
```

## Testing Strategy

### Unit Tests with Mock Track

```python
class MockAudioTrack:
    """Mock WebRTC audio track for testing."""

    def __init__(self):
        self._frame_handlers = []
        self._ended_handlers = []

    def on(self, event: str):
        def decorator(handler):
            if event == "frame":
                self._frame_handlers.append(handler)
            elif event == "ended":
                self._ended_handlers.append(handler)
            return handler
        return decorator

    async def emit_frame(self, samples: np.ndarray, sample_rate: int = 48000):
        """Emit a test audio frame."""
        frame = MockAudioFrame(samples, sample_rate)
        for handler in self._frame_handlers:
            await handler(frame)

    def stop(self):
        for handler in self._ended_handlers:
            handler()


@pytest.mark.asyncio
async def test_capture_receives_frames():
    track = MockAudioTrack()
    adapter = WebRTCCaptureAdapter(track, session_id="test")

    queue = await adapter.start()

    # Emit test frame
    samples = np.sin(np.linspace(0, 2*np.pi, 960)).astype(np.float32)
    await track.emit_frame(samples)

    # Verify received
    chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert len(chunk) > 0
    assert adapter.get_metrics().chunks_captured == 1
```

### Integration Tests with aiortc

```python
@pytest.mark.asyncio
async def test_full_webrtc_capture():
    """Test with real aiortc peer connections."""

    # Create two peer connections (simulating browser + server)
    browser_pc = RTCPeerConnection()
    server_pc = RTCPeerConnection()

    # Add audio track to "browser"
    audio_source = AudioStreamTrack()  # Generates test audio
    browser_pc.addTrack(audio_source)

    # ICE exchange (simplified for test)
    offer = await browser_pc.createOffer()
    await browser_pc.setLocalDescription(offer)
    await server_pc.setRemoteDescription(offer)

    answer = await server_pc.createAnswer()
    await server_pc.setLocalDescription(answer)
    await browser_pc.setRemoteDescription(answer)

    # Get track on server side
    await asyncio.sleep(0.5)  # Wait for connection
    audio_track = server_pc.getReceivers()[0].track

    # Test our adapter
    adapter = WebRTCCaptureAdapter(audio_track, "integration-test")
    queue = await adapter.start()

    # Collect some audio
    chunks = []
    for _ in range(10):
        chunk = await asyncio.wait_for(queue.get(), timeout=2.0)
        chunks.append(chunk)

    assert len(chunks) == 10
    assert all(len(c) > 0 for c in chunks)

    # Cleanup
    adapter.stop()
    await browser_pc.close()
    await server_pc.close()
```

## Dependencies

```python
# Required
aiortc >= 1.6.0      # WebRTC for Python
numpy >= 1.24.0      # Audio processing

# Optional (for high-quality resampling)
scipy >= 1.10.0      # signal.resample
# or
samplerate >= 0.1.0  # libsamplerate bindings (best quality)
```

## Configuration Options

```python
@dataclass
class WebRTCCaptureConfig(AudioCaptureConfig):
    """Extended config for WebRTC capture."""

    # Base AudioCaptureConfig fields
    sample_rate: int = 48000        # WebRTC default (Opus)
    channels: int = 1
    chunk_duration_ms: int = 20     # Opus frame size
    queue_size: int = 50

    # WebRTC-specific
    resample_to: Optional[int] = 24000    # Target sample rate
    enable_dtx: bool = True               # Discontinuous transmission
    jitter_buffer_ms: int = 50            # Jitter buffer size
    stats_interval_ms: int = 1000         # How often to fetch RTCStats
```

## File Structure

```
chatforge/adapters/audio_capture/
├── __init__.py
├── sounddevice_adapter.py    # Local microphone
├── file_adapter.py           # WAV file (testing)
├── null_adapter.py           # Test signals
└── webrtc_adapter.py         # Browser audio (NEW)

tests/adapters/audio_capture/
├── ...
└── test_webrtc_adapter.py    # Unit + integration tests
```

## Related Documents

- `webrtc_signaling_server/desc.md` - Infrastructure component
- `audiocaptureport/desc.md` - Port interface specification
- `vadport/desc.md` - VAD integration
