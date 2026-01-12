"""
Unit tests for SoundDeviceCaptureAdapter.

Tests state machine, callbacks, metrics, and device handling.

Note: Some tests require audio hardware and are marked with @pytest.mark.hardware.
Run with: pytest -m "not hardware" to skip hardware tests.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
from chatforge.ports.audio_capture import (
    AudioCaptureConfig,
    CaptureState,
    DeviceNotFoundError,
)


# =============================================================================
# Basic State Tests (no hardware required)
# =============================================================================


class TestSoundDeviceAdapterBasicState:
    """Test basic adapter state behavior."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_initial_state_is_idle(self, mock_sd):
        """Adapter should start in IDLE state."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        adapter = SoundDeviceCaptureAdapter()

        assert adapter.state == CaptureState.IDLE
        assert not adapter.is_capturing

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_config_applied(self, mock_sd):
        """Custom config should be applied."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        config = AudioCaptureConfig(sample_rate=48000, channels=2)
        adapter = SoundDeviceCaptureAdapter(config=config)

        assert adapter.config.sample_rate == 48000
        assert adapter.config.channels == 2

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_device_info_populated(self, mock_sd):
        """Device info should be populated on init."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        adapter = SoundDeviceCaptureAdapter()
        device_info = adapter.get_device_info()

        assert device_info is not None
        assert device_info.name == "Test Device"
        assert device_info.channels == 2


# =============================================================================
# Device Resolution Tests
# =============================================================================


class TestSoundDeviceAdapterDeviceResolution:
    """Test device resolution behavior."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_device_by_index(self, mock_sd):
        """Should accept device by integer index."""
        mock_sd.query_devices.return_value = {
            "name": "Device 1",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        config = AudioCaptureConfig(device_id=1)
        adapter = SoundDeviceCaptureAdapter(config=config)

        device_info = adapter.get_device_info()
        assert device_info.id == 1

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_device_by_name(self, mock_sd):
        """Should accept device by name substring."""
        mock_sd.query_devices.return_value = [
            {"name": "Built-in Microphone", "max_input_channels": 2, "default_samplerate": 44100.0},
            {"name": "USB Audio", "max_input_channels": 1, "default_samplerate": 48000.0},
        ]
        mock_sd.default.device = [0, 0]

        config = AudioCaptureConfig(device_id="USB")
        adapter = SoundDeviceCaptureAdapter(config=config)

        device_info = adapter.get_device_info()
        assert "USB" in device_info.name

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_device_not_found_raises(self, mock_sd):
        """Should raise DeviceNotFoundError for non-existent device."""
        import sounddevice as real_sd

        mock_sd.query_devices.return_value = [
            {"name": "Built-in Microphone", "max_input_channels": 2, "default_samplerate": 44100.0},
        ]
        mock_sd.default.device = [0, 0]
        mock_sd.PortAudioError = real_sd.PortAudioError

        config = AudioCaptureConfig(device_id="NonExistent Device")

        with pytest.raises(DeviceNotFoundError, match="NonExistent Device"):
            SoundDeviceCaptureAdapter(config=config)


# =============================================================================
# List Devices Tests
# =============================================================================


class TestSoundDeviceAdapterListDevices:
    """Test device listing."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_list_devices_returns_list(self, mock_sd):
        """list_devices should return list of AudioDevice."""
        mock_sd.query_devices.return_value = [
            {"name": "Device 1", "max_input_channels": 2, "default_samplerate": 44100.0},
            {"name": "Device 2", "max_input_channels": 1, "default_samplerate": 48000.0},
            {"name": "Output Only", "max_input_channels": 0, "default_samplerate": 44100.0},
        ]
        mock_sd.default.device = [0, 0]

        devices = SoundDeviceCaptureAdapter.list_devices()

        # Should only include input devices (max_input_channels > 0)
        assert len(devices) == 2
        assert devices[0].name == "Device 1"
        assert devices[1].name == "Device 2"

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_list_devices_marks_default(self, mock_sd):
        """list_devices should mark default device."""
        mock_sd.query_devices.return_value = [
            {"name": "Device 1", "max_input_channels": 2, "default_samplerate": 44100.0},
            {"name": "Device 2", "max_input_channels": 1, "default_samplerate": 48000.0},
        ]
        mock_sd.default.device = [1, 0]  # Device 1 is default input

        devices = SoundDeviceCaptureAdapter.list_devices()

        assert devices[1].is_default


# =============================================================================
# Callback Tests
# =============================================================================


class TestSoundDeviceAdapterCallbacks:
    """Test callback behavior."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    @pytest.mark.asyncio
    async def test_callbacks_set(self, mock_sd):
        """Callbacks should be settable."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        adapter = SoundDeviceCaptureAdapter()

        started_called = []
        stopped_called = []

        adapter.set_callbacks(
            on_started=lambda: started_called.append(1),
            on_stopped=lambda: stopped_called.append(1),
        )

        # Just verify callbacks are set (can't easily test firing without mocking InputStream)
        assert adapter._on_started is not None
        assert adapter._on_stopped is not None


# =============================================================================
# Metrics Tests
# =============================================================================


class TestSoundDeviceAdapterMetrics:
    """Test metrics tracking."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_initial_metrics_are_zero(self, mock_sd):
        """Metrics should be zero before starting."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        adapter = SoundDeviceCaptureAdapter()

        metrics = adapter.get_metrics()
        assert metrics.chunks_captured == 0
        assert metrics.total_bytes == 0
        assert metrics.start_time is None


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestSoundDeviceAdapterCleanup:
    """Test cleanup behavior."""

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_cleanup_is_safe_without_start(self, mock_sd):
        """cleanup() should be safe to call without starting."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        adapter = SoundDeviceCaptureAdapter()

        # Should not raise
        adapter.cleanup()
        adapter.cleanup()

    @patch("chatforge.adapters.audio_capture.sounddevice_adapter.sd")
    def test_context_manager(self, mock_sd):
        """Context manager should cleanup on exit."""
        mock_sd.query_devices.return_value = {
            "name": "Test Device",
            "max_input_channels": 2,
            "default_samplerate": 44100.0,
        }
        mock_sd.default.device = [0, 0]

        with SoundDeviceCaptureAdapter() as adapter:
            pass  # Just test that context manager works

        assert adapter.state == CaptureState.IDLE


# =============================================================================
# Hardware Tests (require actual audio devices)
# =============================================================================


@pytest.mark.hardware
class TestSoundDeviceAdapterHardware:
    """Tests that require actual audio hardware."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Should start and stop capture with real hardware."""
        try:
            adapter = SoundDeviceCaptureAdapter()
        except DeviceNotFoundError:
            pytest.skip("No audio input device available")

        queue = await adapter.start()

        assert adapter.is_capturing
        assert isinstance(queue, asyncio.Queue)

        adapter.stop()

        assert not adapter.is_capturing

    @pytest.mark.asyncio
    async def test_captures_audio(self):
        """Should capture audio from hardware."""
        try:
            adapter = SoundDeviceCaptureAdapter()
        except DeviceNotFoundError:
            pytest.skip("No audio input device available")

        queue = await adapter.start()

        # Wait for some audio
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert len(chunk) > 0
        except asyncio.TimeoutError:
            pytest.skip("No audio captured (microphone may be muted)")
        finally:
            adapter.stop()

    @pytest.mark.asyncio
    async def test_callbacks_fire(self):
        """Callbacks should fire with real hardware."""
        try:
            adapter = SoundDeviceCaptureAdapter()
        except DeviceNotFoundError:
            pytest.skip("No audio input device available")

        started_called = []
        stopped_called = []

        adapter.set_callbacks(
            on_started=lambda: started_called.append(1),
            on_stopped=lambda: stopped_called.append(1),
        )

        await adapter.start()
        await asyncio.sleep(0.2)
        adapter.stop()

        assert len(started_called) == 1
        assert len(stopped_called) == 1

    @pytest.mark.asyncio
    async def test_stop_and_drain(self):
        """stop_and_drain should drain buffers."""
        try:
            adapter = SoundDeviceCaptureAdapter()
        except DeviceNotFoundError:
            pytest.skip("No audio input device available")

        queue = await adapter.start()

        # Wait for some audio to accumulate
        await asyncio.sleep(0.3)

        # Drain should complete without timeout
        await asyncio.wait_for(adapter.stop_and_drain(), timeout=5.0)

        assert not adapter.is_capturing

    def test_list_real_devices(self):
        """Should list real audio devices."""
        devices = SoundDeviceCaptureAdapter.list_devices()

        # Should have at least one device on most systems
        # (skip test if no devices available)
        if not devices:
            pytest.skip("No audio input devices available")

        # Each device should have required properties
        for device in devices:
            assert device.id >= 0
            assert device.name
            assert device.channels > 0
