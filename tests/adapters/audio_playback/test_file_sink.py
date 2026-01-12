"""
Unit tests for FileSinkAdapter.

Tests file writing, state machine, callbacks, and metrics.
"""

import pytest
import wave
import tempfile
import os
from pathlib import Path

from chatforge.adapters.audio_playback import FileSinkAdapter
from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    AudioPlaybackError,
    PlaybackState,
)

from tests.adapters.audio_playback.fixtures import (
    generate_tone,
    generate_silence,
    generate_audio_sequence,
)


# =============================================================================
# File Writing Tests
# =============================================================================


class TestFileSinkWriting:
    """Test file writing behavior."""

    def test_creates_wav_file(self):
        """Should create a valid WAV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            audio = generate_tone(100)
            adapter.play(audio)
            adapter.mark_complete()
            adapter.cleanup()

            assert path.exists()

            # Verify it's a valid WAV file
            with wave.open(str(path), "rb") as wav:
                assert wav.getnchannels() == 1
                assert wav.getsampwidth() == 2  # 16-bit
                assert wav.getframerate() == 24000

    def test_writes_correct_data(self):
        """Should write the correct audio data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            audio = generate_tone(100)
            adapter.play(audio)
            adapter.mark_complete()
            adapter.cleanup()

            # Read back and verify
            with wave.open(str(path), "rb") as wav:
                frames = wav.readframes(wav.getnframes())
                assert frames == audio

    def test_writes_multiple_chunks(self):
        """Should correctly append multiple chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)
            adapter.mark_complete()
            adapter.cleanup()

            # Read back and verify total length
            with wave.open(str(path), "rb") as wav:
                frames = wav.readframes(wav.getnframes())
                expected_bytes = sum(len(c) for c in chunks)
                assert len(frames) == expected_bytes

    def test_creates_parent_directories(self):
        """Should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir1" / "subdir2" / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()
            adapter.cleanup()

            assert path.exists()

    def test_respects_config_sample_rate(self):
        """Should use configured sample rate in WAV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            config = AudioPlaybackConfig(sample_rate=48000)
            adapter = FileSinkAdapter(path, config=config)

            adapter.play(generate_tone(100, sample_rate=48000))
            adapter.mark_complete()
            adapter.cleanup()

            with wave.open(str(path), "rb") as wav:
                assert wav.getframerate() == 48000

    def test_respects_config_channels(self):
        """Should use configured channels in WAV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            config = AudioPlaybackConfig(channels=2)
            adapter = FileSinkAdapter(path, config=config)

            adapter.play(generate_tone(100, channels=2))
            adapter.mark_complete()
            adapter.cleanup()

            with wave.open(str(path), "rb") as wav:
                assert wav.getnchannels() == 2


# =============================================================================
# State Tests
# =============================================================================


class TestFileSinkState:
    """Test state machine behavior."""

    def test_initial_state_is_idle(self):
        """Should start in IDLE state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            assert adapter.state == PlaybackState.IDLE

            adapter.cleanup()

    def test_play_transitions_to_playing(self):
        """play() should transition to PLAYING."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))

            assert adapter.state == PlaybackState.PLAYING

            adapter.cleanup()

    def test_mark_complete_transitions_to_idle(self):
        """mark_complete() should transition to IDLE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            assert adapter.state == PlaybackState.IDLE

            adapter.cleanup()

    def test_play_after_complete_rejected(self):
        """play() after mark_complete() should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            result = adapter.play(generate_tone(100))
            assert result is False

            adapter.cleanup()


# =============================================================================
# Callback Tests
# =============================================================================


class TestFileSinkCallbacks:
    """Test callback behavior."""

    def test_on_started_fires_once(self):
        """on_started should fire once on first write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            started = []
            adapter.set_callbacks(on_started=lambda: started.append(1))

            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            assert len(started) == 1

            adapter.cleanup()

    def test_on_complete_fires_once(self):
        """on_complete should fire once on mark_complete()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            complete = []
            adapter.set_callbacks(on_complete=lambda: complete.append(1))

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            assert len(complete) == 1

            adapter.cleanup()

    def test_on_chunk_played_fires(self):
        """on_chunk_played should fire for each chunk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            played = []
            adapter.set_callbacks(on_chunk_played=lambda c: played.append(c))

            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            assert len(played) == 3

            adapter.cleanup()


# =============================================================================
# Metrics Tests
# =============================================================================


class TestFileSinkMetrics:
    """Test metrics tracking."""

    def test_chunks_counted(self):
        """Should count chunks written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            metrics = adapter.get_metrics()
            assert metrics.chunks_received == 3
            assert metrics.chunks_played == 3

            adapter.cleanup()

    def test_bytes_counted(self):
        """Should count bytes written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            audio = generate_tone(100)  # 4800 bytes
            adapter.play(audio)

            metrics = adapter.get_metrics()
            assert metrics.total_bytes_received == 4800
            assert metrics.total_bytes_played == 4800

            adapter.cleanup()

    def test_timing_tracked(self):
        """Should track timing metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            metrics = adapter.get_metrics()
            assert metrics.first_chunk_time is not None
            assert metrics.playback_start_time is not None
            assert metrics.playback_end_time is not None

            adapter.cleanup()

    def test_buffer_always_zero(self):
        """Buffer should always be 0 (no buffering)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))

            assert adapter.buffer_duration_ms == 0.0

            adapter.cleanup()


# =============================================================================
# Wait Tests
# =============================================================================


class TestFileSinkWait:
    """Test wait functionality."""

    def test_wait_returns_true_after_complete(self):
        """wait_until_complete_sync should return True after mark_complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            result = adapter.wait_until_complete_sync(timeout=1.0)
            assert result is True

            adapter.cleanup()

    @pytest.mark.asyncio
    async def test_async_wait_returns_true(self):
        """async wait should return True after mark_complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            adapter.play(generate_tone(100))
            adapter.mark_complete()

            result = await adapter.wait_until_complete(timeout=1.0)
            assert result is True

            adapter.cleanup()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestFileSinkErrors:
    """Test error handling."""

    def test_invalid_path_raises_error(self):
        """Invalid path should raise AudioPlaybackError."""
        # Try to write to a path that can't be created
        with pytest.raises(AudioPlaybackError):
            FileSinkAdapter("/nonexistent/readonly/path/test.wav")

    def test_get_device_info_returns_none(self):
        """get_device_info should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            assert adapter.get_device_info() is None

            adapter.cleanup()


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestFileSinkContextManager:
    """Test context manager usage."""

    def test_context_manager_closes_file(self):
        """Context manager should close file on exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"

            with FileSinkAdapter(path) as adapter:
                adapter.play(generate_tone(100))
                adapter.mark_complete()

            # File should be closed and valid
            assert path.exists()
            with wave.open(str(path), "rb") as wav:
                assert wav.getnframes() > 0

    def test_context_manager_on_exception(self):
        """Context manager should close file even on exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"

            try:
                with FileSinkAdapter(path) as adapter:
                    adapter.play(generate_tone(100))
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # File should still exist (may be incomplete)
            assert path.exists()


# =============================================================================
# Property Tests
# =============================================================================


class TestFileSinkProperties:
    """Test property accessors."""

    def test_file_path_property(self):
        """file_path should return the output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            assert adapter.file_path == path

            adapter.cleanup()

    def test_config_property(self):
        """config should return the configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            config = AudioPlaybackConfig(sample_rate=48000)
            adapter = FileSinkAdapter(path, config=config)

            assert adapter.config.sample_rate == 48000

            adapter.cleanup()

    def test_is_actively_outputting(self):
        """is_actively_outputting should reflect playing state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.wav"
            adapter = FileSinkAdapter(path)

            assert not adapter.is_actively_outputting

            adapter.play(generate_tone(100))
            assert adapter.is_actively_outputting

            adapter.mark_complete()
            assert not adapter.is_actively_outputting

            adapter.cleanup()
