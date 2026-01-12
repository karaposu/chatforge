"""
File Capture Adapter.

Reads audio data from a WAV file instead of a microphone.
Useful for testing and debugging without actual audio hardware.

Note: This is a "source" adapter that reads from file rather than
capturing from a microphone. It implements the same interface for consistency.

Example:
    from chatforge.adapters.audio_capture import FileCaptureAdapter
    from chatforge.ports.audio_capture import AudioCaptureConfig

    capture = FileCaptureAdapter("test_audio.wav", realtime=True)

    audio_queue = await capture.start()
    while capture.is_capturing:
        chunk = await audio_queue.get()
        process_audio(chunk)
"""

import asyncio
import logging
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Optional, Union

from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    AudioCaptureError,
    AudioCapturePort,
    AudioDevice,
    CaptureMetrics,
    CaptureState,
    UnsupportedConfigError,
)


__all__ = ["FileCaptureAdapter"]


class FileCaptureAdapter(AudioCapturePort):
    """
    Audio capture from WAV file.

    For testing without real microphone.
    Does NOT implement DeviceEnumerable (no devices).

    Features:
        - Load WAV file
        - Chunk into appropriate sizes
        - Optional real-time timing simulation
        - Optional loop mode
        - Optional resampling (requires scipy)

    Thread Safety:
        - Async-only operation
        - Reader task runs in asyncio

    Example:
        capture = FileCaptureAdapter("test.wav", loop=True, realtime=True)
        audio_queue = await capture.start()
        # ... consume chunks ...
        capture.stop()
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        config: Optional[AudioCaptureConfig] = None,
        loop: bool = False,
        realtime: bool = True,
        resample: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize file capture adapter.

        Args:
            file_path: Path to WAV file
            config: Audio configuration (sample_rate, channels, bit_depth)
            loop: If True, loop forever until stop() is called
            realtime: If True, simulate real-time speed with sleeps
            resample: If True, resample audio to match config (requires scipy)
            logger: Optional logger

        Raises:
            AudioCaptureError: If file cannot be opened
            UnsupportedConfigError: If sample rate mismatch and resample=False
            ImportError: If resample=True but scipy not installed
        """
        self._file_path = Path(file_path)
        self._config = config or AudioCaptureConfig()
        self._loop = loop
        self._realtime = realtime
        self._resample = resample
        self._logger = logger or logging.getLogger(__name__)

        # Validate file exists
        if not self._file_path.exists():
            raise AudioCaptureError(f"File not found: {self._file_path}")

        # Check scipy if resampling requested
        self._resample_fn = None
        if resample:
            try:
                from scipy.signal import resample as scipy_resample

                self._resample_fn = scipy_resample
            except ImportError:
                raise ImportError(
                    "Resampling requires scipy. Install with: pip install scipy"
                )

        # State management
        self._capturing_event = threading.Event()
        self._state = CaptureState.IDLE
        self._state_lock = threading.Lock()

        # Queue
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(
            maxsize=self._config.async_buffer_size
        )

        # Reader task
        self._reader_task: Optional[asyncio.Task] = None

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

        # File info (loaded lazily)
        self._wav_file: Optional[wave.Wave_read] = None
        self._file_sample_rate: Optional[int] = None
        self._file_channels: Optional[int] = None
        self._file_sample_width: Optional[int] = None

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
        """True if actively reading file."""
        return self._capturing_event.is_set()

    @property
    def file_path(self) -> Path:
        """Path to input file."""
        return self._file_path

    # =========================================================================
    # Core Methods
    # =========================================================================

    async def start(self) -> asyncio.Queue[bytes]:
        """
        Start reading from file.

        Returns:
            asyncio.Queue[bytes]: Queue that receives audio chunks

        Raises:
            AudioCaptureError: If file cannot be read
            UnsupportedConfigError: If sample rate mismatch and resample=False
        """
        if self._capturing_event.is_set():
            self._logger.warning("start() called while already capturing")
            return self._audio_queue

        # Reset state for new session
        self._reset_state()

        try:
            # Open WAV file
            self._wav_file = wave.open(str(self._file_path), "rb")
            self._file_sample_rate = self._wav_file.getframerate()
            self._file_channels = self._wav_file.getnchannels()
            self._file_sample_width = self._wav_file.getsampwidth()

            # Validate or resample
            if self._file_sample_rate != self._config.sample_rate:
                if not self._resample:
                    raise UnsupportedConfigError(
                        f"File sample rate ({self._file_sample_rate}) doesn't match "
                        f"config ({self._config.sample_rate}). Use resample=True to convert."
                    )

            if self._file_channels != self._config.channels:
                self._logger.warning(
                    f"File has {self._file_channels} channels but config expects "
                    f"{self._config.channels}. Reading as-is."
                )

            # Update state
            self._capturing_event.set()
            self._metrics.start_time = time.time()

            with self._state_lock:
                self._state = CaptureState.CAPTURING

            self._logger.info(
                f"File capture started: {self._file_path} "
                f"({self._file_sample_rate}Hz, {self._file_channels}ch)"
            )

            # Fire on_started callback ONCE
            if not self._started_notified and self._on_started:
                self._started_notified = True
                try:
                    self._on_started()
                except Exception as e:
                    self._logger.error(f"on_started callback error: {e}")

            # Start reader task
            self._reader_task = asyncio.create_task(self._read_file())

            return self._audio_queue

        except Exception as e:
            self._logger.error(f"Failed to start file capture: {e}")
            with self._state_lock:
                self._state = CaptureState.ERROR
            if isinstance(e, (AudioCaptureError, UnsupportedConfigError)):
                raise
            raise AudioCaptureError(f"Failed to start file capture: {e}")

    def stop(self) -> None:
        """Stop reading (sync)."""
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop requested (sync)")

        # Clear capturing flag
        self._capturing_event.clear()

        # Close file
        if self._wav_file:
            try:
                self._wav_file.close()
            except Exception as e:
                self._logger.error(f"Error closing file: {e}")
            finally:
                self._wav_file = None

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

        self._logger.info(f"File capture stopped. Chunks: {self._metrics.chunks_captured}")

    async def stop_and_drain(self) -> None:
        """Stop reading and drain remaining chunks (async)."""
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop and drain requested")

        # Clear capturing flag
        self._capturing_event.clear()

        # Wait for reader task to complete
        if self._reader_task:
            try:
                await asyncio.wait_for(self._reader_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._logger.warning("Reader task didn't complete in time")
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass
            finally:
                self._reader_task = None

        # Close file
        if self._wav_file:
            try:
                self._wav_file.close()
            except Exception as e:
                self._logger.error(f"Error closing file: {e}")
            finally:
                self._wav_file = None

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
            f"File capture stopped (drained). Chunks: {self._metrics.chunks_captured}"
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
        """No device for file adapter."""
        return None

    def cleanup(self) -> None:
        """Close file and release resources."""
        # Stop if capturing
        if self._capturing_event.is_set():
            self.stop()

        # Clear queue
        self._clear_queue()

        # Reset state
        self._reset_state()

        self._logger.debug(f"File capture cleaned up: {self._file_path}")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _read_file(self) -> None:
        """Read file and enqueue chunks."""
        try:
            # Calculate frames per chunk
            frames_per_chunk = self._config.chunk_samples
            chunk_duration_sec = self._config.chunk_duration_ms / 1000.0

            while self._capturing_event.is_set():
                # Read frames
                if self._wav_file is None:
                    break

                frames = self._wav_file.readframes(frames_per_chunk)

                if not frames:
                    # End of file
                    if self._loop:
                        # Rewind and continue
                        self._wav_file.rewind()
                        continue
                    else:
                        # Done
                        break

                # Resample if needed
                if self._resample and self._file_sample_rate != self._config.sample_rate:
                    frames = self._resample_audio(frames)

                # Update metrics
                self._metrics.chunks_captured += 1
                self._metrics.total_bytes += len(frames)

                # Put in queue
                await self._audio_queue.put(frames)

                # Fire on_chunk_captured callback
                if self._on_chunk_captured:
                    try:
                        self._on_chunk_captured(self._metrics.chunks_captured)
                    except Exception as e:
                        self._logger.error(f"on_chunk_captured callback error: {e}")

                # Simulate real-time timing
                if self._realtime:
                    await asyncio.sleep(chunk_duration_sec)

        except asyncio.CancelledError:
            self._logger.debug("Reader task cancelled")
            raise
        except Exception as e:
            self._logger.error(f"Error reading file: {e}")
            with self._state_lock:
                self._state = CaptureState.ERROR
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception as cb_error:
                    self._logger.error(f"on_error callback error: {cb_error}")
        finally:
            self._logger.debug("Reader task ended")

    def _resample_audio(self, audio_bytes: bytes) -> bytes:
        """Resample audio to target sample rate."""
        import numpy as np

        # Convert bytes to numpy array
        dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(
            self._file_sample_width, np.int16
        )
        audio_array = np.frombuffer(audio_bytes, dtype=dtype)

        # Calculate new length
        ratio = self._config.sample_rate / self._file_sample_rate
        new_length = int(len(audio_array) * ratio)

        # Resample
        resampled = self._resample_fn(audio_array, new_length)

        # Convert back to bytes
        return resampled.astype(np.int16).tobytes()

    def _reset_state(self) -> None:
        """Reset adapter state for new session."""
        # Clear queue
        self._clear_queue()

        # Reset metrics
        self._metrics = CaptureMetrics()

        # Reset deduplication flags
        self._started_notified = False
        self._stopped_notified = False

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
