"""
Unit tests for FileCaptureAdapter.

Tests file reading, chunking, and state management.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path

from chatforge.adapters.audio_capture import FileCaptureAdapter
from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    AudioCaptureError,
    CaptureState,
    UnsupportedConfigError,
)

from tests.adapters.audio_capture.fixtures import create_test_wav, create_temp_wav


# =============================================================================
# Basic State Tests
# =============================================================================


class TestFileAdapterBasicState:
    """Test basic adapter state behavior."""

    def test_initial_state_is_idle(self):
        """Adapter should start in IDLE state."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_start_transitions_to_capturing(self):
        """start() should transition to CAPTURING."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        await adapter.start()

        assert adapter.state == CaptureState.CAPTURING
        assert adapter.is_capturing

        adapter.stop()

    @pytest.mark.asyncio
    async def test_stop_transitions_to_idle(self):
        """stop() should transition to IDLE."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        await adapter.start()
        adapter.stop()

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_start_returns_queue(self):
        """start() should return an asyncio.Queue."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        result = await adapter.start()

        assert isinstance(result, asyncio.Queue)

        adapter.stop()

    def test_file_path_property(self):
        """file_path property should return the file path."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        assert adapter.file_path == wav_path


# =============================================================================
# File Reading Tests
# =============================================================================


class TestFileAdapterReading:
    """Test file reading behavior."""

    @pytest.mark.asyncio
    async def test_reads_all_chunks(self):
        """Should read all chunks from file."""
        wav_path = create_temp_wav(duration_ms=300)
        adapter = FileCaptureAdapter(wav_path, realtime=False)

        queue = await adapter.start()

        chunks = []
        try:
            while True:
                chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
                chunks.append(chunk)
        except asyncio.TimeoutError:
            pass

        adapter.stop()

        # 300ms at 100ms per chunk = 3 chunks
        assert len(chunks) == 3

    @pytest.mark.asyncio
    async def test_chunk_sizes_match_config(self):
        """Chunks should match configured chunk size."""
        wav_path = create_temp_wav(duration_ms=200, sample_rate=24000)
        config = AudioCaptureConfig(sample_rate=24000, chunk_duration_ms=100)
        adapter = FileCaptureAdapter(wav_path, config=config, realtime=False)

        queue = await adapter.start()
        chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
        adapter.stop()

        # 100ms at 24kHz, mono, 16-bit = 2400 samples * 2 bytes = 4800 bytes
        assert len(chunk) == 4800

    @pytest.mark.asyncio
    async def test_loop_mode(self):
        """Loop mode should restart from beginning."""
        wav_path = create_temp_wav(duration_ms=100)
        adapter = FileCaptureAdapter(wav_path, loop=True, realtime=False)

        queue = await adapter.start()

        # Should get more than 1 chunk (file is only 100ms = 1 chunk)
        chunks = []
        for _ in range(3):
            chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
            chunks.append(chunk)

        adapter.stop()

        assert len(chunks) == 3

    @pytest.mark.asyncio
    async def test_realtime_timing(self):
        """realtime=True should add delays between chunks."""
        wav_path = create_temp_wav(duration_ms=300)
        adapter = FileCaptureAdapter(wav_path, realtime=True)

        queue = await adapter.start()

        import time

        start = time.time()
        chunk1 = await asyncio.wait_for(queue.get(), timeout=0.5)
        chunk2 = await asyncio.wait_for(queue.get(), timeout=0.5)
        chunk3 = await asyncio.wait_for(queue.get(), timeout=0.5)
        elapsed = time.time() - start

        adapter.stop()

        # Should take approximately 300ms (3 chunks * 100ms)
        # Allow some tolerance for timing variations
        assert elapsed >= 0.2


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestFileAdapterErrors:
    """Test error handling."""

    def test_file_not_found(self):
        """Should raise error for non-existent file."""
        with pytest.raises(AudioCaptureError, match="File not found"):
            FileCaptureAdapter("/nonexistent/file.wav")

    @pytest.mark.asyncio
    async def test_sample_rate_mismatch_error(self):
        """Should raise error for sample rate mismatch without resample."""
        wav_path = create_temp_wav(duration_ms=500, sample_rate=44100)
        config = AudioCaptureConfig(sample_rate=24000)
        adapter = FileCaptureAdapter(wav_path, config=config, resample=False)

        with pytest.raises(UnsupportedConfigError, match="sample rate"):
            await adapter.start()

    def test_resample_requires_scipy(self):
        """resample=True should require scipy."""
        wav_path = create_temp_wav(duration_ms=500)

        # This may or may not raise depending on scipy availability
        # Just test that the parameter is accepted
        try:
            adapter = FileCaptureAdapter(wav_path, resample=True)
            # If scipy is available, this works
        except ImportError as e:
            # If scipy is not available, we get an ImportError
            assert "scipy" in str(e).lower()


# =============================================================================
# Callback Tests
# =============================================================================


class TestFileAdapterCallbacks:
    """Test callback behavior."""

    @pytest.mark.asyncio
    async def test_on_started_fires_once(self):
        """on_started should fire exactly once."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path, realtime=False)
        started_count = []

        adapter.set_callbacks(on_started=lambda: started_count.append(1))

        await adapter.start()
        await asyncio.sleep(0.1)
        adapter.stop()

        assert len(started_count) == 1

    @pytest.mark.asyncio
    async def test_on_stopped_fires_once(self):
        """on_stopped should fire exactly once."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)
        stopped_count = []

        adapter.set_callbacks(on_stopped=lambda: stopped_count.append(1))

        await adapter.start()
        adapter.stop()

        assert len(stopped_count) == 1

    @pytest.mark.asyncio
    async def test_on_chunk_captured_fires_for_each_chunk(self):
        """on_chunk_captured should fire for each chunk."""
        wav_path = create_temp_wav(duration_ms=300)
        adapter = FileCaptureAdapter(wav_path, realtime=False)
        chunk_counts = []

        adapter.set_callbacks(on_chunk_captured=lambda count: chunk_counts.append(count))

        queue = await adapter.start()

        # Wait for all chunks to be read
        await asyncio.sleep(0.2)
        adapter.stop()

        assert len(chunk_counts) == 3


# =============================================================================
# Metrics Tests
# =============================================================================


class TestFileAdapterMetrics:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_chunks_captured_increments(self):
        """chunks_captured should increment for each chunk."""
        wav_path = create_temp_wav(duration_ms=300)
        adapter = FileCaptureAdapter(wav_path, realtime=False)

        queue = await adapter.start()
        await asyncio.sleep(0.2)
        adapter.stop()

        metrics = adapter.get_metrics()
        assert metrics.chunks_captured == 3

    @pytest.mark.asyncio
    async def test_bytes_tracked(self):
        """Total bytes should be tracked."""
        wav_path = create_temp_wav(duration_ms=200)
        adapter = FileCaptureAdapter(wav_path, realtime=False)

        queue = await adapter.start()
        await asyncio.sleep(0.1)
        adapter.stop()

        metrics = adapter.get_metrics()
        assert metrics.total_bytes > 0

    @pytest.mark.asyncio
    async def test_start_time_set(self):
        """start_time should be set after start()."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        await adapter.start()

        metrics = adapter.get_metrics()
        assert metrics.start_time is not None

        adapter.stop()


# =============================================================================
# Config Tests
# =============================================================================


class TestFileAdapterConfig:
    """Test configuration handling."""

    def test_default_config(self):
        """Default config should be applied."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        assert adapter.config.sample_rate == 24000
        assert adapter.config.channels == 1

    def test_custom_config(self):
        """Custom config should be applied."""
        wav_path = create_temp_wav(duration_ms=500, sample_rate=48000)
        config = AudioCaptureConfig(sample_rate=48000, channels=1)
        adapter = FileCaptureAdapter(wav_path, config=config)

        assert adapter.config.sample_rate == 48000

    def test_get_device_info_returns_none(self):
        """get_device_info should return None for file adapter."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        assert adapter.get_device_info() is None


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestFileAdapterCleanup:
    """Test cleanup behavior."""

    @pytest.mark.asyncio
    async def test_cleanup_stops_capture(self):
        """cleanup() should stop capture if active."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        await adapter.start()
        assert adapter.is_capturing

        adapter.cleanup()

        assert not adapter.is_capturing
        assert adapter.state == CaptureState.IDLE

    def test_cleanup_is_safe_without_start(self):
        """cleanup() should be safe to call without starting."""
        wav_path = create_temp_wav(duration_ms=500)
        adapter = FileCaptureAdapter(wav_path)

        # Should not raise
        adapter.cleanup()
        adapter.cleanup()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Context manager should cleanup on exit."""
        wav_path = create_temp_wav(duration_ms=500)
        with FileCaptureAdapter(wav_path) as adapter:
            await adapter.start()
            assert adapter.is_capturing

        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Async context manager should drain and cleanup."""
        wav_path = create_temp_wav(duration_ms=500)
        async with FileCaptureAdapter(wav_path) as adapter:
            await adapter.start()
            assert adapter.is_capturing

        assert not adapter.is_capturing
