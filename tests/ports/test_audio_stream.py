"""Tests for AudioStreamPort interface and types."""

import pytest

from chatforge.adapters.audio import MockAudioStreamAdapter, VoxStreamAdapter
from chatforge.adapters import NullAudioStreamAdapter
from chatforge.ports import (
    AudioStreamPort,
    AudioStreamConfig,
    VADConfig,
    AudioDevice,
    AudioCallbacks,
    AudioStreamError,
    AudioStreamDeviceError,
    AudioStreamBufferError,
    AudioStreamNotInitializedError,
)


class TestAudioStreamConfig:
    """Tests for AudioStreamConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AudioStreamConfig()

        assert config.sample_rate == 24000
        assert config.channels == 1
        assert config.bit_depth == 16
        assert config.chunk_duration_ms == 100

    def test_bytes_per_chunk_calculation(self):
        """Test bytes_per_chunk property calculation."""
        config = AudioStreamConfig()
        # 24000 Hz * 100ms / 1000 = 2400 samples
        # 2400 samples * 1 channel * 2 bytes = 4800 bytes
        assert config.bytes_per_chunk == 4800

    def test_bytes_per_chunk_stereo(self):
        """Test bytes_per_chunk with stereo."""
        config = AudioStreamConfig(channels=2)
        # 24000 Hz * 100ms / 1000 = 2400 samples
        # 2400 samples * 2 channels * 2 bytes = 9600 bytes
        assert config.bytes_per_chunk == 9600

    def test_bytes_per_chunk_different_sample_rate(self):
        """Test bytes_per_chunk with different sample rate."""
        config = AudioStreamConfig(sample_rate=48000, chunk_duration_ms=50)
        # 48000 Hz * 50ms / 1000 = 2400 samples
        # 2400 samples * 1 channel * 2 bytes = 4800 bytes
        assert config.bytes_per_chunk == 4800


class TestVADConfig:
    """Tests for VADConfig."""

    def test_default_values(self):
        """Test default VAD configuration values."""
        config = VADConfig()

        assert config.enabled is True
        assert config.energy_threshold == 0.02
        assert config.speech_start_ms == 100
        assert config.speech_end_ms == 500
        assert config.pre_buffer_ms == 300

    def test_custom_values(self):
        """Test custom VAD configuration."""
        config = VADConfig(
            enabled=False,
            energy_threshold=0.05,
            speech_start_ms=200,
            speech_end_ms=1000,
            pre_buffer_ms=500,
        )

        assert config.enabled is False
        assert config.energy_threshold == 0.05
        assert config.speech_end_ms == 1000


class TestAudioDevice:
    """Tests for AudioDevice dataclass."""

    def test_creation(self):
        """Test AudioDevice creation."""
        device = AudioDevice(
            id=0,
            name="Test Microphone",
            channels=2,
            is_default=True,
        )

        assert device.id == 0
        assert device.name == "Test Microphone"
        assert device.channels == 2
        assert device.is_default is True


class TestAudioCallbacks:
    """Tests for AudioCallbacks dataclass."""

    def test_default_none(self):
        """Test all callbacks default to None."""
        callbacks = AudioCallbacks()

        assert callbacks.on_speech_start is None
        assert callbacks.on_speech_end is None
        assert callbacks.on_playback_complete is None
        assert callbacks.on_error is None

    def test_with_callbacks(self):
        """Test callbacks can be set."""
        callbacks = AudioCallbacks(
            on_speech_start=lambda: None,
            on_speech_end=lambda audio: None,
            on_playback_complete=lambda: None,
            on_error=lambda e: None,
        )

        assert callbacks.on_speech_start is not None
        assert callbacks.on_speech_end is not None
        assert callbacks.on_playback_complete is not None
        assert callbacks.on_error is not None


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_base_exception(self):
        """Test AudioStreamError is base for all."""
        assert issubclass(AudioStreamDeviceError, AudioStreamError)
        assert issubclass(AudioStreamBufferError, AudioStreamError)
        assert issubclass(AudioStreamNotInitializedError, AudioStreamError)

    def test_catch_all(self):
        """Test catching base exception catches all."""
        try:
            raise AudioStreamDeviceError("test")
        except AudioStreamError:
            pass  # Should catch

        try:
            raise AudioStreamBufferError("test")
        except AudioStreamError:
            pass  # Should catch

        try:
            raise AudioStreamNotInitializedError("test")
        except AudioStreamError:
            pass  # Should catch


class TestPortConstants:
    """Tests for AudioStreamPort constants."""

    def test_format_constants(self):
        """Test format constants are correct."""
        assert AudioStreamPort.SAMPLE_RATE == 24000
        assert AudioStreamPort.CHANNELS == 1
        assert AudioStreamPort.FORMAT == "pcm16"


class TestAdapterImplementsPort:
    """Tests that adapters properly implement AudioStreamPort."""

    @pytest.mark.parametrize(
        "adapter_class",
        [MockAudioStreamAdapter, NullAudioStreamAdapter],
    )
    def test_adapter_is_port_subclass(self, adapter_class):
        """Test adapters inherit from AudioStreamPort."""
        assert issubclass(adapter_class, AudioStreamPort)

    @pytest.mark.parametrize(
        "adapter_class",
        [MockAudioStreamAdapter, NullAudioStreamAdapter],
    )
    def test_adapter_has_required_methods(self, adapter_class):
        """Test adapters have all required methods."""
        adapter = adapter_class()

        # Properties
        assert hasattr(adapter, "provider_name")

        # Lifecycle
        assert hasattr(adapter, "__aenter__")
        assert hasattr(adapter, "__aexit__")

        # Capture
        assert hasattr(adapter, "start_capture")
        assert hasattr(adapter, "stop_capture")

        # Playback
        assert hasattr(adapter, "play")
        assert hasattr(adapter, "end_playback")
        assert hasattr(adapter, "stop_playback")

        # Callbacks
        assert hasattr(adapter, "set_callbacks")

        # Devices
        assert hasattr(adapter, "list_input_devices")
        assert hasattr(adapter, "set_input_device")

        # Config
        assert hasattr(adapter, "get_config")

    @pytest.mark.parametrize(
        "adapter_class,expected_name",
        [
            (MockAudioStreamAdapter, "mock"),
            (NullAudioStreamAdapter, "null"),
            (VoxStreamAdapter, "voxstream"),
        ],
    )
    def test_provider_name(self, adapter_class, expected_name):
        """Test each adapter has correct provider_name."""
        adapter = adapter_class()
        assert adapter.provider_name == expected_name


class TestNullAudioStreamAdapter:
    """Tests for NullAudioStreamAdapter."""

    @pytest.mark.asyncio
    async def test_capture_yields_nothing(self):
        """Test null adapter capture yields nothing."""
        adapter = NullAudioStreamAdapter()

        async with adapter:
            chunks = [c async for c in adapter.start_capture()]

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_play_discards(self):
        """Test null adapter discards played audio."""
        adapter = NullAudioStreamAdapter()

        async with adapter:
            await adapter.play(b"test audio")
            await adapter.end_playback()
            # No error, audio is discarded

    @pytest.mark.asyncio
    async def test_list_devices_empty(self):
        """Test null adapter returns empty device list."""
        adapter = NullAudioStreamAdapter()

        async with adapter:
            devices = adapter.list_input_devices()

        assert devices == []

    @pytest.mark.asyncio
    async def test_callbacks_never_fire(self):
        """Test null adapter callbacks never fire."""
        adapter = NullAudioStreamAdapter()
        called = False

        def on_complete():
            nonlocal called
            called = True

        async with adapter:
            adapter.set_callbacks(AudioCallbacks(on_playback_complete=on_complete))
            await adapter.end_playback()

        # Callback should NOT fire for null adapter
        assert not called
