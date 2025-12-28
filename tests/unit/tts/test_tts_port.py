"""
Unit tests for TTSPort interface.

Tests the base TTSPort class functionality using a mock adapter,
including validation, lifecycle management, and utility methods.
"""

import pytest
from typing import AsyncIterator, Optional

from chatforge.ports.tts import (
    TTSPort,
    VoiceConfig,
    AudioResult,
    VoiceInfo,
    AudioFormat,
    AudioQuality,
    TTSError,
    TTSInvalidInputError,
    TTSRateLimitError,
)


class MockTTSAdapter(TTSPort):
    """Mock adapter for testing base class functionality."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_ssml(self) -> bool:
        return False

    @property
    def supports_style_prompt(self) -> bool:
        return False

    @property
    def max_text_length(self) -> int:
        return 100

    async def synthesize(self, text, config, **kwargs) -> AudioResult:
        """Synthesize mock audio for testing."""
        self._validate_input(text, config)
        return AudioResult(
            audio_bytes=b"mock audio data",
            format=kwargs.get("output_format", AudioFormat.MP3),
            sample_rate=44100,
            channels=1,
            duration_ms=len(text) * 50,  # Approximate: 50ms per character
            input_characters=len(text),
        )

    async def stream(self, text, config, **kwargs) -> AsyncIterator[bytes]:
        """Stream mock audio chunks for testing."""
        self._validate_input(text, config)
        yield b"chunk1"
        yield b"chunk2"

    async def list_voices(self, language_code=None) -> list[VoiceInfo]:
        """Return mock voice list for testing."""
        voices = [
            VoiceInfo(
                voice_id="v1",
                name="Voice 1",
                provider="mock",
                language_codes=["en-US"],
            ),
            VoiceInfo(
                voice_id="v2",
                name="Voice 2",
                provider="mock",
                language_codes=["es-ES"],
            ),
        ]
        if language_code:
            voices = [v for v in voices if language_code in v.language_codes]
        return voices


class TestTTSPortValidation:
    """Test input validation in TTSPort base class."""

    @pytest.fixture
    def adapter(self):
        """Create a MockTTSAdapter instance for testing."""
        return MockTTSAdapter()

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, adapter):
        """Verify that synthesize() raises TTSInvalidInputError for empty text."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="cannot be empty"):
            await adapter.synthesize("", config)

    @pytest.mark.asyncio
    async def test_whitespace_only_raises_error(self, adapter):
        """Verify that whitespace-only text is rejected as empty."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="cannot be empty"):
            await adapter.synthesize("   ", config)

    @pytest.mark.asyncio
    async def test_text_too_long_raises_error(self, adapter):
        """Verify that text exceeding max_text_length is rejected."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="exceeds"):
            await adapter.synthesize("x" * 101, config)

    @pytest.mark.asyncio
    async def test_text_at_max_length_succeeds(self, adapter):
        """Verify that text at exactly max_text_length succeeds."""
        config = VoiceConfig(voice_id="test")
        result = await adapter.synthesize("x" * 100, config)
        assert result.input_characters == 100

    @pytest.mark.asyncio
    async def test_valid_text_succeeds(self, adapter):
        """Verify that valid text synthesizes successfully."""
        config = VoiceConfig(voice_id="test")
        result = await adapter.synthesize("Hello", config)
        assert result.audio_bytes == b"mock audio data"
        assert result.input_characters == 5

    @pytest.mark.asyncio
    async def test_stream_validates_input(self, adapter):
        """Verify that stream() validates input before yielding."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="cannot be empty"):
            async for _ in adapter.stream("", config):
                pass


class TestTTSPortStreaming:
    """Test streaming functionality."""

    @pytest.fixture
    def adapter(self):
        """Create a MockTTSAdapter instance for testing."""
        return MockTTSAdapter()

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, adapter):
        """Verify that stream() yields audio chunks."""
        config = VoiceConfig(voice_id="test")
        chunks = []
        async for chunk in adapter.stream("Hello", config):
            chunks.append(chunk)
        assert len(chunks) == 2
        assert chunks[0] == b"chunk1"
        assert chunks[1] == b"chunk2"


class TestTTSPortVoices:
    """Test voice listing functionality."""

    @pytest.fixture
    def adapter(self):
        """Create a MockTTSAdapter instance for testing."""
        return MockTTSAdapter()

    @pytest.mark.asyncio
    async def test_list_voices_returns_all(self, adapter):
        """Verify that list_voices() returns all voices without filter."""
        voices = await adapter.list_voices()
        assert len(voices) == 2
        assert all(v.provider == "mock" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_filters_by_language(self, adapter):
        """Verify that list_voices() filters by language code."""
        voices = await adapter.list_voices(language_code="en-US")
        assert len(voices) == 1
        assert voices[0].voice_id == "v1"

    @pytest.mark.asyncio
    async def test_get_voice_returns_voice_info(self, adapter):
        """Verify that get_voice() returns correct VoiceInfo."""
        voice = await adapter.get_voice("v1")
        assert voice is not None
        assert voice.voice_id == "v1"
        assert voice.name == "Voice 1"

    @pytest.mark.asyncio
    async def test_get_voice_returns_none_for_unknown(self, adapter):
        """Verify that get_voice() returns None for unknown voice ID."""
        voice = await adapter.get_voice("unknown")
        assert voice is None


class TestTTSPortLifecycle:
    """Test lifecycle methods (context manager, close)."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Verify async context manager works correctly."""
        async with MockTTSAdapter() as adapter:
            config = VoiceConfig(voice_id="test")
            result = await adapter.synthesize("Hello", config)
            assert result is not None

    @pytest.mark.asyncio
    async def test_close_can_be_called_multiple_times(self):
        """Verify that close() can be called multiple times safely."""
        adapter = MockTTSAdapter()
        await adapter.close()
        await adapter.close()  # Should not raise


class TestAudioFormat:
    """Test AudioFormat enum."""

    def test_format_values(self):
        """Verify enum values match expected strings."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG_OPUS.value == "ogg_opus"
        assert AudioFormat.PCM.value == "pcm"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.AAC.value == "aac"

    def test_format_is_string(self):
        """Verify AudioFormat inherits from str for JSON serialization."""
        assert isinstance(AudioFormat.MP3, str)
        assert AudioFormat.MP3 == "mp3"


class TestAudioQuality:
    """Test AudioQuality enum."""

    def test_quality_values(self):
        """Verify enum values match expected strings."""
        assert AudioQuality.LOW.value == "low"
        assert AudioQuality.STANDARD.value == "standard"
        assert AudioQuality.HIGH.value == "high"

    def test_quality_is_string(self):
        """Verify AudioQuality inherits from str for JSON serialization."""
        assert isinstance(AudioQuality.STANDARD, str)


class TestVoiceConfig:
    """Test VoiceConfig dataclass."""

    def test_default_values(self):
        """Verify default values are set correctly."""
        config = VoiceConfig(voice_id="test")
        assert config.voice_id == "test"
        assert config.language_code == "en-US"
        assert config.speed == 1.0

    def test_custom_values(self):
        """Verify custom values can be set."""
        config = VoiceConfig(
            voice_id="test",
            language_code="es-ES",
            speed=1.5,
        )
        assert config.language_code == "es-ES"
        assert config.speed == 1.5


class TestAudioResult:
    """Test AudioResult dataclass."""

    def test_minimal_result(self):
        """Verify AudioResult with minimal required fields."""
        result = AudioResult(
            audio_bytes=b"test",
            format=AudioFormat.MP3,
        )
        assert result.audio_bytes == b"test"
        assert result.format == AudioFormat.MP3
        assert result.sample_rate == 44100  # default
        assert result.channels == 1  # default

    def test_full_result(self):
        """Verify AudioResult with all fields populated."""
        result = AudioResult(
            audio_bytes=b"test audio",
            format=AudioFormat.WAV,
            sample_rate=48000,
            bitrate_kbps=192,
            channels=2,
            duration_ms=5000,
            input_characters=100,
            billed_characters=120,
            request_id="req-123",
        )
        assert result.sample_rate == 48000
        assert result.bitrate_kbps == 192
        assert result.channels == 2
        assert result.duration_ms == 5000


class TestVoiceInfo:
    """Test VoiceInfo dataclass."""

    def test_minimal_voice_info(self):
        """Verify VoiceInfo with minimal required fields."""
        info = VoiceInfo(
            voice_id="v1",
            name="Test Voice",
            provider="test",
        )
        assert info.voice_id == "v1"
        assert info.name == "Test Voice"
        assert info.language_codes == []  # default empty list

    def test_full_voice_info(self):
        """Verify VoiceInfo with all fields populated."""
        info = VoiceInfo(
            voice_id="v1",
            name="Test Voice",
            provider="test",
            language_codes=["en-US", "en-GB"],
            gender="female",
            description="A test voice",
            preview_url="https://example.com/preview.mp3",
            supports_ssml=True,
            supports_streaming=True,
            is_custom=True,
            quality_tier="premium",
        )
        assert len(info.language_codes) == 2
        assert info.gender == "female"
        assert info.is_custom is True


class TestTTSExceptions:
    """Test TTS exception classes."""

    def test_tts_error_base(self):
        """Verify TTSError is the base for all TTS exceptions."""
        assert issubclass(TTSInvalidInputError, TTSError)
        assert issubclass(TTSRateLimitError, TTSError)

    def test_rate_limit_error_with_retry(self):
        """Verify TTSRateLimitError stores retry_after_seconds."""
        error = TTSRateLimitError("Rate limited", retry_after_seconds=30.0)
        assert error.retry_after_seconds == 30.0
        assert "Rate limited" in str(error)

    def test_rate_limit_error_without_retry(self):
        """Verify TTSRateLimitError works without retry_after_seconds."""
        error = TTSRateLimitError("Rate limited")
        assert error.retry_after_seconds is None
