"""
Null Capture Adapter.

Generates silence or configurable test signals instead of capturing from
a real microphone. Useful for testing without actual audio hardware.

Example:
    from chatforge.adapters.audio_capture import NullCaptureAdapter

    capture = NullCaptureAdapter(signal="silence")
    capture.set_callbacks(on_started=lambda: print("Started!"))

    audio_queue = await capture.start()
    chunks = []
    for _ in range(10):
        chunk = await audio_queue.get()
        chunks.append(chunk)

    capture.stop()
    assert len(chunks) == 10
"""

import asyncio
import logging
import math
import threading
import time
from typing import Callable, Optional

import numpy as np

from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    AudioCapturePort,
    AudioDevice,
    CaptureMetrics,
    CaptureState,
)


__all__ = ["NullCaptureAdapter"]


class NullCaptureAdapter(AudioCapturePort):
    """
    Null audio capture adapter for testing.

    Generates silence or configurable test signals.
    Does NOT implement DeviceEnumerable (no devices).

    Useful for:
        - Unit testing without audio hardware
        - Integration testing without sound input
        - Benchmarking audio processing pipelines
        - Testing signal processing with known signals

    Thread Safety:
        - Async-only operation
        - Generator task runs in asyncio

    Example:
        capture = NullCaptureAdapter(signal="sine", frequency=440)
        audio_queue = await capture.start()
        # ... consume chunks ...
        capture.stop()
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        signal: str = "silence",
        frequency: int = 440,
        amplitude: float = 0.5,
        duration_ms: int = 0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize null capture adapter.

        Args:
            config: Audio configuration (used for timing and format)
            signal: Signal type - "silence", "sine", or "noise"
            frequency: Frequency for sine wave in Hz (default 440)
            amplitude: Amplitude 0.0-1.0 (default 0.5)
            duration_ms: Duration in ms, 0 = infinite until stop() (default 0)
            logger: Optional logger
        """
        self._config = config or AudioCaptureConfig()
        self._signal = signal
        self._frequency = frequency
        self._amplitude = max(0.0, min(1.0, amplitude))
        self._duration_ms = duration_ms
        self._logger = logger or logging.getLogger(__name__)

        # Pre-computed values
        self._chunk_samples = self._config.chunk_samples
        self._chunk_bytes = self._config.chunk_bytes
        self._max_amplitude = int(32767 * self._amplitude)

        # State management
        self._capturing_event = threading.Event()
        self._state = CaptureState.IDLE
        self._state_lock = threading.Lock()

        # Queue
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(
            maxsize=self._config.async_buffer_size
        )

        # Generator task
        self._generator_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = CaptureMetrics()

        # Callback deduplication flags
        self._started_notified = False
        self._stopped_notified = False

        # Callbacks
        self._on_started: Optional[Callable[[], None]] = None
        self._on_stopped: Optional[Callable[[], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
        self._on_chunk_captured: Optional[Callable[[int], None]] = None

        # Signal generation state
        self._sample_index = 0

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> CaptureState:
        """Current capture state."""
        with self._state_lock:
            return self._state

    @property
    def config(self) -> AudioCaptureConfig:
        """Current configuration."""
        return self._config

    @property
    def is_capturing(self) -> bool:
        """True if actively generating."""
        return self._capturing_event.is_set()

    @property
    def signal_type(self) -> str:
        """Type of signal being generated."""
        return self._signal

    # =========================================================================
    # Core Methods
    # =========================================================================

    async def start(self) -> asyncio.Queue[bytes]:
        """
        Start generating audio.

        Returns:
            asyncio.Queue[bytes]: Queue that receives audio chunks
        """
        if self._capturing_event.is_set():
            self._logger.warning("start() called while already capturing")
            return self._audio_queue

        # Reset state for new session
        self._reset_state()

        # Update state
        self._capturing_event.set()
        self._metrics.start_time = time.time()

        with self._state_lock:
            self._state = CaptureState.CAPTURING

        self._logger.info(
            f"Null capture started: {self._signal} signal "
            f"({self._config.sample_rate}Hz, {self._config.channels}ch)"
        )

        # Fire on_started callback ONCE
        if not self._started_notified and self._on_started:
            self._started_notified = True
            try:
                self._on_started()
            except Exception as e:
                self._logger.error(f"on_started callback error: {e}")

        # Start generator task
        self._generator_task = asyncio.create_task(self._generate_audio())

        return self._audio_queue

    def stop(self) -> None:
        """Stop generating (sync)."""
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop requested (sync)")

        # Clear capturing flag
        self._capturing_event.clear()

        # Update state
        with self._state_lock:
            self._state = CaptureState.IDLE

        # Fire on_stopped callback ONCE
        if not self._stopped_notified and self._on_stopped:
            self._stopped_notified = True
            try:
                self._on_stopped()
            except Exception as e:
                self._logger.error(f"on_stopped callback error: {e}")

        self._logger.info(f"Null capture stopped. Chunks: {self._metrics.chunks_captured}")

    async def stop_and_drain(self) -> None:
        """Stop generating and drain remaining chunks (async)."""
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop and drain requested")

        # Clear capturing flag
        self._capturing_event.clear()

        # Wait for generator task to complete
        if self._generator_task:
            try:
                await asyncio.wait_for(self._generator_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._logger.warning("Generator task didn't complete in time")
                self._generator_task.cancel()
                try:
                    await self._generator_task
                except asyncio.CancelledError:
                    pass
            finally:
                self._generator_task = None

        # Update state
        with self._state_lock:
            self._state = CaptureState.IDLE

        # Fire on_stopped callback ONCE
        if not self._stopped_notified and self._on_stopped:
            self._stopped_notified = True
            try:
                self._on_stopped()
            except Exception as e:
                self._logger.error(f"on_stopped callback error: {e}")

        self._logger.info(
            f"Null capture stopped (drained). Chunks: {self._metrics.chunks_captured}"
        )

    def get_metrics(self) -> CaptureMetrics:
        """Get capture performance metrics."""
        return CaptureMetrics(
            chunks_captured=self._metrics.chunks_captured,
            chunks_dropped=self._metrics.chunks_dropped,
            buffer_overruns=self._metrics.buffer_overruns,
            total_bytes=self._metrics.total_bytes,
            start_time=self._metrics.start_time,
        )

    def get_device_info(self) -> Optional[AudioDevice]:
        """No device for null adapter."""
        return None

    def cleanup(self) -> None:
        """No resources to clean up."""
        # Stop if capturing
        if self._capturing_event.is_set():
            self.stop()

        # Clear queue
        self._clear_queue()

        # Reset state
        self._reset_state()

        self._logger.debug("Null capture cleaned up")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _generate_audio(self) -> None:
        """Generate and enqueue audio chunks."""
        chunk_duration_sec = self._config.chunk_duration_ms / 1000.0
        start_time = time.time()

        try:
            while self._capturing_event.is_set():
                # Check duration limit
                if self._duration_ms > 0:
                    elapsed_ms = (time.time() - start_time) * 1000
                    if elapsed_ms >= self._duration_ms:
                        break

                # Generate chunk
                audio_bytes = self._generate_chunk()

                # Update metrics
                self._metrics.chunks_captured += 1
                self._metrics.total_bytes += len(audio_bytes)

                # Put in queue
                await self._audio_queue.put(audio_bytes)

                # Fire on_chunk_captured callback
                if self._on_chunk_captured:
                    try:
                        self._on_chunk_captured(self._metrics.chunks_captured)
                    except Exception as e:
                        self._logger.error(f"on_chunk_captured callback error: {e}")

                # Simulate real-time timing
                await asyncio.sleep(chunk_duration_sec)

        except asyncio.CancelledError:
            self._logger.debug("Generator task cancelled")
            raise
        except Exception as e:
            self._logger.error(f"Error generating audio: {e}")
            with self._state_lock:
                self._state = CaptureState.ERROR
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception as cb_error:
                    self._logger.error(f"on_error callback error: {cb_error}")
        finally:
            self._logger.debug("Generator task ended")

    def _generate_chunk(self) -> bytes:
        """Generate one chunk of audio."""
        samples = self._chunk_samples * self._config.channels

        if self._signal == "silence":
            # Generate silence (zeros)
            audio_array = np.zeros(samples, dtype=np.int16)

        elif self._signal == "sine":
            # Generate sine wave
            t = np.arange(self._sample_index, self._sample_index + samples)
            self._sample_index += samples
            # Calculate samples accounting for channels
            mono_samples = t // self._config.channels
            audio = np.sin(
                2 * math.pi * self._frequency * mono_samples / self._config.sample_rate
            )
            audio_array = (audio * self._max_amplitude).astype(np.int16)

        elif self._signal == "noise":
            # Generate white noise
            audio = np.random.uniform(-1, 1, samples)
            audio_array = (audio * self._max_amplitude).astype(np.int16)

        else:
            # Unknown signal type, use silence
            self._logger.warning(f"Unknown signal type '{self._signal}', using silence")
            audio_array = np.zeros(samples, dtype=np.int16)

        return audio_array.tobytes()

    def _reset_state(self) -> None:
        """Reset adapter state for new session."""
        # Clear queue
        self._clear_queue()

        # Reset metrics
        self._metrics = CaptureMetrics()

        # Reset deduplication flags
        self._started_notified = False
        self._stopped_notified = False

        # Reset signal state
        self._sample_index = 0

        # Reset state
        with self._state_lock:
            self._state = CaptureState.IDLE

    def _clear_queue(self) -> None:
        """Clear async queue."""
        while True:
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def reset(self) -> None:
        """
        Reset adapter for reuse in tests.

        Clears all state and metrics.
        """
        self.stop()
        self._reset_state()
        self._logger.debug("Null capture reset")
