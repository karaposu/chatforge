"""
SoundDevice Playback Adapter.

Primary adapter using buffered/batching pattern for audio playback.
This matches VoxStream's BufferedAudioPlayer behavior.

Features:
    - Thread-based playback loop
    - Smart buffering with min_buffer_chunks threshold
    - Batch playback via sd.play() blocking calls
    - Proper completion detection and callbacks
    - Callback deduplication (_started_notified, _complete_notified)

Example:
    from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
    from chatforge.ports.audio_playback import AudioPlaybackConfig

    player = SoundDevicePlaybackAdapter(AudioPlaybackConfig(sample_rate=24000))
    player.set_callbacks(
        on_started=lambda: print("Playing..."),
        on_complete=lambda: print("Done!"),
    )

    for chunk in audio_chunks:
        player.play(chunk)

    player.mark_complete()
    player.wait_until_complete_sync()
    player.cleanup()
"""

import asyncio
import logging
import threading
import time
from typing import Callable, List, Optional

import numpy as np
import sounddevice as sd

from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    AudioPlaybackPort,
    DeviceEnumerable,
    DeviceNotFoundError,
    OutputDevice,
    PlaybackMetrics,
    PlaybackState,
)


__all__ = ["SoundDevicePlaybackAdapter"]


class SoundDevicePlaybackAdapter(AudioPlaybackPort, DeviceEnumerable):
    """
    Audio playback using sounddevice library with buffered/batching pattern.

    This is the primary adapter for VoxStream integration.

    Features:
        - Smart buffering with min_buffer_chunks threshold
        - Batch playback for efficiency
        - Thread-based playback loop
        - Proper completion detection
        - Callback deduplication (fires exactly once per session)

    Thread Safety:
        - play() can be called from any thread
        - Callbacks fire from playback thread
        - State transitions are protected by locks

    Example:
        player = SoundDevicePlaybackAdapter()
        player.set_callbacks(on_complete=lambda: print("Done"))

        for chunk in audio_stream:
            player.play(chunk)

        player.mark_complete()
        player.wait_until_complete_sync()
    """

    # Default batch size for playback
    MAX_BATCH_CHUNKS = 5

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize SoundDevice playback adapter.

        Args:
            config: Audio playback configuration. Uses defaults if not provided.
            logger: Optional logger for debugging.
        """
        self._config = config or AudioPlaybackConfig()
        self._logger = logger or logging.getLogger(__name__)

        # Pre-computed values
        self._bytes_per_ms = self._config.bytes_per_ms

        # Buffer management
        self._buffer: List[bytes] = []
        self._buffer_lock = threading.Lock()

        # State management
        self._state = PlaybackState.IDLE
        self._state_lock = threading.Lock()
        self._is_complete = False

        # Playback thread
        self._play_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._completion_event = threading.Event()

        # Metrics
        self._metrics = PlaybackMetrics()

        # Callback deduplication flags (CRITICAL for VoxStream integration)
        self._started_notified = False
        self._complete_notified = False

        # Callbacks (set by set_callbacks)
        self._on_started: Optional[Callable[[], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None
        self._on_buffer_low: Optional[Callable[[], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
        self._on_chunk_played: Optional[Callable[[int], None]] = None

        # Device info
        self._resolved_device_id: Optional[int] = None
        self._device_info: Optional[OutputDevice] = None
        self._resolve_device()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        with self._state_lock:
            return self._state

    @property
    def config(self) -> AudioPlaybackConfig:
        """Current configuration."""
        return self._config

    @property
    def is_playing(self) -> bool:
        """True if in PLAYING or DRAINING state."""
        with self._state_lock:
            return self._state in (PlaybackState.PLAYING, PlaybackState.DRAINING)

    @property
    def is_actively_outputting(self) -> bool:
        """True if audio is actually being output right now."""
        with self._state_lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.DRAINING):
                return False
        with self._buffer_lock:
            return len(self._buffer) > 0

    @property
    def buffer_duration_ms(self) -> float:
        """Current buffer duration in milliseconds."""
        with self._buffer_lock:
            total_bytes = sum(len(chunk) for chunk in self._buffer)
        return total_bytes / self._bytes_per_ms if self._bytes_per_ms > 0 else 0.0

    # =========================================================================
    # Core Methods
    # =========================================================================

    def play(self, audio_data: bytes) -> bool:
        """
        Queue audio for playback.

        Args:
            audio_data: PCM audio bytes to play

        Returns:
            True if queued successfully, False if buffer full
        """
        # Check buffer limit
        current_duration = self.buffer_duration_ms
        new_duration = len(audio_data) / self._bytes_per_ms
        if current_duration + new_duration > self._config.max_buffer_ms:
            self._logger.warning(
                f"Buffer full: {current_duration:.0f}ms + {new_duration:.0f}ms > {self._config.max_buffer_ms}ms"
            )
            return False

        with self._buffer_lock:
            # Track first chunk time
            if self._metrics.chunks_received == 0:
                self._metrics.first_chunk_time = time.time()
                self._logger.debug("First audio chunk received")

            # Add to buffer
            self._buffer.append(audio_data)

            # Update metrics
            self._metrics.chunks_received += 1
            self._metrics.total_bytes_received += len(audio_data)

            self._logger.debug(
                f"Chunk {self._metrics.chunks_received} added to buffer "
                f"(size: {len(self._buffer)}, duration: {self.buffer_duration_ms:.0f}ms)"
            )

        # Start playback if not already running
        if self._play_thread is None or not self._play_thread.is_alive():
            self._start_playback()

        return True

    def mark_complete(self) -> None:
        """Mark that all audio has been sent."""
        self._is_complete = True
        with self._state_lock:
            if self._state == PlaybackState.PLAYING:
                self._state = PlaybackState.DRAINING
        self._logger.info(f"Audio reception complete. Total chunks: {self._metrics.chunks_received}")

    def stop(self, force: bool = False) -> None:
        """
        Stop playback.

        Args:
            force: If True, stop immediately discarding buffer (barge-in).
        """
        self._logger.debug(f"Stop requested (force={force})")

        # Set stop flag
        self._stop_flag.set()

        if force:
            # Force stop sounddevice
            try:
                sd.stop()
                self._logger.debug("Force stopped sounddevice")
            except Exception as e:
                self._logger.error(f"Error force stopping: {e}")

            # Clear buffer immediately
            with self._buffer_lock:
                self._buffer.clear()

        # Wait for thread to finish
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=1.0)

        # Clear buffer
        with self._buffer_lock:
            self._buffer.clear()

        # Reset state
        with self._state_lock:
            self._state = PlaybackState.IDLE
        self._is_complete = False

        # Reset deduplication flags for next session
        self._started_notified = False
        self._complete_notified = False

        # Reset metrics timing for next session
        self._metrics.playback_start_time = None
        self._metrics.playback_end_time = None

        self._logger.info("Playback stopped")

    def wait_until_complete_sync(self, timeout: float = 30.0) -> bool:
        """
        Wait synchronously until all queued audio has been played.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        return self._completion_event.wait(timeout=timeout)

    async def wait_until_complete(self, timeout: float = 30.0) -> bool:
        """
        Wait asynchronously until all queued audio has been played.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        loop = asyncio.get_event_loop()
        # Pass timeout to wait() directly to avoid dangling threads
        return await loop.run_in_executor(
            None, self._completion_event.wait, timeout
        )

    def get_metrics(self) -> PlaybackMetrics:
        """Get playback performance metrics."""
        with self._buffer_lock:
            self._metrics.chunks_buffered = len(self._buffer)
            self._metrics.buffer_duration_ms = self.buffer_duration_ms

        # Calculate playback duration
        if self._metrics.playback_start_time:
            if self._metrics.playback_end_time:
                self._metrics.playback_duration_seconds = (
                    self._metrics.playback_end_time - self._metrics.playback_start_time
                )
            else:
                self._metrics.playback_duration_seconds = (
                    time.time() - self._metrics.playback_start_time
                )

        return PlaybackMetrics(
            chunks_received=self._metrics.chunks_received,
            chunks_played=self._metrics.chunks_played,
            chunks_buffered=self._metrics.chunks_buffered,
            total_bytes_received=self._metrics.total_bytes_received,
            total_bytes_played=self._metrics.total_bytes_played,
            buffer_duration_ms=self._metrics.buffer_duration_ms,
            playback_duration_seconds=self._metrics.playback_duration_seconds,
            first_chunk_time=self._metrics.first_chunk_time,
            playback_start_time=self._metrics.playback_start_time,
            playback_end_time=self._metrics.playback_end_time,
            underruns=self._metrics.underruns,
        )

    def get_device_info(self) -> Optional[OutputDevice]:
        """Get info about current output device."""
        return self._device_info

    def cleanup(self) -> None:
        """Release resources."""
        self.stop(force=True)
        self._logger.debug("Cleanup complete")

    # =========================================================================
    # Device Enumeration (DeviceEnumerable protocol)
    # =========================================================================

    @classmethod
    def list_devices(cls) -> List[OutputDevice]:
        """List available audio output devices."""
        devices = []
        try:
            default_output = sd.default.device[1]
            for i, device in enumerate(sd.query_devices()):
                if device["max_output_channels"] > 0:
                    devices.append(
                        OutputDevice(
                            id=i,
                            name=device["name"],
                            channels=device["max_output_channels"],
                            sample_rates=[int(device["default_samplerate"])],
                            is_default=(i == default_output),
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
                info = sd.query_devices(kind="output")
                self._device_info = OutputDevice(
                    id=sd.default.device[1],
                    name=info["name"],
                    channels=info["max_output_channels"],
                    sample_rates=[int(info["default_samplerate"])],
                    is_default=True,
                )
            elif isinstance(device_id, int):
                # Direct index
                self._resolved_device_id = device_id
                info = sd.query_devices(device_id, "output")
                self._device_info = OutputDevice(
                    id=device_id,
                    name=info["name"],
                    channels=info["max_output_channels"],
                    sample_rates=[int(info["default_samplerate"])],
                    is_default=(device_id == sd.default.device[1]),
                )
            else:
                # String name match
                found = False
                for i, device in enumerate(sd.query_devices()):
                    if (
                        device["max_output_channels"] > 0
                        and device_id.lower() in device["name"].lower()
                    ):
                        self._resolved_device_id = i
                        self._device_info = OutputDevice(
                            id=i,
                            name=device["name"],
                            channels=device["max_output_channels"],
                            sample_rates=[int(device["default_samplerate"])],
                            is_default=(i == sd.default.device[1]),
                        )
                        found = True
                        break
                if not found:
                    raise DeviceNotFoundError(f"No output device matching '{device_id}'")

            self._logger.info(f"Using audio output device: {self._device_info.name}")

        except sd.PortAudioError as e:
            self._logger.error(f"Error querying device: {e}")
            raise DeviceNotFoundError(str(e))

    def _start_playback(self) -> None:
        """Start playback thread."""
        with self._state_lock:
            if self._state not in (PlaybackState.IDLE, PlaybackState.ERROR):
                return
            self._state = PlaybackState.BUFFERING

        self._is_complete = False
        self._stop_flag.clear()
        self._completion_event.clear()

        # Reset deduplication flags for new session
        self._started_notified = False
        self._complete_notified = False

        self._logger.info("Starting playback thread")

        self._play_thread = threading.Thread(
            target=self._playback_loop,
            name="SoundDevicePlayback",
            daemon=True,
        )
        self._play_thread.start()

    def _playback_loop(self) -> None:
        """Buffered playback loop."""
        self._logger.debug("Playback loop started")

        try:
            # Set device if specified
            if self._resolved_device_id is not None:
                sd.default.device = (None, self._resolved_device_id)

            while not self._stop_flag.is_set():
                # Check buffer status
                with self._buffer_lock:
                    buffer_size = len(self._buffer)
                    can_play = (
                        buffer_size >= self._config.min_buffer_chunks
                        or (self._is_complete and buffer_size > 0)
                    )

                if can_play:
                    # Determine how many chunks to play
                    with self._buffer_lock:
                        if self._is_complete:
                            num_chunks = len(self._buffer)
                        else:
                            num_chunks = min(self.MAX_BATCH_CHUNKS, len(self._buffer))

                        # Extract chunks
                        chunks_to_play = []
                        for _ in range(num_chunks):
                            if self._buffer:
                                chunks_to_play.append(self._buffer.pop(0))

                    if chunks_to_play:
                        # Mark first playback
                        if self._metrics.playback_start_time is None:
                            self._metrics.playback_start_time = time.time()
                            with self._state_lock:
                                self._state = PlaybackState.PLAYING
                            self._logger.info("Playback started")

                            # Fire on_started callback ONCE
                            if not self._started_notified and self._on_started:
                                self._started_notified = True
                                try:
                                    self._on_started()
                                except Exception as e:
                                    self._logger.error(f"on_started callback error: {e}")

                        # Combine chunks
                        audio_data = b"".join(chunks_to_play)
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)

                        # Play audio
                        try:
                            self._logger.debug(
                                f"Playing {len(chunks_to_play)} chunks ({len(audio_data)} bytes)"
                            )
                            sd.play(audio_array, self._config.sample_rate, blocking=True)

                            # Update metrics
                            self._metrics.chunks_played += len(chunks_to_play)
                            self._metrics.total_bytes_played += len(audio_data)

                            # Fire on_chunk_played callback
                            if self._on_chunk_played:
                                try:
                                    self._on_chunk_played(len(chunks_to_play))
                                except Exception as e:
                                    self._logger.error(f"on_chunk_played callback error: {e}")

                        except Exception as e:
                            self._logger.error(f"Playback error: {e}")
                            self._metrics.underruns += 1
                            if self._on_error:
                                try:
                                    self._on_error(e)
                                except Exception as cb_error:
                                    self._logger.error(f"on_error callback error: {cb_error}")

                # Check if we're done
                with self._buffer_lock:
                    is_done = self._is_complete and len(self._buffer) == 0

                if is_done:
                    self._logger.info("All audio played, ending playback")
                    self._metrics.playback_end_time = time.time()

                    with self._state_lock:
                        self._state = PlaybackState.IDLE

                    # Fire on_complete callback ONCE
                    if not self._complete_notified and self._on_complete:
                        self._complete_notified = True
                        try:
                            self._on_complete()
                        except Exception as e:
                            self._logger.error(f"on_complete callback error: {e}")

                    # Signal completion
                    self._completion_event.set()
                    break

                # If not enough to play, wait a bit
                if not can_play:
                    time.sleep(0.02)  # 20ms wait

        except Exception as e:
            self._logger.error(f"Playback loop error: {e}", exc_info=True)
            with self._state_lock:
                self._state = PlaybackState.ERROR
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception as cb_error:
                    self._logger.error(f"on_error callback error: {cb_error}")
        finally:
            self._logger.debug("Playback loop ended")
