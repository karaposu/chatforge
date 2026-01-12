"""
File Sink Adapter.

Writes audio data to a WAV file instead of playing it.
Useful for debugging, testing, and audio capture.

Note: This is a "sink" not a "player" - it writes to file rather than
outputting to speakers. It implements the same interface for consistency.

Example:
    from chatforge.adapters.audio_playback import FileSinkAdapter
    from chatforge.ports.audio_playback import AudioPlaybackConfig

    with FileSinkAdapter("output.wav", AudioPlaybackConfig(sample_rate=24000)) as sink:
        for chunk in audio_chunks:
            sink.play(chunk)
        sink.mark_complete()
"""

import asyncio
import logging
import threading
import time
import wave
from pathlib import Path
from typing import Optional, Union

from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    AudioPlaybackError,
    AudioPlaybackPort,
    OutputDevice,
    PlaybackMetrics,
    PlaybackState,
)


__all__ = ["FileSinkAdapter"]


class FileSinkAdapter(AudioPlaybackPort):
    """
    Audio sink that writes to a WAV file.

    This adapter writes audio data to a file instead of playing it.
    Useful for debugging, testing, and audio capture.

    Note:
        This is a "sink" not a "player". The play() method writes to file
        rather than outputting audio to speakers.

    Thread Safety:
        - play() can be called from any thread
        - File writes are protected by a lock

    Example:
        sink = FileSinkAdapter("output.wav")
        for chunk in audio_chunks:
            sink.play(chunk)
        sink.mark_complete()
        sink.cleanup()  # Finalizes WAV file
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        config: Optional[AudioPlaybackConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize file sink adapter.

        Args:
            file_path: Path to output WAV file
            config: Audio configuration (sample_rate, channels, bit_depth)
            logger: Optional logger

        Raises:
            AudioPlaybackError: If file cannot be opened for writing
        """
        self._config = config or AudioPlaybackConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._file_path = Path(file_path)

        # State management
        self._state = PlaybackState.IDLE
        self._state_lock = threading.Lock()
        self._is_complete = False
        self._completion_event = threading.Event()

        # File writing
        self._file_lock = threading.Lock()
        self._wav_file: Optional[wave.Wave_write] = None

        # Metrics
        self._metrics = PlaybackMetrics()

        # Callback deduplication
        self._started_notified = False
        self._complete_notified = False

        # Callbacks
        self._on_started: Optional[callable] = None
        self._on_complete: Optional[callable] = None
        self._on_buffer_low: Optional[callable] = None
        self._on_error: Optional[callable] = None
        self._on_chunk_played: Optional[callable] = None

        # Open file for writing
        self._open_file()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> PlaybackState:
        """Current state."""
        with self._state_lock:
            return self._state

    @property
    def config(self) -> AudioPlaybackConfig:
        """Current configuration."""
        return self._config

    @property
    def is_playing(self) -> bool:
        """True if actively writing."""
        with self._state_lock:
            return self._state in (PlaybackState.PLAYING, PlaybackState.DRAINING)

    @property
    def is_actively_outputting(self) -> bool:
        """True if actively writing (same as is_playing for file sink)."""
        return self.is_playing

    @property
    def buffer_duration_ms(self) -> float:
        """Always 0 for file sink (no buffering)."""
        return 0.0

    @property
    def file_path(self) -> Path:
        """Path to output file."""
        return self._file_path

    # =========================================================================
    # Core Methods
    # =========================================================================

    def play(self, audio_data: bytes) -> bool:
        """
        Write audio data to file.

        Args:
            audio_data: PCM audio bytes to write

        Returns:
            True if written successfully, False if error or already complete
        """
        if self._is_complete:
            self._logger.warning("play() called after mark_complete()")
            return False

        with self._file_lock:
            if self._wav_file is None:
                return False

            try:
                # Track first chunk
                if self._metrics.chunks_received == 0:
                    self._metrics.first_chunk_time = time.time()
                    self._metrics.playback_start_time = time.time()

                    with self._state_lock:
                        self._state = PlaybackState.PLAYING

                    # Fire on_started callback ONCE
                    if not self._started_notified and self._on_started:
                        self._started_notified = True
                        try:
                            self._on_started()
                        except Exception as e:
                            self._logger.error(f"on_started callback error: {e}")

                # Write to file
                self._wav_file.writeframes(audio_data)

                # Update metrics
                self._metrics.chunks_received += 1
                self._metrics.chunks_played += 1
                self._metrics.total_bytes_received += len(audio_data)
                self._metrics.total_bytes_played += len(audio_data)

                self._logger.debug(
                    f"Wrote chunk {self._metrics.chunks_received} ({len(audio_data)} bytes)"
                )

                # Fire on_chunk_played callback
                if self._on_chunk_played:
                    try:
                        self._on_chunk_played(1)
                    except Exception as e:
                        self._logger.error(f"on_chunk_played callback error: {e}")

                return True

            except Exception as e:
                self._logger.error(f"Error writing to file: {e}")
                with self._state_lock:
                    self._state = PlaybackState.ERROR
                if self._on_error:
                    try:
                        self._on_error(e)
                    except Exception as cb_error:
                        self._logger.error(f"on_error callback error: {cb_error}")
                return False

    def mark_complete(self) -> None:
        """Mark that all audio has been sent."""
        self._is_complete = True
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

        self._completion_event.set()
        self._logger.info(
            f"File sink complete: {self._metrics.chunks_played} chunks, "
            f"{self._metrics.total_bytes_played} bytes written to {self._file_path}"
        )

    def stop(self, force: bool = False) -> None:
        """
        Stop writing (for consistency with interface).

        Args:
            force: Ignored for file sink
        """
        with self._state_lock:
            self._state = PlaybackState.IDLE
        self._is_complete = False
        self._started_notified = False
        self._complete_notified = False

    def wait_until_complete_sync(self, timeout: float = 30.0) -> bool:
        """
        Wait for completion (instant for file sink).

        Returns:
            True if complete
        """
        return self._completion_event.wait(timeout=timeout)

    async def wait_until_complete(self, timeout: float = 30.0) -> bool:
        """
        Wait asynchronously for completion.

        Returns:
            True if complete
        """
        loop = asyncio.get_event_loop()
        # Pass timeout to wait() directly to avoid dangling threads
        return await loop.run_in_executor(
            None, self._completion_event.wait, timeout
        )

    def get_metrics(self) -> PlaybackMetrics:
        """Get metrics."""
        if self._metrics.playback_start_time and self._metrics.playback_end_time:
            self._metrics.playback_duration_seconds = (
                self._metrics.playback_end_time - self._metrics.playback_start_time
            )
        return PlaybackMetrics(
            chunks_received=self._metrics.chunks_received,
            chunks_played=self._metrics.chunks_played,
            chunks_buffered=0,
            total_bytes_received=self._metrics.total_bytes_received,
            total_bytes_played=self._metrics.total_bytes_played,
            buffer_duration_ms=0.0,
            playback_duration_seconds=self._metrics.playback_duration_seconds,
            first_chunk_time=self._metrics.first_chunk_time,
            playback_start_time=self._metrics.playback_start_time,
            playback_end_time=self._metrics.playback_end_time,
            underruns=0,
        )

    def get_device_info(self) -> Optional[OutputDevice]:
        """No device for file sink."""
        return None

    def cleanup(self) -> None:
        """Close file and release resources."""
        self._close_file()
        self._logger.debug(f"File sink cleaned up: {self._file_path}")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _open_file(self) -> None:
        """Open WAV file for writing."""
        try:
            # Ensure parent directory exists
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            self._wav_file = wave.open(str(self._file_path), "wb")
            self._wav_file.setnchannels(self._config.channels)
            self._wav_file.setsampwidth(self._config.bytes_per_sample)
            self._wav_file.setframerate(self._config.sample_rate)

            self._logger.info(
                f"Opened WAV file for writing: {self._file_path} "
                f"({self._config.sample_rate}Hz, {self._config.channels}ch, "
                f"{self._config.bit_depth}bit)"
            )

        except Exception as e:
            self._logger.error(f"Failed to open WAV file: {e}")
            raise AudioPlaybackError(f"Failed to open WAV file: {e}")

    def _close_file(self) -> None:
        """Close WAV file."""
        with self._file_lock:
            if self._wav_file:
                try:
                    self._wav_file.close()
                    self._logger.debug(f"Closed WAV file: {self._file_path}")
                except Exception as e:
                    self._logger.error(f"Error closing WAV file: {e}")
                finally:
                    self._wav_file = None
