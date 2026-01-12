# WebRTCCaptureAdapter - Step by Step Implementation Plan

## Executive Summary

Build an adapter that captures audio from browser clients via WebRTC, implementing the existing `AudioCapturePort` interface. The implementation is split into phases to allow testing without the full WebRTC stack.

---

## Prerequisites

### Dependencies to Install

```bash
pip install aiortc numpy
# Optional for high-quality resampling:
pip install scipy
```

### Files to Read First

```
chatforge/ports/audio_capture.py           # Interface we're implementing
chatforge/adapters/audio_capture/__init__.py  # Export patterns
chatforge/adapters/audio_capture/sounddevice_adapter.py  # Reference implementation
```

### Key aiortc Concepts

```python
from aiortc import RTCPeerConnection, MediaStreamTrack
from aiortc.mediastreams import AudioStreamTrack

# Track events (decorator pattern)
@track.on("frame")
async def on_frame(frame):
    # frame.planes[0] contains audio bytes
    # frame.sample_rate, frame.samples, etc.

@track.on("ended")
def on_ended():
    # Track was closed
```

---

## Phase 1: Foundation (No aiortc Runtime Dependency)

### Step 1: Create Exception Classes

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py`

```python
"""
WebRTCCaptureAdapter - Capture audio from browser via WebRTC.
"""

from chatforge.ports.audio_capture import AudioCaptureError

__all__ = [
    "WebRTCCaptureAdapter",
    "WebRTCCaptureError",
    "TrackEndedError",
    "ConnectionLostError",
    "CodecError",
]


class WebRTCCaptureError(AudioCaptureError):
    """Base error for WebRTC capture issues."""
    pass


class TrackEndedError(WebRTCCaptureError):
    """Remote audio track ended unexpectedly."""
    pass


class ConnectionLostError(WebRTCCaptureError):
    """WebRTC connection was lost."""
    pass


class CodecError(WebRTCCaptureError):
    """Failed to decode audio codec."""
    pass
```

**Validation:** Exceptions can be imported and raised.

---

### Step 2: Create WebRTCCaptureConfig

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append)

```python
from dataclasses import dataclass, field
from typing import Optional

from chatforge.ports.audio_capture import AudioCaptureConfig


@dataclass
class WebRTCCaptureConfig(AudioCaptureConfig):
    """Extended configuration for WebRTC capture."""

    # Base fields (inherited defaults)
    sample_rate: int = 48000        # WebRTC/Opus default
    channels: int = 1
    chunk_duration_ms: int = 20     # Opus frame size
    queue_size: int = 50

    # WebRTC-specific
    resample_to: Optional[int] = 24000
    """Target sample rate. Set to None to preserve original."""

    stats_interval_ms: int = 1000
    """How often to fetch RTCStats for metrics."""
```

**Validation:** Config can be instantiated, defaults are sensible.

---

### Step 3: Create Test Fixtures (Mock Track)

**File:** `tests/adapters/audio_capture/webrtc_fixtures.py`

```python
"""
Mock fixtures for WebRTC adapter testing.

Allows testing without aiortc dependency.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np


@dataclass
class MockAudioFrame:
    """Mock aiortc AudioFrame for testing."""

    planes: List[bytes]
    sample_rate: int = 48000
    samples: int = 960  # 20ms at 48kHz

    @classmethod
    def from_samples(
        cls,
        samples: np.ndarray,
        sample_rate: int = 48000,
    ) -> "MockAudioFrame":
        """Create frame from numpy samples (int16)."""
        audio_bytes = samples.astype(np.int16).tobytes()
        return cls(
            planes=[audio_bytes],
            sample_rate=sample_rate,
            samples=len(samples),
        )

    @classmethod
    def silence(cls, duration_ms: int = 20, sample_rate: int = 48000) -> "MockAudioFrame":
        """Create silent frame."""
        num_samples = int(sample_rate * duration_ms / 1000)
        samples = np.zeros(num_samples, dtype=np.int16)
        return cls.from_samples(samples, sample_rate)

    @classmethod
    def sine(
        cls,
        duration_ms: int = 20,
        frequency: int = 440,
        amplitude: float = 0.5,
        sample_rate: int = 48000,
    ) -> "MockAudioFrame":
        """Create sine wave frame."""
        num_samples = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, num_samples, endpoint=False)
        samples = (np.sin(2 * np.pi * frequency * t) * amplitude * 32767).astype(np.int16)
        return cls.from_samples(samples, sample_rate)


class MockAudioTrack:
    """
    Mock WebRTC audio track for testing.

    Simulates aiortc's MediaStreamTrack event model.
    """

    def __init__(self):
        self._frame_handlers: List[Callable] = []
        self._ended_handlers: List[Callable] = []
        self._stopped = False
        self.kind = "audio"

    def on(self, event: str):
        """Decorator to register event handlers (aiortc pattern)."""
        def decorator(handler):
            if event == "frame":
                self._frame_handlers.append(handler)
            elif event == "ended":
                self._ended_handlers.append(handler)
            return handler
        return decorator

    async def emit_frame(self, frame: MockAudioFrame) -> None:
        """Emit a frame to all handlers."""
        if self._stopped:
            return
        for handler in self._frame_handlers:
            await handler(frame)

    async def emit_frames(
        self,
        count: int,
        frame_factory: Callable[[], MockAudioFrame] = None,
        interval_ms: float = 20,
    ) -> None:
        """Emit multiple frames with timing."""
        factory = frame_factory or MockAudioFrame.silence
        for _ in range(count):
            await self.emit_frame(factory())
            await asyncio.sleep(interval_ms / 1000)

    def stop(self) -> None:
        """Stop the track and fire ended handlers."""
        if self._stopped:
            return
        self._stopped = True
        for handler in self._ended_handlers:
            handler()

    def remove_listener(self, event: str, handler: Callable) -> None:
        """Remove event handler."""
        if event == "frame" and handler in self._frame_handlers:
            self._frame_handlers.remove(handler)
        elif event == "ended" and handler in self._ended_handlers:
            self._ended_handlers.remove(handler)
```

**Validation:** Mock track can emit frames, handlers receive them.

---

### Step 4: Implement Adapter Skeleton

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append)

```python
import asyncio
import logging
import time
from typing import Callable, Optional, Protocol

import numpy as np

from chatforge.ports.audio_capture import (
    AudioCapturePort,
    CaptureMetrics,
    CaptureState,
)


class AudioTrackProtocol(Protocol):
    """Protocol for WebRTC audio track (aiortc or mock)."""

    kind: str

    def on(self, event: str) -> Callable: ...
    def stop(self) -> None: ...


class WebRTCCaptureAdapter(AudioCapturePort):
    """
    Capture audio from a WebRTC peer connection.

    Implements AudioCapturePort for browser-based audio sources.
    Works with aiortc MediaStreamTrack or compatible mock.

    Audio Flow:
        Browser mic → Opus/SRTP → aiortc decode → This adapter → Queue[bytes]

    Example:
        track = peer_connection.getReceivers()[0].track
        adapter = WebRTCCaptureAdapter(track, session_id="abc123")

        queue = await adapter.start()
        async for chunk in queue_iterator(queue):
            process(chunk)
    """

    def __init__(
        self,
        audio_track: AudioTrackProtocol,
        session_id: str,
        config: Optional[WebRTCCaptureConfig] = None,
    ) -> None:
        """
        Initialize WebRTC capture adapter.

        Args:
            audio_track: WebRTC audio track (from RTCPeerConnection).
            session_id: Unique session identifier for logging/metrics.
            config: Capture configuration. Uses defaults if None.
        """
        if audio_track.kind != "audio":
            raise ValueError(f"Expected audio track, got {audio_track.kind}")

        self._track = audio_track
        self._session_id = session_id
        self._config = config or WebRTCCaptureConfig()
        self._logger = logging.getLogger(f"{__name__}.{session_id}")

        # State
        self._state = CaptureState.IDLE
        self._audio_queue: Optional[asyncio.Queue[bytes]] = None

        # Callbacks
        self._on_started: Optional[Callable[[], None]] = None
        self._on_stopped: Optional[Callable[[], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

        # Callback deduplication
        self._started_notified = False
        self._stopped_notified = False

        # Metrics
        self._metrics = CaptureMetrics()

        # Event handlers (stored for cleanup)
        self._frame_handler: Optional[Callable] = None
        self._ended_handler: Optional[Callable] = None

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> CaptureState:
        """Current capture state."""
        return self._state

    @property
    def is_capturing(self) -> bool:
        """Whether actively capturing audio."""
        return self._state == CaptureState.CAPTURING

    @property
    def config(self) -> WebRTCCaptureConfig:
        """Current configuration."""
        return self._config

    @property
    def session_id(self) -> str:
        """Session identifier."""
        return self._session_id
```

**Validation:** Adapter can be instantiated with mock track.

---

### Step 5: Implement start()

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append to class)

```python
    async def start(self) -> asyncio.Queue[bytes]:
        """
        Start receiving audio from the WebRTC track.

        Returns:
            Queue that will receive audio chunks as bytes.

        Raises:
            AudioCaptureError: If already capturing or track invalid.
        """
        if self._state != CaptureState.IDLE:
            raise WebRTCCaptureError(
                f"Cannot start: state is {self._state.value}, expected IDLE"
            )

        self._state = CaptureState.STARTING
        self._logger.debug("Starting WebRTC capture")

        # Create queue
        self._audio_queue = asyncio.Queue(maxsize=self._config.queue_size)

        # Reset metrics
        self._metrics = CaptureMetrics()
        self._metrics.start_time = time.time()

        # Reset notification flags
        self._started_notified = False
        self._stopped_notified = False

        # Subscribe to track events
        @self._track.on("frame")
        async def on_frame(frame):
            await self._process_frame(frame)

        @self._track.on("ended")
        def on_ended():
            self._handle_track_ended()

        # Store handlers for cleanup
        self._frame_handler = on_frame
        self._ended_handler = on_ended

        # Transition to capturing
        self._state = CaptureState.CAPTURING
        self._fire_started_callback()

        self._logger.info(f"WebRTC capture started (session={self._session_id})")

        return self._audio_queue
```

---

### Step 6: Implement _process_frame()

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append to class)

```python
    async def _process_frame(self, frame) -> None:
        """
        Process incoming WebRTC audio frame.

        Converts frame to bytes and puts in queue.
        """
        if self._state != CaptureState.CAPTURING:
            return

        try:
            # Extract audio data from frame
            # aiortc AudioFrame: planes[0] contains interleaved int16 samples
            audio_bytes = bytes(frame.planes[0])

            # Convert to numpy for processing
            samples = np.frombuffer(audio_bytes, dtype=np.int16)

            # Resample if needed
            if (
                self._config.resample_to
                and frame.sample_rate != self._config.resample_to
            ):
                samples = self._resample(
                    samples,
                    frame.sample_rate,
                    self._config.resample_to,
                )

            # Convert back to bytes
            output_bytes = samples.tobytes()

            # Put in queue
            try:
                self._audio_queue.put_nowait(output_bytes)
                self._metrics.chunks_captured += 1
                self._metrics.total_bytes += len(output_bytes)
            except asyncio.QueueFull:
                self._metrics.chunks_dropped += 1
                self._metrics.buffer_overruns += 1
                self._logger.warning("Audio queue full, dropping frame")

        except Exception as e:
            self._logger.error(f"Error processing frame: {e}")
            self._metrics.frames_skipped += 1
            self._fire_error_callback(e)
```

---

### Step 7: Implement _resample()

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append to class)

```python
    def _resample(
        self,
        samples: np.ndarray,
        from_rate: int,
        to_rate: int,
    ) -> np.ndarray:
        """
        Resample audio to target rate.

        Uses simple decimation for common ratios, scipy for others.
        """
        if from_rate == to_rate:
            return samples

        # Fast path: 48kHz → 24kHz (2:1 decimation)
        if from_rate == 48000 and to_rate == 24000:
            return samples[::2].copy()

        # Fast path: 48kHz → 16kHz (3:1 decimation)
        if from_rate == 48000 and to_rate == 16000:
            return samples[::3].copy()

        # General case: try scipy
        try:
            from scipy import signal
            num_samples = int(len(samples) * to_rate / from_rate)
            resampled = signal.resample(samples.astype(np.float32), num_samples)
            return resampled.astype(np.int16)
        except ImportError:
            # Fallback: linear interpolation
            self._logger.warning(
                "scipy not available, using linear interpolation for resampling"
            )
            ratio = to_rate / from_rate
            num_samples = int(len(samples) * ratio)
            indices = np.linspace(0, len(samples) - 1, num_samples)
            return np.interp(indices, np.arange(len(samples)), samples).astype(np.int16)
```

---

### Step 8: Implement stop() and Lifecycle Methods

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append to class)

```python
    def stop(self) -> None:
        """
        Stop capturing immediately (sync).

        For use in signal handlers or synchronous contexts.
        """
        if self._state != CaptureState.CAPTURING:
            return

        self._logger.debug("Stopping WebRTC capture")
        self._state = CaptureState.IDLE

        # Stop the track
        try:
            self._track.stop()
        except Exception as e:
            self._logger.warning(f"Error stopping track: {e}")

        # Send sentinel to unblock consumers
        if self._audio_queue:
            try:
                self._audio_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

        self._fire_stopped_callback()
        self._logger.info(f"WebRTC capture stopped (session={self._session_id})")

    async def stop_and_drain(self) -> None:
        """
        Stop capturing and wait for queue to drain.
        """
        self.stop()

        # Wait for queue to empty (with timeout)
        if self._audio_queue:
            try:
                await asyncio.wait_for(self._audio_queue.join(), timeout=2.0)
            except asyncio.TimeoutError:
                self._logger.warning("Queue drain timeout")

    def _handle_track_ended(self) -> None:
        """Handle WebRTC track ending (browser disconnected)."""
        if self._state != CaptureState.CAPTURING:
            return

        self._logger.info(f"Track ended (session={self._session_id})")
        self._state = CaptureState.IDLE

        # Send sentinel
        if self._audio_queue:
            try:
                self._audio_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

        self._fire_stopped_callback()

    def cleanup(self) -> None:
        """Release all resources."""
        self.stop()
        self._audio_queue = None
        self._frame_handler = None
        self._ended_handler = None
```

---

### Step 9: Implement Callbacks and Metrics

**File:** `chatforge/adapters/audio_capture/webrtc_adapter.py` (append to class)

```python
    def set_callbacks(
        self,
        on_started: Optional[Callable[[], None]] = None,
        on_stopped: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Set event callbacks."""
        self._on_started = on_started
        self._on_stopped = on_stopped
        self._on_error = on_error

    def get_metrics(self) -> CaptureMetrics:
        """Get capture metrics."""
        return self._metrics

    def _fire_started_callback(self) -> None:
        """Fire on_started callback (with deduplication)."""
        if self._started_notified:
            return
        self._started_notified = True

        if self._on_started:
            try:
                self._on_started()
            except Exception as e:
                self._logger.error(f"on_started callback error: {e}")

    def _fire_stopped_callback(self) -> None:
        """Fire on_stopped callback (with deduplication)."""
        if self._stopped_notified:
            return
        self._stopped_notified = True

        if self._on_stopped:
            try:
                self._on_stopped()
            except Exception as e:
                self._logger.error(f"on_stopped callback error: {e}")

    def _fire_error_callback(self, error: Exception) -> None:
        """Fire on_error callback."""
        if self._on_error:
            try:
                self._on_error(error)
            except Exception as e:
                self._logger.error(f"on_error callback error: {e}")
```

---

### Step 10: Update __init__.py Exports

**File:** `chatforge/adapters/audio_capture/__init__.py`

Add to existing exports:

```python
from chatforge.adapters.audio_capture.webrtc_adapter import (
    WebRTCCaptureAdapter,
    WebRTCCaptureConfig,
    WebRTCCaptureError,
    TrackEndedError,
    ConnectionLostError,
    CodecError,
)

__all__ = [
    # ... existing exports ...
    # WebRTC
    "WebRTCCaptureAdapter",
    "WebRTCCaptureConfig",
    "WebRTCCaptureError",
    "TrackEndedError",
    "ConnectionLostError",
    "CodecError",
]
```

---

## Phase 2: Unit Tests (Mock Track)

### Step 11: Create Unit Test File

**File:** `tests/adapters/audio_capture/test_webrtc_adapter.py`

```python
"""
Unit tests for WebRTCCaptureAdapter.

Uses MockAudioTrack to test without aiortc dependency.
"""

import asyncio
import pytest
import numpy as np

from chatforge.adapters.audio_capture import (
    WebRTCCaptureAdapter,
    WebRTCCaptureConfig,
    WebRTCCaptureError,
)
from chatforge.ports.audio_capture import CaptureState

from .webrtc_fixtures import MockAudioTrack, MockAudioFrame


# =============================================================================
# Basic State Tests
# =============================================================================

class TestWebRTCAdapterBasicState:
    """Test basic state behavior."""

    def test_initial_state_is_idle(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_start_transitions_to_capturing(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        queue = await adapter.start()

        assert adapter.state == CaptureState.CAPTURING
        assert adapter.is_capturing
        assert queue is not None

    @pytest.mark.asyncio
    async def test_stop_transitions_to_idle(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        await adapter.start()
        adapter.stop()

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_cannot_start_twice(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        await adapter.start()

        with pytest.raises(WebRTCCaptureError, match="Cannot start"):
            await adapter.start()


# =============================================================================
# Frame Processing Tests
# =============================================================================

class TestWebRTCAdapterFrameProcessing:
    """Test audio frame processing."""

    @pytest.mark.asyncio
    async def test_receives_frames(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        queue = await adapter.start()

        # Emit a frame
        frame = MockAudioFrame.sine(duration_ms=20)
        await track.emit_frame(frame)

        # Should receive in queue
        chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert len(chunk) > 0

    @pytest.mark.asyncio
    async def test_resamples_48k_to_24k(self):
        track = MockAudioTrack()
        config = WebRTCCaptureConfig(resample_to=24000)
        adapter = WebRTCCaptureAdapter(track, session_id="test", config=config)

        queue = await adapter.start()

        # Emit 48kHz frame (960 samples = 20ms)
        frame = MockAudioFrame.sine(duration_ms=20, sample_rate=48000)
        await track.emit_frame(frame)

        chunk = await asyncio.wait_for(queue.get(), timeout=1.0)

        # After resampling: 480 samples * 2 bytes = 960 bytes
        # Original was 960 samples * 2 bytes = 1920 bytes
        assert len(chunk) == 960  # Half the samples

    @pytest.mark.asyncio
    async def test_no_resample_when_disabled(self):
        track = MockAudioTrack()
        config = WebRTCCaptureConfig(resample_to=None)
        adapter = WebRTCCaptureAdapter(track, session_id="test", config=config)

        queue = await adapter.start()

        frame = MockAudioFrame.sine(duration_ms=20, sample_rate=48000)
        await track.emit_frame(frame)

        chunk = await asyncio.wait_for(queue.get(), timeout=1.0)

        # No resampling: 960 samples * 2 bytes = 1920 bytes
        assert len(chunk) == 1920

    @pytest.mark.asyncio
    async def test_multiple_frames(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        queue = await adapter.start()

        # Emit multiple frames
        for _ in range(5):
            await track.emit_frame(MockAudioFrame.silence())

        # Should receive all
        chunks = []
        for _ in range(5):
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            chunks.append(chunk)

        assert len(chunks) == 5
        assert adapter.get_metrics().chunks_captured == 5


# =============================================================================
# Callback Tests
# =============================================================================

class TestWebRTCAdapterCallbacks:
    """Test callback behavior."""

    @pytest.mark.asyncio
    async def test_on_started_fires(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        started = []
        adapter.set_callbacks(on_started=lambda: started.append(True))

        await adapter.start()

        assert len(started) == 1

    @pytest.mark.asyncio
    async def test_on_stopped_fires(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        stopped = []
        adapter.set_callbacks(on_stopped=lambda: stopped.append(True))

        await adapter.start()
        adapter.stop()

        assert len(stopped) == 1

    @pytest.mark.asyncio
    async def test_on_stopped_fires_on_track_ended(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        stopped = []
        adapter.set_callbacks(on_stopped=lambda: stopped.append(True))

        await adapter.start()
        track.stop()  # Simulate browser disconnect

        assert len(stopped) == 1

    @pytest.mark.asyncio
    async def test_callbacks_fire_once(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        started = []
        stopped = []
        adapter.set_callbacks(
            on_started=lambda: started.append(True),
            on_stopped=lambda: stopped.append(True),
        )

        await adapter.start()
        adapter.stop()
        adapter.stop()  # Double stop

        assert len(started) == 1
        assert len(stopped) == 1


# =============================================================================
# Track Ended Tests
# =============================================================================

class TestWebRTCAdapterTrackEnded:
    """Test track ended behavior."""

    @pytest.mark.asyncio
    async def test_track_ended_sends_sentinel(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        queue = await adapter.start()
        track.stop()

        sentinel = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert sentinel is None

    @pytest.mark.asyncio
    async def test_track_ended_transitions_to_idle(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        await adapter.start()
        track.stop()

        assert adapter.state == CaptureState.IDLE


# =============================================================================
# Metrics Tests
# =============================================================================

class TestWebRTCAdapterMetrics:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_chunks_captured_counted(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        await adapter.start()

        for _ in range(10):
            await track.emit_frame(MockAudioFrame.silence())

        metrics = adapter.get_metrics()
        assert metrics.chunks_captured == 10

    @pytest.mark.asyncio
    async def test_total_bytes_tracked(self):
        track = MockAudioTrack()
        config = WebRTCCaptureConfig(resample_to=None)
        adapter = WebRTCCaptureAdapter(track, session_id="test", config=config)

        await adapter.start()

        frame = MockAudioFrame.silence(duration_ms=20, sample_rate=48000)
        await track.emit_frame(frame)

        metrics = adapter.get_metrics()
        assert metrics.total_bytes == 1920  # 960 samples * 2 bytes


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestWebRTCAdapterErrorHandling:
    """Test error handling."""

    def test_rejects_non_audio_track(self):
        track = MockAudioTrack()
        track.kind = "video"

        with pytest.raises(ValueError, match="Expected audio track"):
            WebRTCCaptureAdapter(track, session_id="test")

    @pytest.mark.asyncio
    async def test_error_callback_on_processing_error(self):
        track = MockAudioTrack()
        adapter = WebRTCCaptureAdapter(track, session_id="test")

        errors = []
        adapter.set_callbacks(on_error=lambda e: errors.append(e))

        await adapter.start()

        # Emit invalid frame (will cause processing error)
        bad_frame = MockAudioFrame(planes=[b"invalid"], sample_rate=48000)
        await track.emit_frame(bad_frame)

        # Error should be captured, not raised
        # (adapter continues operating)
        assert adapter.is_capturing
```

**Validation:** Run `pytest tests/adapters/audio_capture/test_webrtc_adapter.py -v`

---

## Phase 3: Integration Tests (aiortc)

### Step 12: Create Integration Test File

**File:** `tests/adapters/audio_capture/test_webrtc_adapter_integration.py`

```python
"""
Integration tests for WebRTCCaptureAdapter using real aiortc.

Requires: pip install aiortc

These tests create actual WebRTC peer connections.
"""

import asyncio
import pytest
import numpy as np

# Skip if aiortc not installed
aiortc = pytest.importorskip("aiortc")

from aiortc import RTCPeerConnection
from aiortc.contrib.media import MediaPlayer
from aiortc.mediastreams import AudioStreamTrack

from chatforge.adapters.audio_capture import WebRTCCaptureAdapter, WebRTCCaptureConfig


class SineWaveTrack(AudioStreamTrack):
    """Audio track that generates sine wave for testing."""

    def __init__(self, frequency: int = 440, duration: float = 5.0):
        super().__init__()
        self.frequency = frequency
        self.duration = duration
        self._timestamp = 0
        self._samples_per_frame = 960  # 20ms at 48kHz

    async def recv(self):
        from av import AudioFrame

        # Generate sine wave
        t = np.linspace(
            self._timestamp / 48000,
            (self._timestamp + self._samples_per_frame) / 48000,
            self._samples_per_frame,
            endpoint=False,
        )
        samples = (np.sin(2 * np.pi * self.frequency * t) * 16000).astype(np.int16)

        # Create frame
        frame = AudioFrame(format="s16", layout="mono", samples=self._samples_per_frame)
        frame.sample_rate = 48000
        frame.pts = self._timestamp
        frame.planes[0].update(samples.tobytes())

        self._timestamp += self._samples_per_frame

        # Simulate real-time
        await asyncio.sleep(0.02)

        return frame


@pytest.mark.asyncio
async def test_real_webrtc_connection():
    """Test with real aiortc peer connections."""

    # Create peer connections
    browser_pc = RTCPeerConnection()
    server_pc = RTCPeerConnection()

    # Add audio track to "browser"
    audio_track = SineWaveTrack(frequency=440)
    browser_pc.addTrack(audio_track)

    # Collect received tracks on server
    received_track = None

    @server_pc.on("track")
    def on_track(track):
        nonlocal received_track
        if track.kind == "audio":
            received_track = track

    try:
        # Exchange SDP
        offer = await browser_pc.createOffer()
        await browser_pc.setLocalDescription(offer)
        await server_pc.setRemoteDescription(offer)

        answer = await server_pc.createAnswer()
        await server_pc.setLocalDescription(answer)
        await browser_pc.setRemoteDescription(answer)

        # Wait for connection
        await asyncio.sleep(0.5)

        assert received_track is not None, "Should receive audio track"

        # Test our adapter
        adapter = WebRTCCaptureAdapter(
            received_track,
            session_id="integration-test",
            config=WebRTCCaptureConfig(resample_to=24000),
        )

        queue = await adapter.start()

        # Collect some audio
        chunks = []
        for _ in range(5):
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=2.0)
                if chunk is None:
                    break
                chunks.append(chunk)
            except asyncio.TimeoutError:
                break

        assert len(chunks) >= 3, f"Should receive audio chunks, got {len(chunks)}"
        assert all(len(c) > 0 for c in chunks)

        # Verify resampling worked (24kHz, 20ms = 480 samples = 960 bytes)
        # Note: actual frame sizes may vary slightly

        adapter.stop()

    finally:
        await browser_pc.close()
        await server_pc.close()
```

**Validation:** Run `pytest tests/adapters/audio_capture/test_webrtc_adapter_integration.py -v`

---

## Validation Checklist

### Phase 1 Validation

- [ ] Exception classes importable
- [ ] WebRTCCaptureConfig instantiable with defaults
- [ ] MockAudioTrack emits frames correctly
- [ ] Adapter can be created with mock track
- [ ] `start()` returns queue and transitions state
- [ ] `stop()` transitions state and sends sentinel
- [ ] Callbacks fire correctly

### Phase 2 Validation

- [ ] All unit tests pass
- [ ] Frame processing works
- [ ] Resampling produces correct output sizes
- [ ] Metrics are tracked
- [ ] Error handling doesn't crash adapter

### Phase 3 Validation

- [ ] aiortc integration test passes
- [ ] Real audio flows through adapter
- [ ] Resampling works with real frames

---

## Post-Implementation

### Future Enhancements (Not in Scope)

1. **WebRTC Stats Integration** - Fetch RTCStats for packet loss, jitter metrics
2. **Jitter Buffer Tuning** - Expose aiortc jitter buffer configuration
3. **Multiple Tracks** - Support stereo or multi-track connections
4. **Opus Settings** - Expose DTX, FEC, bandwidth settings

### Integration with WebRTCSignalingServer

After this adapter is complete, the signaling server can create adapters:

```python
# In signaling server's session handler
@server_pc.on("track")
def on_track(track):
    if track.kind == "audio":
        adapter = WebRTCCaptureAdapter(track, session_id)
        await handle_audio_session(adapter)
```

This is documented in `webrtc_signaling_server/desc.md`.
