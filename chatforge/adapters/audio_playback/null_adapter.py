"""
Null Playback Adapter.

Discards all audio data - useful for testing without actual playback.
Still tracks metrics and fires callbacks for proper test coverage.

Example:
    from chatforge.adapters.audio_playback import NullPlaybackAdapter

    player = NullPlaybackAdapter()
    player.set_callbacks(on_complete=lambda: print("Done!"))

    for chunk in audio_chunks:
        player.play(chunk)

    player.mark_complete()
    assert player.get_metrics().chunks_played == len(audio_chunks)
"""

import asyncio
import logging
import threading
import time
from typing import Optional

from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    AudioPlaybackPort,
    OutputDevice,
    PlaybackMetrics,
    PlaybackState,
)


__all__ = ["NullPlaybackAdapter"]


class NullPlaybackAdapter(AudioPlaybackPort):
    """
    Null audio playback adapter for testing.

    Discards all audio data but tracks metrics and fires callbacks.
    Useful for:
        - Unit testing without audio hardware
        - Integration testing without sound output
        - Benchmarking audio processing pipelines

    Thread Safety:
        - play() can be called from any thread
        - Metrics updates are protected by lock

    Example:
        player = NullPlaybackAdapter()
        player.set_callbacks(on_started=..., on_complete=...)

        for chunk in audio_stream:
            player.play(chunk)

        player.mark_complete()
        metrics = player.get_metrics()
        assert metrics.chunks_played > 0
    """

    def __init__(
        self,
        config: Optional[AudioPlaybackConfig] = None,
        logger: Optional[logging.Logger] = None,
        simulate_playback_time: bool = False,
    ) -> None:
        """
        Initialize null playback adapter.

        Args:
            config: Audio configuration (used for metrics calculation)
            logger: Optional logger
            simulate_playback_time: If True, sleep for audio duration to simulate real playback
        """
        self._config = config or AudioPlaybackConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._simulate_playback_time = simulate_playback_time

        # Pre-computed values
        self._bytes_per_ms = self._config.bytes_per_ms

        # State management
        self._state = PlaybackState.IDLE
        self._state_lock = threading.Lock()
        self._is_complete = False
        self._completion_event = threading.Event()

        # Metrics
        self._metrics = PlaybackMetrics()
        self._metrics_lock = threading.Lock()

        # Callback deduplication
        self._started_notified = False
        self._complete_notified = False

        # Callbacks
        self._on_started: Optional[callable] = None
        self._on_complete: Optional[callable] = None
        self._on_buffer_low: Optional[callable] = None
        self._on_error: Optional[callable] = None
        self._on_chunk_played: Optional[callable] = None

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
        """True if in playing state."""
        with self._state_lock:
            return self._state in (PlaybackState.PLAYING, PlaybackState.DRAINING)

    @property
    def is_actively_outputting(self) -> bool:
        """Always False for null adapter (no actual output)."""
        return False

    @property
    def buffer_duration_ms(self) -> float:
        """Always 0 for null adapter (no buffering)."""
        return 0.0

    # =========================================================================
    # Core Methods
    # =========================================================================

    def play(self, audio_data: bytes) -> bool:
        """
        Accept and discard audio data.

        Args:
            audio_data: PCM audio bytes (discarded)

        Returns:
            True always (null adapter never rejects)
        """
        if self._is_complete:
            self._logger.warning("play() called after mark_complete()")
            return False

        with self._metrics_lock:
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

            # Update metrics (data is discarded)
            self._metrics.chunks_received += 1
            self._metrics.chunks_played += 1
            self._metrics.total_bytes_received += len(audio_data)
            self._metrics.total_bytes_played += len(audio_data)

        # Simulate playback time if requested
        if self._simulate_playback_time and self._bytes_per_ms > 0:
            duration_ms = len(audio_data) / self._bytes_per_ms
            time.sleep(duration_ms / 1000.0)

        # Fire on_chunk_played callback
        if self._on_chunk_played:
            try:
                self._on_chunk_played(1)
            except Exception as e:
                self._logger.error(f"on_chunk_played callback error: {e}")

        self._logger.debug(
            f"Null adapter received chunk {self._metrics.chunks_received} "
            f"({len(audio_data)} bytes)"
        )

        return True

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
            f"Null adapter complete: {self._metrics.chunks_played} chunks, "
            f"{self._metrics.total_bytes_played} bytes discarded"
        )

    def stop(self, force: bool = False) -> None:
        """
        Stop playback (reset state).

        Args:
            force: Ignored for null adapter
        """
        with self._state_lock:
            self._state = PlaybackState.IDLE
        self._is_complete = False
        self._started_notified = False
        self._complete_notified = False
        self._completion_event.clear()

    def wait_until_complete_sync(self, timeout: float = 30.0) -> bool:
        """
        Wait for completion.

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
        with self._metrics_lock:
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
        """No device for null adapter."""
        return None

    def cleanup(self) -> None:
        """No resources to clean up."""
        self._logger.debug("Null adapter cleaned up")

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def reset(self) -> None:
        """
        Reset adapter for reuse in tests.

        Clears all state and metrics.
        """
        self.stop()
        with self._metrics_lock:
            self._metrics = PlaybackMetrics()
        self._completion_event.clear()
        self._logger.debug("Null adapter reset")
