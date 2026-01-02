"""Tests for MockAudioStreamAdapter."""

import pytest

from chatforge.adapters.audio import MockAudioStreamAdapter
from chatforge.ports import AudioCallbacks, AudioStreamError


class TestMockAudioStreamAdapter:
    """Tests for MockAudioStreamAdapter."""

    @pytest.mark.asyncio
    async def test_capture_yields_chunks(self):
        """Test that capture yields pre-recorded audio in chunks."""
        audio_data = b"\x00\x01" * 4800  # 2 chunks worth
        mock = MockAudioStreamAdapter(
            capture_audio=audio_data, chunk_size=4800, capture_delay_ms=1
        )

        async with mock:
            chunks = [c async for c in mock.start_capture()]

        assert len(chunks) == 2
        assert mock.capture_started
        assert chunks[0] == b"\x00\x01" * 2400
        assert chunks[1] == b"\x00\x01" * 2400

    @pytest.mark.asyncio
    async def test_capture_empty_audio(self):
        """Test capture with no pre-recorded audio."""
        mock = MockAudioStreamAdapter(capture_audio=b"", capture_delay_ms=1)

        async with mock:
            chunks = [c async for c in mock.start_capture()]

        assert len(chunks) == 0
        assert mock.capture_started

    @pytest.mark.asyncio
    async def test_capture_already_capturing_raises(self):
        """Test that starting capture twice raises error."""
        mock = MockAudioStreamAdapter(capture_audio=b"\x00" * 100, capture_delay_ms=1)

        async with mock:
            gen = mock.start_capture()
            await gen.__anext__()  # Start capturing

            with pytest.raises(AudioStreamError, match="Already capturing"):
                async for _ in mock.start_capture():
                    pass

    @pytest.mark.asyncio
    async def test_playback_collects_chunks(self):
        """Test that play() collects chunks for assertions."""
        mock = MockAudioStreamAdapter()

        async with mock:
            await mock.play(b"chunk1")
            await mock.play(b"chunk2")

        assert len(mock.played_chunks) == 2
        assert mock.played_chunks[0] == b"chunk1"
        assert mock.played_chunks[1] == b"chunk2"
        assert mock.get_total_played_bytes() == 12

    @pytest.mark.asyncio
    async def test_end_playback_triggers_callback(self):
        """Test that end_playback triggers on_playback_complete."""
        mock = MockAudioStreamAdapter()
        completed = False

        def on_complete():
            nonlocal completed
            completed = True

        async with mock:
            mock.set_callbacks(AudioCallbacks(on_playback_complete=on_complete))
            await mock.end_playback()

        assert mock.end_playback_called
        assert completed

    @pytest.mark.asyncio
    async def test_stop_playback_sets_flag(self):
        """Test that stop_playback sets the flag."""
        mock = MockAudioStreamAdapter()

        async with mock:
            await mock.stop_playback()

        assert mock.playback_stopped

    @pytest.mark.asyncio
    async def test_speech_start_callback(self):
        """Test simulate_speech_start triggers callback."""
        mock = MockAudioStreamAdapter()
        speech_started = False

        def on_start():
            nonlocal speech_started
            speech_started = True

        async with mock:
            mock.set_callbacks(AudioCallbacks(on_speech_start=on_start))
            mock.simulate_speech_start()

        assert speech_started

    @pytest.mark.asyncio
    async def test_speech_end_callback(self):
        """Test simulate_speech_end triggers callback with audio."""
        mock = MockAudioStreamAdapter()
        speech_audio = None

        def on_end(audio):
            nonlocal speech_audio
            speech_audio = audio

        async with mock:
            mock.set_callbacks(AudioCallbacks(on_speech_end=on_end))
            mock.simulate_speech_end(b"pre_buffer_audio")

        assert speech_audio == b"pre_buffer_audio"

    @pytest.mark.asyncio
    async def test_error_callback(self):
        """Test simulate_error triggers callback."""
        mock = MockAudioStreamAdapter()
        errors = []

        async with mock:
            mock.set_callbacks(AudioCallbacks(on_error=lambda e: errors.append(e)))
            mock.simulate_error(RuntimeError("Device disconnected"))

        assert len(errors) == 1
        assert "disconnected" in str(errors[0])

    @pytest.mark.asyncio
    async def test_device_selection(self):
        """Test device listing and selection."""
        mock = MockAudioStreamAdapter()

        async with mock:
            devices = mock.list_input_devices()
            assert len(devices) == 2
            assert devices[0].is_default
            assert devices[0].name == "Mock Microphone"

            mock.set_input_device(1)
            # Should not raise

    @pytest.mark.asyncio
    async def test_device_change_while_capturing_raises(self):
        """Test that changing device while capturing raises."""
        mock = MockAudioStreamAdapter(
            capture_audio=b"\x00" * 10000, capture_delay_ms=100
        )

        async with mock:
            gen = mock.start_capture()
            await gen.__anext__()  # Start capturing

            with pytest.raises(RuntimeError, match="Cannot change device"):
                mock.set_input_device(1)

    @pytest.mark.asyncio
    async def test_provider_name(self):
        """Test provider_name property."""
        mock = MockAudioStreamAdapter()
        assert mock.provider_name == "mock"

    @pytest.mark.asyncio
    async def test_get_config(self):
        """Test get_config returns default config."""
        mock = MockAudioStreamAdapter()
        config = mock.get_config()

        assert config.sample_rate == 24000
        assert config.channels == 1
        assert config.bit_depth == 16

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test reset clears all state."""
        mock = MockAudioStreamAdapter(capture_audio=b"\x00" * 100, capture_delay_ms=1)

        async with mock:
            async for _ in mock.start_capture():
                pass
            await mock.play(b"chunk")
            await mock.end_playback()

        assert mock.capture_started
        assert len(mock.played_chunks) == 1
        assert mock.end_playback_called

        mock.reset()

        assert not mock.capture_started
        assert len(mock.played_chunks) == 0
        assert not mock.end_playback_called

    @pytest.mark.asyncio
    async def test_stop_capture(self):
        """Test stop_capture stops the generator."""
        mock = MockAudioStreamAdapter(
            capture_audio=b"\x00" * 48000,  # Many chunks
            chunk_size=4800,
            capture_delay_ms=1,
        )

        async with mock:
            chunks = []
            async for chunk in mock.start_capture():
                chunks.append(chunk)
                if len(chunks) >= 2:
                    await mock.stop_capture()
                    break

        assert len(chunks) == 2
        assert mock.capture_stopped
