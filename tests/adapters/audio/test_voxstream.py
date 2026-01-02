"""
Tests for VoxStreamAdapter.

Unit tests run without VoxStream installed.
Integration tests require VoxStream and audio hardware.
"""

import pytest

from chatforge.adapters.audio import VoxStreamAdapter
from chatforge.ports import AudioStreamConfig, VADConfig


class TestVoxStreamAdapterUnit:
    """Unit tests for VoxStreamAdapter - no audio hardware required."""

    def test_provider_name(self):
        """Test provider_name property."""
        adapter = VoxStreamAdapter()
        assert adapter.provider_name == "voxstream"

    def test_default_config(self):
        """Test default configuration."""
        adapter = VoxStreamAdapter()
        config = adapter.get_config()

        assert config.sample_rate == 24000
        assert config.channels == 1
        assert config.bit_depth == 16
        assert config.chunk_duration_ms == 100

    def test_custom_config(self):
        """Test custom configuration."""
        custom_config = AudioStreamConfig(
            sample_rate=48000,
            channels=2,
            bit_depth=24,
            chunk_duration_ms=50,
        )
        adapter = VoxStreamAdapter(config=custom_config)

        assert adapter.get_config().sample_rate == 48000
        assert adapter.get_config().channels == 2

    def test_default_vad_config(self):
        """Test default VAD configuration."""
        adapter = VoxStreamAdapter()
        # VAD config is internal, but we can verify adapter was created
        assert adapter._vad_config.enabled is True
        assert adapter._vad_config.energy_threshold == 0.02

    def test_custom_vad_config(self):
        """Test custom VAD configuration."""
        vad_config = VADConfig(
            enabled=True,
            energy_threshold=0.05,
            speech_start_ms=200,
            speech_end_ms=800,
            pre_buffer_ms=500,
        )
        adapter = VoxStreamAdapter(vad_config=vad_config)

        assert adapter._vad_config.energy_threshold == 0.05
        assert adapter._vad_config.speech_end_ms == 800

    def test_mode_parameter(self):
        """Test processing mode parameter."""
        adapter = VoxStreamAdapter(mode="quality")
        assert adapter._mode == "quality"

        adapter2 = VoxStreamAdapter(mode="balanced")
        assert adapter2._mode == "balanced"


# Integration tests - require VoxStream and audio hardware
# These will be skipped if voxstream is not installed
try:
    import voxstream

    HAS_VOXSTREAM = True
except ImportError:
    HAS_VOXSTREAM = False


@pytest.mark.skipif(not HAS_VOXSTREAM, reason="voxstream not installed")
@pytest.mark.integration
class TestVoxStreamAdapterIntegration:
    """Integration tests for VoxStreamAdapter - require audio hardware."""

    @pytest.mark.asyncio
    async def test_voxstream_adapter_initializes(self):
        """Test that adapter initializes successfully."""
        async with VoxStreamAdapter() as audio:
            assert audio.get_config().sample_rate == 24000
            assert audio.provider_name == "voxstream"

    @pytest.mark.asyncio
    async def test_voxstream_with_custom_config(self):
        """Test adapter with custom configuration."""
        config = AudioStreamConfig(
            sample_rate=16000,
            channels=1,
            bit_depth=16,
            chunk_duration_ms=50,
        )

        async with VoxStreamAdapter(config=config) as audio:
            assert audio.get_config().sample_rate == 16000
            assert audio.get_config().chunk_duration_ms == 50

    @pytest.mark.asyncio
    async def test_voxstream_with_vad_disabled(self):
        """Test adapter with VAD disabled."""
        vad_config = VADConfig(enabled=False)

        async with VoxStreamAdapter(vad_config=vad_config) as audio:
            # Should initialize without VAD
            assert audio.provider_name == "voxstream"

    @pytest.mark.asyncio
    async def test_voxstream_capture_yields_audio(self):
        """Test that capture yields audio chunks."""
        async with VoxStreamAdapter() as audio:
            chunks = []
            async for chunk in audio.start_capture():
                chunks.append(chunk)
                if len(chunks) >= 5:
                    await audio.stop_capture()
                    break

            assert len(chunks) == 5
            assert all(isinstance(c, bytes) for c in chunks)
            # Each chunk should have data
            assert all(len(c) > 0 for c in chunks)

    @pytest.mark.asyncio
    async def test_voxstream_list_devices(self):
        """Test that device listing works."""
        async with VoxStreamAdapter() as audio:
            devices = audio.list_input_devices()

            assert isinstance(devices, list)
            # At least one device should exist on a machine with audio
            assert len(devices) >= 1
            # Check device structure
            assert hasattr(devices[0], "id")
            assert hasattr(devices[0], "name")
            assert hasattr(devices[0], "channels")
            assert hasattr(devices[0], "is_default")
