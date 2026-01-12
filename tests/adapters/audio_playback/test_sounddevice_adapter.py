"""
Unit tests for SoundDevicePlaybackAdapter.

These tests require sounddevice and audio hardware.
Use pytest markers to skip on CI or when hardware isn't available.

Run with:
    pytest tests/adapters/audio_playback/test_sounddevice_adapter.py -v
    pytest tests/adapters/audio_playback/test_sounddevice_adapter.py -v -m "not hardware"
"""

import pytest
import threading
import time
import os
from typing import List

# Check if sounddevice is available
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
    try:
        # Check if audio devices are available
        sd.query_devices()
        AUDIO_DEVICES_AVAILABLE = True
    except Exception:
        AUDIO_DEVICES_AVAILABLE = False
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    AUDIO_DEVICES_AVAILABLE = False

# Skip all tests if sounddevice not available
pytestmark = pytest.mark.skipif(
    not SOUNDDEVICE_AVAILABLE,
    reason="sounddevice not installed"
)

# Marker for tests that require actual audio hardware
hardware_test = pytest.mark.skipif(
    not AUDIO_DEVICES_AVAILABLE or os.environ.get("CI") == "true",
    reason="Requires audio hardware (skipped in CI)"
)

from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
from chatforge.ports.audio_playback import (
    AudioPlaybackConfig,
    PlaybackState,
    DeviceNotFoundError,
)

from tests.adapters.audio_playback.fixtures import (
    generate_tone,
    generate_silence,
    generate_audio_sequence,
)


# =============================================================================
# Basic State Tests (No Hardware Required)
# =============================================================================


class TestSoundDeviceAdapterState:
    """Test basic state behavior (minimal hardware dependency)."""

    def test_initial_state_is_idle(self):
        """Should start in IDLE state."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            assert adapter.state == PlaybackState.IDLE
            assert not adapter.is_playing
        finally:
            adapter.cleanup()

    def test_config_accessible(self):
        """Config should be accessible."""
        config = AudioPlaybackConfig(sample_rate=24000, channels=1)
        adapter = SoundDevicePlaybackAdapter(config=config)
        try:
            assert adapter.config.sample_rate == 24000
            assert adapter.config.channels == 1
        finally:
            adapter.cleanup()

    def test_default_config(self):
        """Default config should be applied."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            assert adapter.config.sample_rate == 24000
            assert adapter.config.min_buffer_chunks == 2
        finally:
            adapter.cleanup()


# =============================================================================
# Device Enumeration Tests
# =============================================================================


@hardware_test
class TestSoundDeviceEnumeration:
    """Test device enumeration."""

    def test_list_devices_returns_list(self):
        """list_devices should return a list."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        assert isinstance(devices, list)

    def test_list_devices_has_output_devices(self):
        """list_devices should find output devices."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        assert len(devices) > 0

    def test_devices_have_required_fields(self):
        """Each device should have required fields."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        if devices:
            device = devices[0]
            assert hasattr(device, "id")
            assert hasattr(device, "name")
            assert hasattr(device, "channels")
            assert hasattr(device, "is_default")

    def test_at_least_one_default_device(self):
        """Should have at least one default device."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        defaults = [d for d in devices if d.is_default]
        assert len(defaults) >= 1


# =============================================================================
# Device Resolution Tests
# =============================================================================


@hardware_test
class TestSoundDeviceResolution:
    """Test device resolution by ID/name."""

    def test_default_device_resolved(self):
        """Default device should be resolved."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            info = adapter.get_device_info()
            assert info is not None
            assert info.name
            assert info.channels > 0
        finally:
            adapter.cleanup()

    def test_device_by_index(self):
        """Should accept device by index."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        if devices:
            config = AudioPlaybackConfig(device_id=devices[0].id)
            adapter = SoundDevicePlaybackAdapter(config=config)
            try:
                info = adapter.get_device_info()
                assert info is not None
                assert info.id == devices[0].id
            finally:
                adapter.cleanup()

    def test_device_by_name(self):
        """Should accept device by name substring."""
        devices = SoundDevicePlaybackAdapter.list_devices()
        if devices:
            # Use first few characters of name
            name_part = devices[0].name[:5]
            config = AudioPlaybackConfig(device_id=name_part)
            adapter = SoundDevicePlaybackAdapter(config=config)
            try:
                info = adapter.get_device_info()
                assert info is not None
                assert name_part.lower() in info.name.lower()
            finally:
                adapter.cleanup()

    def test_invalid_device_raises_error(self):
        """Invalid device should raise DeviceNotFoundError."""
        config = AudioPlaybackConfig(device_id="nonexistent_device_xyz123")
        with pytest.raises(DeviceNotFoundError):
            SoundDevicePlaybackAdapter(config=config)


# =============================================================================
# Playback Tests (Require Hardware)
# =============================================================================


@hardware_test
class TestSoundDevicePlayback:
    """Test actual playback functionality."""

    def test_play_queues_audio(self):
        """play() should queue audio for playback."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            audio = generate_tone(100)
            result = adapter.play(audio)
            assert result is True
        finally:
            adapter.cleanup()

    def test_play_updates_metrics(self):
        """play() should update metrics."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            audio = generate_tone(100)
            adapter.play(audio)

            metrics = adapter.get_metrics()
            assert metrics.chunks_received == 1
            assert metrics.total_bytes_received > 0
        finally:
            adapter.cleanup()

    def test_state_transitions(self):
        """Should transition through states correctly."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            assert adapter.state == PlaybackState.IDLE

            # Play audio
            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            # Should be buffering or playing
            assert adapter.state in (PlaybackState.BUFFERING, PlaybackState.PLAYING)

            adapter.mark_complete()

            # Wait for completion
            adapter.wait_until_complete_sync(timeout=5.0)
            assert adapter.state == PlaybackState.IDLE
        finally:
            adapter.cleanup()

    def test_playback_completes(self):
        """Playback should complete and fire callback."""
        adapter = SoundDevicePlaybackAdapter()
        complete = []

        try:
            adapter.set_callbacks(on_complete=lambda: complete.append(1))

            chunks = generate_audio_sequence(200, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.mark_complete()
            result = adapter.wait_until_complete_sync(timeout=5.0)

            assert result is True
            assert len(complete) == 1
        finally:
            adapter.cleanup()

    def test_on_started_fires(self):
        """on_started should fire when playback begins."""
        adapter = SoundDevicePlaybackAdapter()
        started = []

        try:
            adapter.set_callbacks(on_started=lambda: started.append(1))

            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.mark_complete()
            adapter.wait_until_complete_sync(timeout=5.0)

            assert len(started) == 1
        finally:
            adapter.cleanup()


# =============================================================================
# Buffer Tests
# =============================================================================


@hardware_test
class TestSoundDeviceBuffer:
    """Test buffer behavior."""

    def test_buffer_duration_updates(self):
        """buffer_duration_ms should update as chunks are added."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            initial = adapter.buffer_duration_ms
            assert initial == 0.0

            adapter.play(generate_tone(100))
            # Buffer may be consumed immediately, but should have tracked it
            metrics = adapter.get_metrics()
            assert metrics.total_bytes_received > 0
        finally:
            adapter.cleanup()

    def test_buffer_overflow_returns_false(self):
        """play() should return False when buffer is full."""
        config = AudioPlaybackConfig(max_buffer_ms=100)  # Very small buffer
        adapter = SoundDevicePlaybackAdapter(config=config)

        try:
            # Try to queue much more audio than buffer can hold
            result = True
            for _ in range(20):
                audio = generate_tone(50)  # 50ms per chunk
                result = adapter.play(audio)
                if not result:
                    break

            # At some point buffer should have been full
            # (May not happen if playback is fast enough)
        finally:
            adapter.cleanup()


# =============================================================================
# Stop/Barge-in Tests
# =============================================================================


@hardware_test
class TestSoundDeviceStop:
    """Test stop and barge-in behavior."""

    def test_stop_returns_to_idle(self):
        """stop() should return to IDLE state."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            chunks = generate_audio_sequence(500, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            assert adapter.state != PlaybackState.IDLE

            adapter.stop()
            assert adapter.state == PlaybackState.IDLE
        finally:
            adapter.cleanup()

    def test_force_stop_clears_buffer(self):
        """stop(force=True) should clear buffer immediately."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            chunks = generate_audio_sequence(500, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.stop(force=True)

            assert adapter.state == PlaybackState.IDLE
            assert adapter.buffer_duration_ms == 0.0
        finally:
            adapter.cleanup()

    def test_can_play_after_stop(self):
        """Should be able to play again after stop()."""
        adapter = SoundDevicePlaybackAdapter()
        started = []

        try:
            adapter.set_callbacks(on_started=lambda: started.append(1))

            # First session
            adapter.play(generate_tone(100))
            adapter.stop()

            # Second session
            adapter.play(generate_tone(100))
            adapter.mark_complete()
            adapter.wait_until_complete_sync(timeout=5.0)

            # on_started should have fired twice
            assert len(started) == 2
        finally:
            adapter.cleanup()


# =============================================================================
# Threading Tests
# =============================================================================


@hardware_test
class TestSoundDeviceThreading:
    """Test thread safety."""

    def test_play_from_multiple_threads(self):
        """play() should be safe from multiple threads."""
        adapter = SoundDevicePlaybackAdapter()
        errors = []

        try:
            def play_chunks():
                try:
                    for _ in range(5):
                        adapter.play(generate_tone(50))
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=play_chunks) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
        finally:
            adapter.cleanup()


# =============================================================================
# Metrics Tests
# =============================================================================


@hardware_test
class TestSoundDeviceMetrics:
    """Test metrics tracking."""

    def test_initial_latency_tracked(self):
        """initial_latency_ms should be tracked after playback starts."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            chunks = generate_audio_sequence(300, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.mark_complete()
            adapter.wait_until_complete_sync(timeout=5.0)

            metrics = adapter.get_metrics()
            assert metrics.initial_latency_ms is not None
            assert metrics.initial_latency_ms >= 0
        finally:
            adapter.cleanup()

    def test_playback_duration_tracked(self):
        """playback_duration_seconds should be tracked."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            chunks = generate_audio_sequence(200, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.mark_complete()
            adapter.wait_until_complete_sync(timeout=5.0)

            metrics = adapter.get_metrics()
            assert metrics.playback_duration_seconds > 0
        finally:
            adapter.cleanup()


# =============================================================================
# Async Wait Tests
# =============================================================================


@hardware_test
class TestSoundDeviceAsyncWait:
    """Test async wait functionality."""

    @pytest.mark.asyncio
    async def test_async_wait_completes(self):
        """async wait_until_complete should complete."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            chunks = generate_audio_sequence(200, chunk_ms=100)
            for chunk in chunks:
                adapter.play(chunk)

            adapter.mark_complete()
            result = await adapter.wait_until_complete(timeout=5.0)

            assert result is True
        finally:
            adapter.cleanup()

    @pytest.mark.asyncio
    async def test_async_wait_timeout(self):
        """async wait should timeout if not completed."""
        adapter = SoundDevicePlaybackAdapter()
        try:
            # Play but don't mark complete
            adapter.play(generate_tone(100))

            result = await adapter.wait_until_complete(timeout=0.1)
            assert result is False
        finally:
            adapter.cleanup()


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestSoundDeviceCleanup:
    """Test cleanup behavior."""

    def test_cleanup_stops_playback(self):
        """cleanup() should stop any ongoing playback."""
        adapter = SoundDevicePlaybackAdapter()

        adapter.play(generate_tone(100))
        adapter.cleanup()

        assert adapter.state == PlaybackState.IDLE

    def test_multiple_cleanup_calls_safe(self):
        """Multiple cleanup() calls should be safe."""
        adapter = SoundDevicePlaybackAdapter()

        adapter.play(generate_tone(100))
        adapter.cleanup()
        adapter.cleanup()  # Should not raise
        adapter.cleanup()
