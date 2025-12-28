"""
Tests for OpenAI TTS adapter.

Tests adapter initialization, properties, format mapping, and error handling.
Uses mocks to avoid actual API calls.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from chatforge.adapters.tts.openai import (
    OpenAITTSAdapter,
    OpenAIVoiceConfig,
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


class TestOpenAIAdapterInit:
    """Test OpenAI adapter initialization."""

    def test_requires_api_key(self):
        """Verify that adapter raises error when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSAuthenticationError, match="API key required"):
                OpenAITTSAdapter()

    def test_accepts_explicit_api_key(self):
        """Verify that explicit api_key parameter is accepted."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAITTSAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"

    def test_reads_env_var(self):
        """Verify that API key is read from environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with patch("openai.AsyncOpenAI"):
                adapter = OpenAITTSAdapter()
                assert adapter._api_key == "env-key"


class TestOpenAIAdapterProperties:
    """Test OpenAI adapter properties."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI"):
            return OpenAITTSAdapter(api_key="test")

    def test_provider_name(self, adapter):
        """Verify provider_name returns 'openai'."""
        assert adapter.provider_name == "openai"

    def test_supports_streaming(self, adapter):
        """Verify supports_streaming returns True."""
        assert adapter.supports_streaming is True

    def test_supports_ssml(self, adapter):
        """Verify supports_ssml returns False."""
        assert adapter.supports_ssml is False

    def test_supports_style_prompt(self, adapter):
        """Verify supports_style_prompt returns True."""
        assert adapter.supports_style_prompt is True

    def test_max_text_length(self, adapter):
        """Verify max_text_length returns 4096."""
        assert adapter.max_text_length == 4096


class TestOpenAIFormatMapping:
    """Test format mapping logic."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI"):
            return OpenAITTSAdapter(api_key="test")

    def test_supported_formats(self, adapter):
        """Verify all supported formats map correctly."""
        assert adapter._get_provider_format(AudioFormat.MP3) == "mp3"
        assert adapter._get_provider_format(AudioFormat.WAV) == "wav"
        assert adapter._get_provider_format(AudioFormat.FLAC) == "flac"
        assert adapter._get_provider_format(AudioFormat.AAC) == "aac"
        assert adapter._get_provider_format(AudioFormat.OGG_OPUS) == "opus"
        assert adapter._get_provider_format(AudioFormat.PCM) == "pcm"


class TestOpenAIVoiceConfig:
    """Test OpenAIVoiceConfig dataclass."""

    def test_default_values(self):
        """Verify default values are set correctly."""
        config = OpenAIVoiceConfig(voice_id="nova")
        assert config.style_prompt is None

    def test_custom_style_prompt(self):
        """Verify style_prompt can be set."""
        config = OpenAIVoiceConfig(
            voice_id="nova",
            style_prompt="Speak in a warm, friendly tone",
        )
        assert config.style_prompt == "Speak in a warm, friendly tone"

    def test_inherits_base_config(self):
        """Verify OpenAIVoiceConfig inherits from VoiceConfig."""
        config = OpenAIVoiceConfig(
            voice_id="nova",
            language_code="es-ES",
            speed=1.5,
        )
        assert config.language_code == "es-ES"
        assert config.speed == 1.5


class TestOpenAIPreprocessText:
    """Test text preprocessing."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI"):
            return OpenAITTSAdapter(api_key="test")

    def test_strips_elevenlabs_audio_tags(self, adapter):
        """Verify ElevenLabs audio tags are removed."""
        config = VoiceConfig(voice_id="test")
        text = "Hello [whispers] world [laughs] how are [pause] you [sighs]?"
        result = adapter._preprocess_text(text, config)
        assert result == "Hello  world  how are  you ?"

    def test_preserves_normal_text(self, adapter):
        """Verify normal text is preserved."""
        config = VoiceConfig(voice_id="test")
        text = "Hello world, how are you?"
        result = adapter._preprocess_text(text, config)
        assert result == text


class TestOpenAIListVoices:
    """Test list_voices method."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI"):
            return OpenAITTSAdapter(api_key="test")

    @pytest.mark.asyncio
    async def test_list_voices_returns_all_voices(self, adapter):
        """Verify list_voices returns all OpenAI voices."""
        voices = await adapter.list_voices()
        voice_ids = [v.voice_id for v in voices]

        # Verify expected voices are present
        assert "alloy" in voice_ids
        assert "echo" in voice_ids
        assert "nova" in voice_ids
        assert "onyx" in voice_ids
        assert "shimmer" in voice_ids

    @pytest.mark.asyncio
    async def test_list_voices_all_have_correct_provider(self, adapter):
        """Verify all voices have provider set to 'openai'."""
        voices = await adapter.list_voices()
        assert all(v.provider == "openai" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_all_support_streaming(self, adapter):
        """Verify all voices support streaming."""
        voices = await adapter.list_voices()
        assert all(v.supports_streaming for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_none_support_ssml(self, adapter):
        """Verify no voices claim SSML support."""
        voices = await adapter.list_voices()
        assert all(not v.supports_ssml for v in voices)


class TestOpenAISynthesize:
    """Test synthesize method."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI") as mock_class:
            mock_client = MagicMock()
            mock_class.return_value = mock_client
            adapter = OpenAITTSAdapter(api_key="test")
            adapter._client = mock_client
            return adapter

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_result(self, adapter):
        """Verify synthesize returns AudioResult with correct data."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = b"audio data"
        adapter._client.audio.speech.create = AsyncMock(return_value=mock_response)

        config = VoiceConfig(voice_id="nova")
        result = await adapter.synthesize("Hello world", config)

        assert result.audio_bytes == b"audio data"
        assert result.format == AudioFormat.MP3
        assert result.sample_rate == 24000  # OpenAI default
        assert result.input_characters == 11

    @pytest.mark.asyncio
    async def test_synthesize_uses_quality_for_model_selection(self, adapter):
        """Verify quality parameter affects model selection."""
        mock_response = MagicMock()
        mock_response.content = b"audio"
        adapter._client.audio.speech.create = AsyncMock(return_value=mock_response)

        config = VoiceConfig(voice_id="nova")

        # Standard quality -> tts-1
        await adapter.synthesize("Hello", config, quality=AudioQuality.STANDARD)
        call_kwargs = adapter._client.audio.speech.create.call_args.kwargs
        assert call_kwargs["model"] == "tts-1"

        # High quality -> tts-1-hd
        await adapter.synthesize("Hello", config, quality=AudioQuality.HIGH)
        call_kwargs = adapter._client.audio.speech.create.call_args.kwargs
        assert call_kwargs["model"] == "tts-1-hd"

    @pytest.mark.asyncio
    async def test_synthesize_with_style_prompt(self, adapter):
        """Verify synthesize uses OpenAIVoiceConfig style_prompt."""
        mock_response = MagicMock()
        mock_response.content = b"audio"
        adapter._client.audio.speech.create = AsyncMock(return_value=mock_response)

        config = OpenAIVoiceConfig(
            voice_id="nova",
            style_prompt="Speak enthusiastically",
        )
        await adapter.synthesize("Hello", config)

        call_kwargs = adapter._client.audio.speech.create.call_args.kwargs
        assert call_kwargs["instructions"] == "Speak enthusiastically"

    @pytest.mark.asyncio
    async def test_synthesize_with_speed(self, adapter):
        """Verify synthesize uses speed from config."""
        mock_response = MagicMock()
        mock_response.content = b"audio"
        adapter._client.audio.speech.create = AsyncMock(return_value=mock_response)

        config = VoiceConfig(voice_id="nova", speed=1.5)
        await adapter.synthesize("Hello", config)

        call_kwargs = adapter._client.audio.speech.create.call_args.kwargs
        assert call_kwargs["speed"] == 1.5

    @pytest.mark.asyncio
    async def test_synthesize_validates_empty_text(self, adapter):
        """Verify synthesize rejects empty text."""
        config = VoiceConfig(voice_id="nova")
        with pytest.raises(TTSInvalidInputError, match="cannot be empty"):
            await adapter.synthesize("", config)


class TestOpenAIErrorHandling:
    """Test error handling and exception mapping."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch("openai.AsyncOpenAI"):
            return OpenAITTSAdapter(api_key="test")

    def test_authentication_error_from_string(self, adapter):
        """Verify authentication errors are detected from string."""
        error = Exception("invalid_api_key error")
        with pytest.raises(TTSAuthenticationError):
            adapter._handle_api_error(error)

    def test_rate_limit_error_from_string(self, adapter):
        """Verify rate limit errors are detected from string."""
        error = Exception("rate_limit exceeded")
        with pytest.raises(TTSRateLimitError):
            adapter._handle_api_error(error)

    def test_quota_error_from_string(self, adapter):
        """Verify quota errors are detected from string."""
        error = Exception("insufficient_quota")
        with pytest.raises(TTSQuotaExceededError):
            adapter._handle_api_error(error)

    def test_voice_error_from_string(self, adapter):
        """Verify voice errors are detected from string."""
        error = Exception("invalid_voice specified")
        with pytest.raises(TTSInvalidVoiceError):
            adapter._handle_api_error(error)

    def test_generic_error_fallback(self, adapter):
        """Verify unknown errors become TTSError."""
        error = Exception("some unknown error")
        with pytest.raises(TTSError, match="OpenAI error"):
            adapter._handle_api_error(error)
