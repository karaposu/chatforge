"""
ElevenLabs TTS Adapter

Implements TTSPort for ElevenLabs text-to-speech API.
Supports both HTTP streaming and standard synthesis.

Features:
- High-quality neural voices
- Voice cloning support
- SSML support
- Multiple output formats and quality levels
- Async streaming

Usage:
    from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

    async with ElevenLabsTTSAdapter() as tts:
        config = ElevenLabsVoiceConfig(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            stability=0.5,
            similarity_boost=0.75,
        )
        result = await tts.synthesize("Hello world", config)

Environment Variables:
    ELEVENLABS_API_KEY: ElevenLabs API key
"""

import os
from dataclasses import dataclass
from typing import AsyncIterator, NoReturn, Optional

from chatforge.ports.tts import (
    TTSPort,
    VoiceConfig,
    AudioResult,
    VoiceInfo,
    AudioFormat,
    AudioQuality,
    TTSError,
    TTSNetworkError,
    TTSAuthenticationError,
    TTSQuotaExceededError,
    TTSRateLimitError,
    TTSInvalidVoiceError,
    TTSInvalidInputError,
)


__all__ = [
    "ElevenLabsTTSAdapter",
    "ElevenLabsVoiceConfig",
]


@dataclass
class ElevenLabsVoiceConfig(VoiceConfig):
    """
    ElevenLabs-specific voice configuration.

    Attributes:
        stability: Voice stability (0.0-1.0). Lower = more expressive.
        similarity_boost: Voice similarity (0.0-1.0). Higher = more similar to original.
        style_exaggeration: Style intensity (0.0-1.0). Higher = more pronounced style.
        use_speaker_boost: Enable speaker boost for clarity.
    """

    stability: float = 0.5
    similarity_boost: float = 0.75
    style_exaggeration: float = 0.0
    use_speaker_boost: bool = True


class ElevenLabsTTSAdapter(TTSPort):
    """
    ElevenLabs TTS adapter implementation.

    Provides text-to-speech synthesis using ElevenLabs API with support
    for multiple voices, formats, and quality levels.
    """

    # Format mapping: (AudioFormat, AudioQuality) -> ElevenLabs format string
    _FORMAT_MAP = {
        (AudioFormat.MP3, AudioQuality.LOW): "mp3_22050_32",
        (AudioFormat.MP3, AudioQuality.STANDARD): "mp3_44100_128",
        (AudioFormat.MP3, AudioQuality.HIGH): "mp3_44100_192",
        (AudioFormat.PCM, AudioQuality.LOW): "pcm_16000",
        (AudioFormat.PCM, AudioQuality.STANDARD): "pcm_22050",
        (AudioFormat.PCM, AudioQuality.HIGH): "pcm_44100",
        (AudioFormat.OGG_OPUS, AudioQuality.LOW): "opus_16000_32",
        (AudioFormat.OGG_OPUS, AudioQuality.STANDARD): "opus_22050_64",
        (AudioFormat.OGG_OPUS, AudioQuality.HIGH): "opus_44100_128",
    }

    # Reverse mapping for AudioResult population
    _FORMAT_INFO = {
        "mp3_22050_32": {"sample_rate": 22050, "bitrate_kbps": 32},
        "mp3_44100_128": {"sample_rate": 44100, "bitrate_kbps": 128},
        "mp3_44100_192": {"sample_rate": 44100, "bitrate_kbps": 192},
        "pcm_16000": {"sample_rate": 16000, "bitrate_kbps": None},
        "pcm_22050": {"sample_rate": 22050, "bitrate_kbps": None},
        "pcm_44100": {"sample_rate": 44100, "bitrate_kbps": None},
        "opus_16000_32": {"sample_rate": 16000, "bitrate_kbps": 32},
        "opus_22050_64": {"sample_rate": 22050, "bitrate_kbps": 64},
        "opus_44100_128": {"sample_rate": 44100, "bitrate_kbps": 128},
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs adapter.

        Args:
            api_key: ElevenLabs API key. If not provided, reads from
                     ELEVENLABS_API_KEY environment variable.

        Raises:
            TTSAuthenticationError: If no API key is provided or found.
            ImportError: If elevenlabs package is not installed.
        """
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key or set ELEVENLABS_API_KEY env var."
            )

        # Use AsyncElevenLabs for native async support
        try:
            from elevenlabs import AsyncElevenLabs

            self._client = AsyncElevenLabs(api_key=self._api_key)
        except ImportError:
            raise ImportError(
                "elevenlabs package required. Install with: pip install elevenlabs"
            )

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "elevenlabs"

    @property
    def supports_streaming(self) -> bool:
        """ElevenLabs supports streaming."""
        return True

    @property
    def supports_ssml(self) -> bool:
        """ElevenLabs supports SSML."""
        return True

    @property
    def supports_style_prompt(self) -> bool:
        """ElevenLabs uses audio tags instead of style prompts."""
        return False

    @property
    def max_text_length(self) -> int:
        """ElevenLabs maximum text length."""
        return 5000

    async def synthesize(
        self,
        text: str,
        config: VoiceConfig,
        *,
        output_format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.STANDARD,
        model: Optional[str] = None,
    ) -> AudioResult:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            config: Voice configuration (VoiceConfig or ElevenLabsVoiceConfig)
            output_format: Desired audio format
            quality: Audio quality tier
            model: ElevenLabs model ID (default: eleven_multilingual_v2)

        Returns:
            AudioResult with synthesized audio

        Raises:
            TTSInvalidInputError: If text is empty or too long
            TTSInvalidVoiceError: If voice_id is invalid
            TTSError: For other API errors
        """
        # Validation order: validate ORIGINAL text first, then preprocess.
        # This ensures we reject invalid input (empty, too long) before
        # any transformations. Preprocessing may strip tags but won't
        # change validity of the core text content.
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        # Get provider format
        format_str = self._get_provider_format(output_format, quality)
        format_info = self._FORMAT_INFO.get(format_str, {})

        # Build voice settings
        voice_settings = None
        if isinstance(config, ElevenLabsVoiceConfig):
            voice_settings = {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style_exaggeration,
                "use_speaker_boost": config.use_speaker_boost,
            }

        try:
            # Call ElevenLabs API - returns async generator
            audio_stream = self._client.text_to_speech.convert(
                voice_id=config.voice_id,
                text=text,
                model_id=model or "eleven_multilingual_v2",
                output_format=format_str,
                voice_settings=voice_settings,
            )

            # Collect all chunks from the async generator
            chunks = []
            async for chunk in audio_stream:
                chunks.append(chunk)
            audio_bytes = b"".join(chunks)

            return AudioResult(
                audio_bytes=audio_bytes,
                format=output_format,
                sample_rate=format_info.get("sample_rate", 44100),
                bitrate_kbps=format_info.get("bitrate_kbps"),
                channels=1,
                duration_ms=self._calculate_duration(
                    audio_bytes, output_format, format_info
                ),
                input_characters=len(text),
            )

        except Exception as e:
            self._handle_api_error(e)

    async def stream(
        self,
        text: str,
        config: VoiceConfig,
        *,
        output_format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.STANDARD,
        model: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """
        Stream audio chunks as they're generated.

        Args:
            text: Text to synthesize
            config: Voice configuration
            output_format: Desired audio format
            quality: Audio quality tier
            model: ElevenLabs model ID

        Yields:
            Audio data chunks as bytes
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format, quality)

        voice_settings = None
        if isinstance(config, ElevenLabsVoiceConfig):
            voice_settings = {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
            }

        try:
            # Get async stream from ElevenLabs - returns async generator directly
            audio_stream = self._client.text_to_speech.convert_as_stream(
                voice_id=config.voice_id,
                text=text,
                model_id=model or "eleven_multilingual_v2",
                output_format=format_str,
                voice_settings=voice_settings,
            )

            # Async iteration over the stream
            async for chunk in audio_stream:
                yield chunk

        except Exception as e:
            self._handle_api_error(e)

    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """
        List available voices.

        Args:
            language_code: Optional language filter

        Returns:
            List of VoiceInfo objects
        """
        try:
            # Async call to get all voices
            response = await self._client.voices.get_all()
            voices = []

            for voice in response.voices:
                # Safely access labels (may be None or missing)
                labels = getattr(voice, "labels", None) or {}
                voice_languages = labels.get("language", "")

                # Filter by language if specified
                if language_code and language_code.lower() not in voice_languages.lower():
                    continue

                voices.append(
                    VoiceInfo(
                        voice_id=voice.voice_id,
                        name=voice.name,
                        provider="elevenlabs",
                        language_codes=[voice_languages] if voice_languages else [],
                        gender=labels.get("gender"),
                        description=getattr(voice, "description", None),
                        preview_url=getattr(voice, "preview_url", None),
                        supports_ssml=True,
                        supports_streaming=True,
                        is_custom=voice.category == "cloned",
                    )
                )

            return voices

        except Exception as e:
            self._handle_api_error(e)

    def _get_provider_format(self, format: AudioFormat, quality: AudioQuality) -> str:
        """
        Map abstract format+quality to ElevenLabs format string.

        Args:
            format: Desired audio format
            quality: Desired quality level

        Returns:
            ElevenLabs format string

        Raises:
            TTSInvalidInputError: If format/quality combination not supported
        """
        key = (format, quality)
        if key not in self._FORMAT_MAP:
            raise TTSInvalidInputError(
                f"ElevenLabs does not support {format.value} at {quality.value} quality"
            )
        return self._FORMAT_MAP[key]

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert ElevenLabs errors to TTSPort exceptions.

        Uses SDK exception types for reliable detection, with string
        matching fallback for unknown errors.

        Args:
            error: Exception from ElevenLabs SDK

        Raises:
            TTSAuthenticationError: For 401 errors
            TTSRateLimitError: For 429 errors
            TTSInvalidInputError: For 422 errors
            TTSInvalidVoiceError: For 404 errors
            TTSQuotaExceededError: For 402 errors
            TTSNetworkError: For connection errors
            TTSError: For other errors
        """
        # Try SDK-specific exception handling first
        try:
            from elevenlabs.core.api_error import ApiError

            if isinstance(error, ApiError):
                status = getattr(error, "status_code", None)

                if status == 401:
                    raise TTSAuthenticationError(
                        f"ElevenLabs authentication failed: {error}"
                    ) from error

                if status == 429:
                    headers = getattr(error, "headers", {}) or {}
                    retry_after = headers.get("Retry-After")
                    raise TTSRateLimitError(
                        f"ElevenLabs rate limit exceeded: {error}",
                        retry_after_seconds=float(retry_after) if retry_after else None,
                    ) from error

                if status == 422:
                    raise TTSInvalidInputError(
                        f"ElevenLabs invalid input: {error}"
                    ) from error

                if status == 404:
                    raise TTSInvalidVoiceError(
                        f"ElevenLabs voice not found: {error}"
                    ) from error

                if status == 402:
                    raise TTSQuotaExceededError(
                        f"ElevenLabs quota exceeded: {error}"
                    ) from error

        except ImportError:
            pass  # SDK types not available, fall through to string matching

        # Fallback: string matching for unknown errors
        error_str = str(error).lower()

        if "unauthorized" in error_str or "invalid api key" in error_str:
            raise TTSAuthenticationError(
                f"ElevenLabs authentication failed: {error}"
            ) from error

        if "rate limit" in error_str or "too many requests" in error_str:
            raise TTSRateLimitError(
                f"ElevenLabs rate limit exceeded: {error}"
            ) from error

        if "quota" in error_str or "insufficient" in error_str:
            raise TTSQuotaExceededError(
                f"ElevenLabs quota exceeded: {error}"
            ) from error

        if "voice" in error_str and ("not found" in error_str or "invalid" in error_str):
            raise TTSInvalidVoiceError(
                f"ElevenLabs voice not found: {error}"
            ) from error

        if "connection" in error_str or "timeout" in error_str:
            raise TTSNetworkError(f"ElevenLabs network error: {error}") from error

        raise TTSError(f"ElevenLabs error: {error}") from error

    def _calculate_duration(
        self,
        audio_bytes: bytes,
        format: AudioFormat,
        format_info: dict,
    ) -> Optional[int]:
        """
        Calculate audio duration in milliseconds.

        Only accurate for PCM format. Returns None for compressed formats.

        Args:
            audio_bytes: Raw audio data
            format: Audio format
            format_info: Format metadata

        Returns:
            Duration in milliseconds, or None if cannot be calculated
        """
        if format == AudioFormat.PCM:
            sample_rate = format_info.get("sample_rate", 44100)
            # 16-bit mono PCM = 2 bytes per sample
            num_samples = len(audio_bytes) // 2
            return int((num_samples / sample_rate) * 1000)
        return None  # Can't easily calculate for compressed formats
