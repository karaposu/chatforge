"""
Integration tests for TTS adapters.

These tests require actual API keys and make real API calls.
Run with: pytest tests/integration/tts/ -v --run-integration

WARNING: These tests cost money (API usage).
"""

import os
import pytest

# Skip all tests if no API keys
pytestmark = pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY") and not os.getenv("OPENAI_API_KEY"),
    reason="No TTS API keys configured",
)


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ELEVENLABS_API_KEY"), reason="No ElevenLabs key")
class TestElevenLabsIntegration:
    """Integration tests for ElevenLabs (requires valid API key in environment)."""

    @pytest.mark.asyncio
    async def test_synthesize(self):
        """Test text-to-speech synthesis with a dynamically selected voice."""
        from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter
        from chatforge.ports.tts import VoiceConfig, AudioFormat

        async with ElevenLabsTTSAdapter() as tts:
            # Get voice dynamically instead of hardcoding
            # This ensures the test works across different accounts
            voices = await tts.list_voices()
            voice_id = voices[0].voice_id if voices else "21m00Tcm4TlvDq8ikWAM"

            config = VoiceConfig(voice_id=voice_id)
            result = await tts.synthesize("Hello world", config)

            assert len(result.audio_bytes) > 0
            assert result.format == AudioFormat.MP3
            assert result.input_characters == 11

    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test that list_voices returns available voices from the account."""
        from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter

        async with ElevenLabsTTSAdapter() as tts:
            voices = await tts.list_voices()
            assert len(voices) > 0
            assert all(v.provider == "elevenlabs" for v in voices)
            assert all(v.voice_id for v in voices)
            assert all(v.name for v in voices)

    @pytest.mark.asyncio
    async def test_stream(self):
        """Test streaming synthesis yields audio chunks."""
        from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter
        from chatforge.ports.tts import VoiceConfig

        async with ElevenLabsTTSAdapter() as tts:
            voices = await tts.list_voices()
            voice_id = voices[0].voice_id if voices else "21m00Tcm4TlvDq8ikWAM"

            config = VoiceConfig(voice_id=voice_id)
            chunks = []
            async for chunk in tts.stream("Hello world", config):
                chunks.append(chunk)

            assert len(chunks) > 0
            total_bytes = sum(len(c) for c in chunks)
            assert total_bytes > 0


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OpenAI key")
class TestOpenAIIntegration:
    """Integration tests for OpenAI (requires valid API key in environment)."""

    @pytest.mark.asyncio
    async def test_synthesize(self):
        """Test text-to-speech synthesis with OpenAI."""
        from chatforge.adapters.tts.openai import OpenAITTSAdapter
        from chatforge.ports.tts import VoiceConfig, AudioFormat

        async with OpenAITTSAdapter() as tts:
            config = VoiceConfig(voice_id="nova")
            result = await tts.synthesize("Hello world", config)

            assert len(result.audio_bytes) > 0
            assert result.format == AudioFormat.MP3
            assert result.input_characters == 11

    @pytest.mark.asyncio
    async def test_synthesize_with_style_prompt(self):
        """Test synthesis with style prompt."""
        from chatforge.adapters.tts.openai import OpenAITTSAdapter, OpenAIVoiceConfig
        from chatforge.ports.tts import AudioFormat

        async with OpenAITTSAdapter() as tts:
            config = OpenAIVoiceConfig(
                voice_id="nova",
                style_prompt="Speak in a warm, friendly tone",
            )
            result = await tts.synthesize("Hello world", config)

            assert len(result.audio_bytes) > 0
            assert result.format == AudioFormat.MP3

    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test that list_voices returns available voices."""
        from chatforge.adapters.tts.openai import OpenAITTSAdapter

        async with OpenAITTSAdapter() as tts:
            voices = await tts.list_voices()
            assert len(voices) > 0
            assert all(v.provider == "openai" for v in voices)

            # Check for expected voices
            voice_ids = [v.voice_id for v in voices]
            assert "nova" in voice_ids
            assert "alloy" in voice_ids

    @pytest.mark.asyncio
    async def test_stream(self):
        """Test streaming synthesis yields audio chunks."""
        from chatforge.adapters.tts.openai import OpenAITTSAdapter
        from chatforge.ports.tts import VoiceConfig

        async with OpenAITTSAdapter() as tts:
            config = VoiceConfig(voice_id="nova")
            chunks = []
            async for chunk in tts.stream("Hello world", config):
                chunks.append(chunk)

            assert len(chunks) > 0
            total_bytes = sum(len(c) for c in chunks)
            assert total_bytes > 0

    @pytest.mark.asyncio
    async def test_different_formats(self):
        """Test synthesis with different audio formats."""
        from chatforge.adapters.tts.openai import OpenAITTSAdapter
        from chatforge.ports.tts import VoiceConfig, AudioFormat

        async with OpenAITTSAdapter() as tts:
            config = VoiceConfig(voice_id="nova")

            # Test MP3
            result_mp3 = await tts.synthesize(
                "Hello", config, output_format=AudioFormat.MP3
            )
            assert len(result_mp3.audio_bytes) > 0
            assert result_mp3.format == AudioFormat.MP3

            # Test WAV
            result_wav = await tts.synthesize(
                "Hello", config, output_format=AudioFormat.WAV
            )
            assert len(result_wav.audio_bytes) > 0
            assert result_wav.format == AudioFormat.WAV
