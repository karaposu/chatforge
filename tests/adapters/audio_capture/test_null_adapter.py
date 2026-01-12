"""
Unit tests for NullCaptureAdapter.

Tests state machine, callbacks, metrics, and signal generation.
"""

import asyncio
import pytest

from chatforge.adapters.audio_capture import NullCaptureAdapter
from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    CaptureState,
)


# =============================================================================
# Basic State Tests
# =============================================================================


class TestNullAdapterBasicState:
    """Test basic adapter state behavior."""

    def test_initial_state_is_idle(self):
        """Adapter should start in IDLE state."""
        adapter = NullCaptureAdapter()
        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_start_transitions_to_capturing(self):
        """start() should transition to CAPTURING."""
        adapter = NullCaptureAdapter()

        await adapter.start()

        assert adapter.state == CaptureState.CAPTURING
        assert adapter.is_capturing

        adapter.stop()

    @pytest.mark.asyncio
    async def test_stop_transitions_to_idle(self):
        """stop() should transition to IDLE."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        assert adapter.is_capturing

        adapter.stop()

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_stop_and_drain_transitions_to_idle(self):
        """stop_and_drain() should transition to IDLE."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        assert adapter.is_capturing

        await adapter.stop_and_drain()

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_start_returns_queue(self):
        """start() should return an asyncio.Queue."""
        adapter = NullCaptureAdapter()

        result = await adapter.start()

        assert isinstance(result, asyncio.Queue)

        adapter.stop()

    @pytest.mark.asyncio
    async def test_double_start_returns_same_queue(self):
        """Calling start() twice should return the same queue."""
        adapter = NullCaptureAdapter()

        queue1 = await adapter.start()
        queue2 = await adapter.start()

        assert queue1 is queue2

        adapter.stop()


# =============================================================================
# Callback Tests
# =============================================================================


class TestNullAdapterCallbacks:
    """Test callback behavior."""

    @pytest.mark.asyncio
    async def test_on_started_fires_once(self):
        """on_started should fire exactly once."""
        adapter = NullCaptureAdapter()
        started_count = []

        adapter.set_callbacks(on_started=lambda: started_count.append(1))

        await adapter.start()
        # Wait a bit to generate some chunks
        await asyncio.sleep(0.1)
        adapter.stop()

        assert len(started_count) == 1

    @pytest.mark.asyncio
    async def test_on_stopped_fires_once(self):
        """on_stopped should fire exactly once on stop()."""
        adapter = NullCaptureAdapter()
        stopped_count = []

        adapter.set_callbacks(on_stopped=lambda: stopped_count.append(1))

        await adapter.start()
        adapter.stop()

        assert len(stopped_count) == 1

    @pytest.mark.asyncio
    async def test_on_stopped_fires_once_on_drain(self):
        """on_stopped should fire exactly once on stop_and_drain()."""
        adapter = NullCaptureAdapter()
        stopped_count = []

        adapter.set_callbacks(on_stopped=lambda: stopped_count.append(1))

        await adapter.start()
        await adapter.stop_and_drain()

        assert len(stopped_count) == 1

    @pytest.mark.asyncio
    async def test_on_chunk_captured_fires_for_each_chunk(self):
        """on_chunk_captured should fire for each chunk."""
        adapter = NullCaptureAdapter()
        chunk_counts = []

        adapter.set_callbacks(on_chunk_captured=lambda count: chunk_counts.append(count))

        await adapter.start()
        # Wait to generate some chunks
        await asyncio.sleep(0.25)
        adapter.stop()

        # Should have generated at least 2 chunks (100ms each)
        assert len(chunk_counts) >= 2

    @pytest.mark.asyncio
    async def test_callback_exception_is_caught(self):
        """Callback exceptions should not propagate."""
        adapter = NullCaptureAdapter()

        def bad_callback():
            raise ValueError("Test error")

        adapter.set_callbacks(on_started=bad_callback)

        # Should not raise
        await adapter.start()
        assert adapter.is_capturing

        adapter.stop()


# =============================================================================
# Metrics Tests
# =============================================================================


class TestNullAdapterMetrics:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_chunks_captured_increments(self):
        """chunks_captured should increment for each generated chunk."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        # Wait to generate some chunks
        await asyncio.sleep(0.25)
        adapter.stop()

        metrics = adapter.get_metrics()
        assert metrics.chunks_captured >= 2

    @pytest.mark.asyncio
    async def test_bytes_tracked(self):
        """Total bytes should be tracked."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        await asyncio.sleep(0.15)
        adapter.stop()

        metrics = adapter.get_metrics()
        assert metrics.total_bytes > 0

    @pytest.mark.asyncio
    async def test_start_time_set(self):
        """start_time should be set after start()."""
        adapter = NullCaptureAdapter()

        await adapter.start()

        metrics = adapter.get_metrics()
        assert metrics.start_time is not None

        adapter.stop()

    @pytest.mark.asyncio
    async def test_capture_duration_computed(self):
        """capture_duration_seconds should be computed dynamically."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        await asyncio.sleep(0.1)

        metrics = adapter.get_metrics()
        assert metrics.capture_duration_seconds >= 0.1

        adapter.stop()

    @pytest.mark.asyncio
    async def test_capture_rate_computed(self):
        """capture_rate should be computed dynamically."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        await asyncio.sleep(0.25)
        adapter.stop()

        metrics = adapter.get_metrics()
        # With 100ms chunks, should be about 10 chunks/sec
        assert metrics.capture_rate > 0

    def test_initial_metrics_are_zero(self):
        """Metrics should be zero before starting."""
        adapter = NullCaptureAdapter()

        metrics = adapter.get_metrics()
        assert metrics.chunks_captured == 0
        assert metrics.total_bytes == 0
        assert metrics.start_time is None


# =============================================================================
# Signal Generation Tests
# =============================================================================


class TestNullAdapterSignals:
    """Test signal generation."""

    @pytest.mark.asyncio
    async def test_silence_generates_zeros(self):
        """silence signal should generate zeros."""
        adapter = NullCaptureAdapter(signal="silence")

        queue = await adapter.start()
        chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
        adapter.stop()

        # All bytes should be zero
        assert all(b == 0 for b in chunk)

    @pytest.mark.asyncio
    async def test_sine_generates_nonzero(self):
        """sine signal should generate non-zero values."""
        adapter = NullCaptureAdapter(signal="sine", frequency=440)

        queue = await adapter.start()
        chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
        adapter.stop()

        # Should have some non-zero bytes
        assert any(b != 0 for b in chunk)

    @pytest.mark.asyncio
    async def test_noise_generates_nonzero(self):
        """noise signal should generate non-zero values."""
        adapter = NullCaptureAdapter(signal="noise")

        queue = await adapter.start()
        chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
        adapter.stop()

        # Should have some non-zero bytes
        assert any(b != 0 for b in chunk)

    @pytest.mark.asyncio
    async def test_duration_limit(self):
        """duration_ms should limit capture duration."""
        adapter = NullCaptureAdapter(duration_ms=150)

        queue = await adapter.start()

        # Collect all chunks until generator stops
        chunks = []
        try:
            while True:
                chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
                chunks.append(chunk)
        except asyncio.TimeoutError:
            pass

        adapter.stop()

        # Should have generated about 1-2 chunks (100ms each, 150ms duration)
        assert 1 <= len(chunks) <= 2

    def test_signal_type_property(self):
        """signal_type property should return signal type."""
        adapter = NullCaptureAdapter(signal="sine")
        assert adapter.signal_type == "sine"


# =============================================================================
# Config Tests
# =============================================================================


class TestNullAdapterConfig:
    """Test configuration handling."""

    def test_default_config(self):
        """Default config should be applied."""
        adapter = NullCaptureAdapter()

        assert adapter.config.sample_rate == 24000
        assert adapter.config.channels == 1
        assert adapter.config.bit_depth == 16

    def test_custom_config(self):
        """Custom config should be applied."""
        config = AudioCaptureConfig(sample_rate=48000, channels=2)
        adapter = NullCaptureAdapter(config=config)

        assert adapter.config.sample_rate == 48000
        assert adapter.config.channels == 2

    def test_get_device_info_returns_none(self):
        """get_device_info should return None for null adapter."""
        adapter = NullCaptureAdapter()
        assert adapter.get_device_info() is None


# =============================================================================
# Reset Tests
# =============================================================================


class TestNullAdapterReset:
    """Test reset behavior."""

    @pytest.mark.asyncio
    async def test_reset_clears_metrics(self):
        """reset() should clear all metrics."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        await asyncio.sleep(0.15)
        adapter.stop()

        assert adapter.get_metrics().chunks_captured > 0

        adapter.reset()

        assert adapter.get_metrics().chunks_captured == 0
        assert adapter.state == CaptureState.IDLE

    @pytest.mark.asyncio
    async def test_reset_allows_new_session(self):
        """After reset, a new capture session should work."""
        adapter = NullCaptureAdapter()
        started_count = []

        adapter.set_callbacks(on_started=lambda: started_count.append(1))

        # First session
        await adapter.start()
        adapter.stop()

        # Reset
        adapter.reset()

        # Second session
        await adapter.start()
        adapter.stop()

        # on_started should fire again
        assert len(started_count) == 2


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestNullAdapterCleanup:
    """Test cleanup behavior."""

    @pytest.mark.asyncio
    async def test_cleanup_stops_capture(self):
        """cleanup() should stop capture if active."""
        adapter = NullCaptureAdapter()

        await adapter.start()
        assert adapter.is_capturing

        adapter.cleanup()

        assert not adapter.is_capturing
        assert adapter.state == CaptureState.IDLE

    def test_cleanup_is_safe_without_start(self):
        """cleanup() should be safe to call without starting."""
        adapter = NullCaptureAdapter()

        # Should not raise
        adapter.cleanup()
        adapter.cleanup()  # Multiple calls should be safe

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Context manager should cleanup on exit."""
        with NullCaptureAdapter() as adapter:
            await adapter.start()
            assert adapter.is_capturing

        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Async context manager should drain and cleanup."""
        async with NullCaptureAdapter() as adapter:
            await adapter.start()
            assert adapter.is_capturing

        assert not adapter.is_capturing
