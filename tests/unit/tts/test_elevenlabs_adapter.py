"""
Tests for ElevenLabs TTS adapter.

Tests adapter initialization, properties, format mapping, and error handling.
Uses mocks to avoid actual API calls.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from chatforge.adapters.tts.elevenlabs import (
    ElevenLabsTTSAdapter,
    ElevenLabsVoiceConfig,
)
from chatforge.ports.tts import (
    AudioFormat,
    AudioQuality,
    VoiceConfig,
    TTSAuthenticationError,
    TTSRateLimitError,
    TTSInvalidVoiceError,
    TTSInvalidInputError,
    TTSQuotaExceededError,
    TTSError,
)


class TestElevenLabsAdapterInit:
    """Test ElevenLabs adapter initialization."""

    def test_requires_api_key(self):
        """Verify that adapter raises error when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSAuthenticationError, match="API key required"):
                ElevenLabsTTSAdapter()

    def test_accepts_explicit_api_key(self):
        """Verify that explicit api_key parameter is accepted."""
        with patch("elevenlabs.AsyncElevenLabs"):
            adapter = ElevenLabsTTSAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"

    def test_reads_env_var(self):
        """Verify that API key is read from environment variable."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "env-key"}):
            with patch("elevenlabs.AsyncElevenLabs"):
                adapter = ElevenLabsTTSAdapter()
                assert adapter._api_key == "env-key"

    def test_explicit_key_overrides_env(self):
        """Verify that explicit api_key takes precedence over env var."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "env-key"}):
            with patch("elevenlabs.AsyncElevenLabs"):
                adapter = ElevenLabsTTSAdapter(api_key="explicit-key")
                assert adapter._api_key == "explicit-key"


class TestElevenLabsAdapterProperties:
    """Test ElevenLabs adapter properties."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("elevenlabs.AsyncElevenLabs"):
            return ElevenLabsTTSAdapter(api_key="test")

    def test_provider_name(self, adapter):
        """Verify provider_name returns 'elevenlabs'."""
        assert adapter.provider_name == "elevenlabs"

    def test_supports_streaming(self, adapter):
        """Verify supports_streaming returns True."""
        assert adapter.supports_streaming is True

    def test_supports_ssml(self, adapter):
        """Verify supports_ssml returns True."""
        assert adapter.supports_ssml is True

    def test_supports_style_prompt(self, adapter):
        """Verify supports_style_prompt returns False (uses audio tags)."""
        assert adapter.supports_style_prompt is False

    def test_max_text_length(self, adapter):
        """Verify max_text_length returns 5000."""
        assert adapter.max_text_length == 5000


class TestElevenLabsFormatMapping:
    """Test format mapping logic."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("elevenlabs.AsyncElevenLabs"):
            return ElevenLabsTTSAdapter(api_key="test")

    def test_mp3_quality_mapping(self, adapter):
        """Verify MP3 format maps correctly for different quality levels."""
        assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.LOW) == "mp3_22050_32"
        assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.STANDARD) == "mp3_44100_128"
        assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.HIGH) == "mp3_44100_192"

    def test_pcm_quality_mapping(self, adapter):
        """Verify PCM format maps correctly for different quality levels."""
        assert adapter._get_provider_format(AudioFormat.PCM, AudioQuality.LOW) == "pcm_16000"
        assert adapter._get_provider_format(AudioFormat.PCM, AudioQuality.STANDARD) == "pcm_22050"
        assert adapter._get_provider_format(AudioFormat.PCM, AudioQuality.HIGH) == "pcm_44100"

    def test_opus_quality_mapping(self, adapter):
        """Verify OGG_OPUS format maps correctly for different quality levels."""
        assert adapter._get_provider_format(AudioFormat.OGG_OPUS, AudioQuality.LOW) == "opus_16000_32"
        assert adapter._get_provider_format(AudioFormat.OGG_OPUS, AudioQuality.STANDARD) == "opus_22050_64"
        assert adapter._get_provider_format(AudioFormat.OGG_OPUS, AudioQuality.HIGH) == "opus_44100_128"

    def test_unsupported_format_raises_error(self, adapter):
        """Verify unsupported format/quality combinations raise error."""
        with pytest.raises(TTSInvalidInputError, match="does not support"):
            adapter._get_provider_format(AudioFormat.WAV, AudioQuality.STANDARD)


class TestElevenLabsVoiceConfig:
    """Test ElevenLabsVoiceConfig dataclass."""

    def test_default_values(self):
        """Verify default values are set correctly."""
        config = ElevenLabsVoiceConfig(voice_id="test")
        assert config.stability == 0.5
        assert config.similarity_boost == 0.75
        assert config.style_exaggeration == 0.0
        assert config.use_speaker_boost is True

    def test_custom_values(self):
        """Verify custom values can be set."""
        config = ElevenLabsVoiceConfig(
            voice_id="test",
            stability=0.8,
            similarity_boost=0.9,
            style_exaggeration=0.5,
            use_speaker_boost=False,
        )
        assert config.stability == 0.8
        assert config.similarity_boost == 0.9
        assert config.style_exaggeration == 0.5
        assert config.use_speaker_boost is False

    def test_inherits_base_config(self):
        """Verify ElevenLabsVoiceConfig inherits from VoiceConfig."""
        config = ElevenLabsVoiceConfig(
            voice_id="test",
            language_code="es-ES",
            speed=1.2,
        )
        assert config.language_code == "es-ES"
        assert config.speed == 1.2


class TestElevenLabsSynthesize:
    """Test synthesize method."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("elevenlabs.AsyncElevenLabs") as mock_class:
            mock_client = MagicMock()
            mock_class.return_value = mock_client
            adapter = ElevenLabsTTSAdapter(api_key="test")
            return adapter

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_result(self, adapter):
        """Verify synthesize returns AudioResult with correct data."""
        # Mock the API response
        adapter._client.text_to_speech.convert = AsyncMock(return_value=b"audio data")

        config = VoiceConfig(voice_id="test-voice")
        result = await adapter.synthesize("Hello world", config)

        assert result.audio_bytes == b"audio data"
        assert result.format == AudioFormat.MP3
        assert result.input_characters == 11

    @pytest.mark.asyncio
    async def test_synthesize_with_elevenlabs_config(self, adapter):
        """Verify synthesize uses ElevenLabsVoiceConfig settings."""
        adapter._client.text_to_speech.convert = AsyncMock(return_value=b"audio data")

        config = ElevenLabsVoiceConfig(
            voice_id="test-voice",
            stability=0.8,
            similarity_boost=0.9,
        )
        await adapter.synthesize("Hello", config)

        # Verify voice_settings were passed
        call_kwargs = adapter._client.text_to_speech.convert.call_args.kwargs
        assert call_kwargs["voice_settings"]["stability"] == 0.8
        assert call_kwargs["voice_settings"]["similarity_boost"] == 0.9

    @pytest.mark.asyncio
    async def test_synthesize_validates_empty_text(self, adapter):
        """Verify synthesize rejects empty text."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="cannot be empty"):
            await adapter.synthesize("", config)

    @pytest.mark.asyncio
    async def test_synthesize_validates_long_text(self, adapter):
        """Verify synthesize rejects text exceeding max length."""
        config = VoiceConfig(voice_id="test")
        with pytest.raises(TTSInvalidInputError, match="exceeds"):
            await adapter.synthesize("x" * 5001, config)


class TestElevenLabsErrorHandling:
    """Test error handling and exception mapping."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("elevenlabs.AsyncElevenLabs"):
            return ElevenLabsTTSAdapter(api_key="test")

    def test_authentication_error_from_string(self, adapter):
        """Verify authentication errors are detected from string."""
        error = Exception("unauthorized request")
        with pytest.raises(TTSAuthenticationError):
            adapter._handle_api_error(error)

    def test_rate_limit_error_from_string(self, adapter):
        """Verify rate limit errors are detected from string."""
        error = Exception("rate limit exceeded")
        with pytest.raises(TTSRateLimitError):
            adapter._handle_api_error(error)

    def test_quota_error_from_string(self, adapter):
        """Verify quota errors are detected from string."""
        error = Exception("quota exceeded")
        with pytest.raises(TTSQuotaExceededError):
            adapter._handle_api_error(error)

    def test_voice_not_found_from_string(self, adapter):
        """Verify voice not found errors are detected from string."""
        error = Exception("voice not found")
        with pytest.raises(TTSInvalidVoiceError):
            adapter._handle_api_error(error)

    def test_generic_error_fallback(self, adapter):
        """Verify unknown errors become TTSError."""
        error = Exception("some unknown error")
        with pytest.raises(TTSError, match="ElevenLabs error"):
            adapter._handle_api_error(error)


class TestElevenLabsDurationCalculation:
    """Test audio duration calculation."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("elevenlabs.AsyncElevenLabs"):
            return ElevenLabsTTSAdapter(api_key="test")

    def test_pcm_duration_calculation(self, adapter):
        """Verify PCM duration is calculated correctly."""
        # 44100 samples/sec, 16-bit (2 bytes/sample), mono
        # 1 second = 44100 * 2 = 88200 bytes
        audio_bytes = b"\x00" * 88200
        format_info = {"sample_rate": 44100}

        duration = adapter._calculate_duration(audio_bytes, AudioFormat.PCM, format_info)
        assert duration == 1000  # 1000 ms = 1 second

    def test_mp3_duration_returns_none(self, adapter):
        """Verify compressed format duration returns None."""
        audio_bytes = b"compressed audio"
        format_info = {"sample_rate": 44100}

        duration = adapter._calculate_duration(audio_bytes, AudioFormat.MP3, format_info)
        assert duration is None
