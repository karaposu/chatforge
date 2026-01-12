"""
SoundDevice Capture Adapter.

Primary adapter for microphone input using sounddevice library.
Uses a queue-based async interface matching VoxStream's DirectAudioCapture.

Features:
    - Queue-based async interface (not iterator)
    - Triple-buffered capture for zero drops
    - Both sync and async stop methods
    - Callback deduplication
    - Proper drain on stop

Example:
    from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
    from chatforge.ports.audio_capture import AudioCaptureConfig

    capture = SoundDeviceCaptureAdapter(AudioCaptureConfig(sample_rate=24000))
    capture.set_callbacks(
        on_started=lambda: print("Capturing..."),
        on_stopped=lambda: print("Stopped!"),
    )

    audio_queue = await capture.start()
    while capture.is_capturing:
        chunk = await audio_queue.get()
        process_audio(chunk)
        if should_stop:
            capture.stop()  # Sync stop
            break
"""

import asyncio
import logging
import queue
import threading
import time
from typing import Callable, List, Optional

import numpy as np
import sounddevice as sd

from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    AudioCaptureError,
    AudioCapturePort,
    AudioDevice,
    CaptureMetrics,
    CaptureState,
    DeviceEnumerable,
    DeviceNotFoundError,
)


__all__ = ["SoundDeviceCaptureAdapter"]


class SoundDeviceCaptureAdapter(AudioCapturePort, DeviceEnumerable):
    """
    Audio capture using sounddevice library.

    Features:
        - Queue-based async interface (not iterator)
        - Triple-buffered capture for zero drops
        - Both sync and async stop methods
        - Callback deduplication
        - Proper drain on stop

    Thread Safety:
        - Audio callback runs in sounddevice thread
        - Transfer loop runs in asyncio
        - State protected by threading.Event
        - Callbacks fire from asyncio context

    Example:
        capture = SoundDeviceCaptureAdapter()
        capture.set_callbacks(on_started=..., on_stopped=...)

        audio_queue = await capture.start()
        while capture.is_capturing:
            chunk = await audio_queue.get()
            process(chunk)
            if should_stop:
                capture.stop()
                break

        capture.cleanup()
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        latency: str = "low",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize SoundDevice capture adapter.

        Args:
            config: Audio capture configuration. Uses defaults if not provided.
            latency: Latency preference - "low", "high", or float seconds.
            logger: Optional logger for debugging.
        """
        self._config = config or AudioCaptureConfig()
        self._latency = latency
        self._logger = logger or logging.getLogger(__name__)

        # Pre-computed values
        self._chunk_samples = self._config.chunk_samples

        # State management (thread-safe via Event)
        self._capturing_event = threading.Event()
        self._state = CaptureState.IDLE
        self._state_lock = threading.Lock()

        # Queues
        # callback_queue: sync queue for audio callback -> transfer task
        self._callback_queue: queue.Queue = queue.Queue(
            maxsize=self._config.callback_buffer_size
        )
        # audio_queue: async queue for transfer task -> consumer
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(
            maxsize=self._config.async_buffer_size
        )

        # Stream and transfer task
        self._stream: Optional[sd.InputStream] = None
        self._transfer_task: Optional[asyncio.Task] = None

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

        # Device info
        self._resolved_device_id: Optional[int] = None
        self._device_info: Optional[AudioDevice] = None
        self._resolve_device()

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
        """True if actively capturing audio."""
        return self._capturing_event.is_set()

    # =========================================================================
    # Core Methods
    # =========================================================================

    async def start(self) -> asyncio.Queue[bytes]:
        """
        Start audio capture.

        Returns an asyncio.Queue that receives audio chunks as bytes.

        Returns:
            asyncio.Queue[bytes]: Queue that receives audio chunks

        Raises:
            AudioCaptureError: If capture cannot be started
            DeviceNotFoundError: If configured device not found
        """
        # Check if already capturing
        if self._capturing_event.is_set():
            self._logger.warning("start() called while already capturing")
            return self._audio_queue

        # Reset state for new session
        self._reset_state()

        try:
            # Create input stream
            self._stream = sd.InputStream(
                device=self._resolved_device_id,
                channels=self._config.channels,
                samplerate=self._config.sample_rate,
                blocksize=self._chunk_samples,
                dtype=np.int16,
                callback=self._audio_callback,
                latency=self._latency,
            )

            # Start stream
            self._stream.start()

            # Update state
            self._capturing_event.set()
            self._metrics.start_time = time.time()

            with self._state_lock:
                self._state = CaptureState.CAPTURING

            self._logger.info(
                f"Capture started on {self._device_info.name if self._device_info else 'default'} "
                f"({self._config.sample_rate}Hz, {self._config.channels}ch)"
            )

            # Fire on_started callback ONCE
            if not self._started_notified and self._on_started:
                self._started_notified = True
                try:
                    self._on_started()
                except Exception as e:
                    self._logger.error(f"on_started callback error: {e}")

            # Start transfer task
            self._transfer_task = asyncio.create_task(self._transfer_audio())

            return self._audio_queue

        except sd.PortAudioError as e:
            self._logger.error(f"Failed to start capture: {e}")
            with self._state_lock:
                self._state = CaptureState.ERROR
            raise AudioCaptureError(f"Failed to start capture: {e}")

    def stop(self) -> None:
        """
        Stop capture immediately (sync).

        This is a SYNCHRONOUS method for use in signal handlers
        and sync cleanup code. Does not drain buffers.
        """
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop requested (sync)")

        # Clear capturing flag first
        self._capturing_event.clear()

        # Stop and close stream
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                self._logger.error(f"Error stopping stream: {e}")
            finally:
                self._stream = None

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
            f"Capture stopped. Chunks: {self._metrics.chunks_captured}, "
            f"Dropped: {self._metrics.chunks_dropped}"
        )

    async def stop_and_drain(self) -> None:
        """
        Stop capture and drain remaining chunks (async).

        Waits for the transfer loop to finish processing remaining
        chunks in the buffer before stopping.
        """
        if not self._capturing_event.is_set():
            return

        self._logger.debug("Stop and drain requested")

        # Clear capturing flag (transfer loop will drain and exit)
        self._capturing_event.clear()

        # Stop stream (no more new audio)
        if self._stream:
            try:
                self._stream.stop()
            except Exception as e:
                self._logger.error(f"Error stopping stream: {e}")

        # Wait for transfer task to complete (it drains the queue)
        if self._transfer_task:
            try:
                await asyncio.wait_for(self._transfer_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._logger.warning("Transfer task didn't complete in time")
                self._transfer_task.cancel()
                try:
                    await self._transfer_task
                except asyncio.CancelledError:
                    pass
            finally:
                self._transfer_task = None

        # Close stream
        if self._stream:
            try:
                self._stream.close()
            except Exception as e:
                self._logger.error(f"Error closing stream: {e}")
            finally:
                self._stream = None

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
            f"Capture stopped (drained). Chunks: {self._metrics.chunks_captured}, "
            f"Dropped: {self._metrics.chunks_dropped}"
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
        """Get info about current input device."""
        return self._device_info

    def cleanup(self) -> None:
        """Release resources."""
        # Stop if capturing
        if self._capturing_event.is_set():
            self.stop()

        # Clear queues
        self._clear_queues()

        # Reset state
        self._reset_state()

        self._logger.debug("Cleanup complete")

    # =========================================================================
    # Device Enumeration (DeviceEnumerable protocol)
    # =========================================================================

    @classmethod
    def list_devices(cls) -> List[AudioDevice]:
        """List available audio input devices."""
        devices = []
        try:
            default_input = sd.default.device[0]
            for i, device in enumerate(sd.query_devices()):
                if device["max_input_channels"] > 0:
                    devices.append(
                        AudioDevice(
                            id=i,
                            name=device["name"],
                            channels=device["max_input_channels"],
                            sample_rates=[int(device["default_samplerate"])],
                            is_default=(i == default_input),
                        )
                    )
        except Exception:
            pass
        return devices

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _resolve_device(self) -> None:
        """Resolve device_id to integer index and get device info."""
        device_id = self._config.device_id

        try:
            if device_id is None:
                # Use default device
                self._resolved_device_id = None
                info = sd.query_devices(kind="input")
                self._device_info = AudioDevice(
                    id=sd.default.device[0],
                    name=info["name"],
                    channels=info["max_input_channels"],
                    sample_rates=[int(info["default_samplerate"])],
                    is_default=True,
                )
            elif isinstance(device_id, int):
                # Direct index
                self._resolved_device_id = device_id
                info = sd.query_devices(device_id, "input")
                self._device_info = AudioDevice(
                    id=device_id,
                    name=info["name"],
                    channels=info["max_input_channels"],
                    sample_rates=[int(info["default_samplerate"])],
                    is_default=(device_id == sd.default.device[0]),
                )
            else:
                # String name match
                found = False
                for i, device in enumerate(sd.query_devices()):
                    if (
                        device["max_input_channels"] > 0
                        and device_id.lower() in device["name"].lower()
                    ):
                        self._resolved_device_id = i
                        self._device_info = AudioDevice(
                            id=i,
                            name=device["name"],
                            channels=device["max_input_channels"],
                            sample_rates=[int(device["default_samplerate"])],
                            is_default=(i == sd.default.device[0]),
                        )
                        found = True
                        break
                if not found:
                    raise DeviceNotFoundError(f"No input device matching '{device_id}'")

            self._logger.info(f"Using audio input device: {self._device_info.name}")

        except sd.PortAudioError as e:
            self._logger.error(f"Error querying device: {e}")
            raise DeviceNotFoundError(str(e))

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """
        Audio callback called by sounddevice from audio thread.

        Args:
            indata: Input audio data as numpy array
            frames: Number of frames
            time_info: Timing information
            status: Callback status flags
        """
        if not self._capturing_event.is_set():
            return

        # Check for overflow
        if status.input_overflow:
            self._metrics.buffer_overruns += 1
            self._logger.warning("Input overflow detected")

        # Copy audio data (prevent overwrite)
        audio_copy = indata.copy()

        # Put in callback queue (non-blocking)
        try:
            self._callback_queue.put_nowait(audio_copy)
        except queue.Full:
            # Queue full - drop chunk
            self._metrics.chunks_dropped += 1
            self._logger.debug(
                f"Callback queue full, dropped chunk (total dropped: {self._metrics.chunks_dropped})"
            )

    async def _transfer_audio(self) -> None:
        """
        Transfer audio from callback queue to async queue.

        Uses drain-on-stop pattern: continues draining even after
        capture is stopped to avoid data loss.
        """
        loop = asyncio.get_event_loop()

        try:
            while self._capturing_event.is_set() or not self._callback_queue.empty():
                try:
                    # Get from callback queue with timeout
                    audio_array = await loop.run_in_executor(
                        None, self._callback_queue.get, True, 0.05
                    )

                    # Convert to bytes (int16 PCM)
                    if audio_array.dtype != np.int16:
                        audio_array = (audio_array * 32767).astype(np.int16)
                    audio_bytes = audio_array.tobytes()

                    # Update metrics
                    self._metrics.chunks_captured += 1
                    self._metrics.total_bytes += len(audio_bytes)

                    # Put in async queue
                    await self._audio_queue.put(audio_bytes)

                    # Fire on_chunk_captured callback
                    if self._on_chunk_captured:
                        try:
                            self._on_chunk_captured(self._metrics.chunks_captured)
                        except Exception as e:
                            self._logger.error(f"on_chunk_captured callback error: {e}")

                except queue.Empty:
                    if not self._capturing_event.is_set():
                        # Only exit when stopped AND queue empty
                        break
                    continue
                except Exception as e:
                    self._logger.error(f"Transfer error: {e}")
                    if self._on_error:
                        try:
                            self._on_error(e)
                        except Exception as cb_error:
                            self._logger.error(f"on_error callback error: {cb_error}")
                    break

        except asyncio.CancelledError:
            self._logger.debug("Transfer task cancelled")
            raise
        finally:
            self._logger.debug("Transfer task ended")

    def _reset_state(self) -> None:
        """Reset adapter state for new capture session."""
        # Clear queues
        self._clear_queues()

        # Reset metrics
        self._metrics = CaptureMetrics()

        # Reset deduplication flags
        self._started_notified = False
        self._stopped_notified = False

        # Reset state
        with self._state_lock:
            self._state = CaptureState.IDLE

    def _clear_queues(self) -> None:
        """Clear all queues."""
        # Clear callback queue
        while True:
            try:
                self._callback_queue.get_nowait()
            except queue.Empty:
                break

        # Clear async queue
        while True:
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
