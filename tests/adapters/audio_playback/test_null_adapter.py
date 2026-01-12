"""
Unit tests for NullPlaybackAdapter.

Tests state machine, callbacks, metrics, and threading behavior.
"""

import pytest
import threading
import time
from typing import List

from chatforge.adapters.audio_playback import NullPlaybackAdapter
from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    PlaybackState,
)

from tests.adapters.audio_playback.fixtures import (
    generate_tone,
    generate_silence,
    chunk_audio,
    generate_audio_sequence,
)


# =============================================================================
# Basic State Tests
# =============================================================================


class TestNullAdapterBasicState:
    """Test basic adapter state behavior."""

    def test_initial_state_is_idle(self):
        """Adapter should start in IDLE state."""
        adapter = NullPlaybackAdapter()
        assert adapter.state == PlaybackState.IDLE
        assert not adapter.is_playing

    def test_play_transitions_to_playing(self):
        """First play() call should transition to PLAYING."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)

        assert adapter.state == PlaybackState.PLAYING
        assert adapter.is_playing

    def test_mark_complete_transitions_to_idle(self):
        """mark_complete() should transition to IDLE."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        adapter.mark_complete()

        assert adapter.state == PlaybackState.IDLE
        assert not adapter.is_playing

    def test_stop_resets_state(self):
        """stop() should reset to IDLE."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        assert adapter.state == PlaybackState.PLAYING

        adapter.stop()
        assert adapter.state == PlaybackState.IDLE

    def test_play_after_mark_complete_rejected(self):
        """play() after mark_complete() should return False."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        adapter.mark_complete()

        result = adapter.play(audio)
        assert result is False


# =============================================================================
# Callback Tests
# =============================================================================


class TestNullAdapterCallbacks:
    """Test callback behavior."""

    def test_on_started_fires_once(self):
        """on_started should fire exactly once."""
        adapter = NullPlaybackAdapter()
        started_count = []

        adapter.set_callbacks(on_started=lambda: started_count.append(1))

        # Play multiple chunks
        chunks = generate_audio_sequence(500, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)

        assert len(started_count) == 1

    def test_on_complete_fires_once(self):
        """on_complete should fire exactly once on mark_complete()."""
        adapter = NullPlaybackAdapter()
        complete_count = []

        adapter.set_callbacks(on_complete=lambda: complete_count.append(1))

        chunks = generate_audio_sequence(300, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)

        adapter.mark_complete()

        assert len(complete_count) == 1

    def test_on_chunk_played_fires_for_each_chunk(self):
        """on_chunk_played should fire for each chunk."""
        adapter = NullPlaybackAdapter()
        chunk_counts = []

        adapter.set_callbacks(on_chunk_played=lambda count: chunk_counts.append(count))

        chunks = generate_audio_sequence(300, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)

        assert len(chunk_counts) == 3
        assert all(c == 1 for c in chunk_counts)

    def test_callbacks_not_fired_without_play(self):
        """Callbacks should not fire if no audio played."""
        adapter = NullPlaybackAdapter()
        started = []
        complete = []

        adapter.set_callbacks(
            on_started=lambda: started.append(1),
            on_complete=lambda: complete.append(1),
        )

        adapter.mark_complete()

        assert len(started) == 0
        # on_complete still fires on mark_complete
        assert len(complete) == 1

    def test_callback_exception_is_caught(self):
        """Callback exceptions should not propagate."""
        adapter = NullPlaybackAdapter()

        def bad_callback():
            raise ValueError("Test error")

        adapter.set_callbacks(on_started=bad_callback)

        # Should not raise
        audio = generate_tone(100)
        adapter.play(audio)

        assert adapter.state == PlaybackState.PLAYING


# =============================================================================
# Metrics Tests
# =============================================================================


class TestNullAdapterMetrics:
    """Test metrics tracking."""

    def test_chunks_received_increments(self):
        """chunks_received should increment for each play() call."""
        adapter = NullPlaybackAdapter()

        chunks = generate_audio_sequence(300, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)

        metrics = adapter.get_metrics()
        assert metrics.chunks_received == 3

    def test_chunks_played_equals_received(self):
        """For null adapter, chunks_played == chunks_received (instant)."""
        adapter = NullPlaybackAdapter()

        chunks = generate_audio_sequence(300, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)

        metrics = adapter.get_metrics()
        assert metrics.chunks_played == metrics.chunks_received

    def test_bytes_tracked(self):
        """Total bytes should be tracked."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)  # 100ms at 24kHz, 16-bit mono = 4800 bytes

        adapter.play(audio)

        metrics = adapter.get_metrics()
        assert metrics.total_bytes_received == 4800
        assert metrics.total_bytes_played == 4800

    def test_timing_metrics_set(self):
        """Timing metrics should be set after play and complete."""
        adapter = NullPlaybackAdapter()

        audio = generate_tone(100)
        adapter.play(audio)

        metrics = adapter.get_metrics()
        assert metrics.first_chunk_time is not None
        assert metrics.playback_start_time is not None

        adapter.mark_complete()
        metrics = adapter.get_metrics()
        assert metrics.playback_end_time is not None

    def test_initial_latency_calculated(self):
        """initial_latency_ms should be calculated after playback starts."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)

        metrics = adapter.get_metrics()
        # For null adapter, initial latency should be nearly 0
        assert metrics.initial_latency_ms is not None
        assert metrics.initial_latency_ms < 100  # Should be very fast

    def test_buffer_always_zero(self):
        """Buffer duration should always be 0 for null adapter."""
        adapter = NullPlaybackAdapter()

        adapter.play(generate_tone(100))

        assert adapter.buffer_duration_ms == 0.0
        metrics = adapter.get_metrics()
        assert metrics.buffer_duration_ms == 0.0


# =============================================================================
# Wait Tests
# =============================================================================


class TestNullAdapterWait:
    """Test wait functionality."""

    def test_wait_returns_true_after_complete(self):
        """wait_until_complete_sync should return True after mark_complete."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        adapter.mark_complete()

        result = adapter.wait_until_complete_sync(timeout=1.0)
        assert result is True

    def test_wait_returns_false_on_timeout(self):
        """wait_until_complete_sync should return False on timeout."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        # Don't call mark_complete

        result = adapter.wait_until_complete_sync(timeout=0.1)
        assert result is False

    @pytest.mark.asyncio
    async def test_async_wait_returns_true(self):
        """async wait_until_complete should return True after mark_complete."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        adapter.mark_complete()

        result = await adapter.wait_until_complete(timeout=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_wait_returns_false_on_timeout(self):
        """async wait_until_complete should return False on timeout."""
        adapter = NullPlaybackAdapter()
        audio = generate_tone(100)

        adapter.play(audio)
        # Don't call mark_complete

        result = await adapter.wait_until_complete(timeout=0.1)
        assert result is False


# =============================================================================
# Threading Tests
# =============================================================================


class TestNullAdapterThreading:
    """Test thread safety."""

    def test_play_from_multiple_threads(self):
        """play() should be safe from multiple threads."""
        adapter = NullPlaybackAdapter()
        chunks = generate_audio_sequence(1000, chunk_ms=50)
        errors = []

        def play_chunks(thread_id: int):
            try:
                for i, chunk in enumerate(chunks):
                    if i % 2 == thread_id % 2:  # Interleave
                        adapter.play(chunk)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=play_chunks, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # All chunks should have been played
        metrics = adapter.get_metrics()
        assert metrics.chunks_played > 0


# =============================================================================
# Reset Tests
# =============================================================================


class TestNullAdapterReset:
    """Test reset behavior."""

    def test_reset_clears_metrics(self):
        """reset() should clear all metrics."""
        adapter = NullPlaybackAdapter()

        chunks = generate_audio_sequence(300, chunk_ms=100)
        for chunk in chunks:
            adapter.play(chunk)
        adapter.mark_complete()

        assert adapter.get_metrics().chunks_played == 3

        adapter.reset()

        assert adapter.get_metrics().chunks_played == 0
        assert adapter.get_metrics().chunks_received == 0
        assert adapter.state == PlaybackState.IDLE

    def test_reset_allows_new_session(self):
        """After reset, a new playback session should work."""
        adapter = NullPlaybackAdapter()
        started_count = []

        adapter.set_callbacks(on_started=lambda: started_count.append(1))

        # First session
        adapter.play(generate_tone(100))
        adapter.mark_complete()

        # Reset
        adapter.reset()

        # Second session
        adapter.play(generate_tone(100))

        # on_started should fire again
        assert len(started_count) == 2


# =============================================================================
# Simulate Playback Tests
# =============================================================================


class TestNullAdapterSimulatePlayback:
    """Test simulate_playback_time mode."""

    def test_simulate_playback_adds_delay(self):
        """simulate_playback_time should add realistic delays."""
        adapter = NullPlaybackAdapter(simulate_playback_time=True)

        # 100ms of audio should take ~100ms to "play"
        audio = generate_tone(100)

        start = time.time()
        adapter.play(audio)
        elapsed = time.time() - start

        # Should have slept for approximately 100ms (with some tolerance)
        assert elapsed >= 0.08  # At least 80ms
        assert elapsed < 0.2  # But not too long

    def test_simulate_playback_off_is_instant(self):
        """Without simulate_playback_time, play should be instant."""
        adapter = NullPlaybackAdapter(simulate_playback_time=False)

        audio = generate_tone(100)

        start = time.time()
        adapter.play(audio)
        elapsed = time.time() - start

        # Should be nearly instant
        assert elapsed < 0.01


# =============================================================================
# Config Tests
# =============================================================================


class TestNullAdapterConfig:
    """Test configuration handling."""

    def test_default_config(self):
        """Default config should be applied."""
        adapter = NullPlaybackAdapter()

        assert adapter.config.sample_rate == 24000
        assert adapter.config.channels == 1
        assert adapter.config.bit_depth == 16

    def test_custom_config(self):
        """Custom config should be applied."""
        config = AudioPlaybackConfig(sample_rate=48000, channels=2)
        adapter = NullPlaybackAdapter(config=config)

        assert adapter.config.sample_rate == 48000
        assert adapter.config.channels == 2

    def test_get_device_info_returns_none(self):
        """get_device_info should return None for null adapter."""
        adapter = NullPlaybackAdapter()
        assert adapter.get_device_info() is None

    def test_is_actively_outputting_always_false(self):
        """is_actively_outputting should always be False."""
        adapter = NullPlaybackAdapter()

        assert not adapter.is_actively_outputting

        adapter.play(generate_tone(100))
        assert not adapter.is_actively_outputting

    def test_cleanup_is_safe(self):
        """cleanup() should be safe to call."""
        adapter = NullPlaybackAdapter()
        adapter.play(generate_tone(100))

        # Should not raise
        adapter.cleanup()
        adapter.cleanup()  # Multiple calls should be safe
