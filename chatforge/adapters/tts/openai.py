"""
OpenAI TTS Adapter

Implements TTSPort for OpenAI text-to-speech API.
Supports style prompts via instructions parameter.

Features:
- Multiple voice options (alloy, echo, fable, onyx, nova, shimmer, etc.)
- Style prompts for natural language voice direction
- Two quality tiers (tts-1 for speed, tts-1-hd for quality)
- Multiple output formats
- Async streaming

Usage:
    from chatforge.adapters.tts import OpenAITTSAdapter, OpenAIVoiceConfig

    async with OpenAITTSAdapter() as tts:
        config = OpenAIVoiceConfig(
            voice_id="nova",
            style_prompt="Speak in a warm, friendly tone",
        )
        result = await tts.synthesize("Hello world", config)

Environment Variables:
    OPENAI_API_KEY: OpenAI API key
"""

import os
import re
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
    "OpenAITTSAdapter",
    "OpenAIVoiceConfig",
]


@dataclass
class OpenAIVoiceConfig(VoiceConfig):
    """
    OpenAI-specific voice configuration.

    Attributes:
        style_prompt: Natural language instructions for voice style.
                      Example: "Speak in a warm, friendly tone"
    """

    style_prompt: Optional[str] = None


class OpenAITTSAdapter(TTSPort):
    """
    OpenAI TTS adapter implementation.

    Provides text-to-speech synthesis using OpenAI's TTS API with support
    for multiple voices and style prompts.
    """

    # OpenAI supports these formats (no quality control per format)
    _FORMAT_MAP = {
        AudioFormat.MP3: "mp3",
        AudioFormat.WAV: "wav",
        AudioFormat.FLAC: "flac",
        AudioFormat.AAC: "aac",
        AudioFormat.OGG_OPUS: "opus",
        AudioFormat.PCM: "pcm",
    }

    # Available voices
    _VOICES = [
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "nova",
        "onyx",
        "sage",
        "shimmer",
        "verse",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key. If not provided, reads from
                     OPENAI_API_KEY environment variable.

        Raises:
            TTSAuthenticationError: If no API key is provided or found.
            ImportError: If openai package is not installed.
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key or set OPENAI_API_KEY env var."
            )

        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key)
        except ImportError:
            raise ImportError(
                "openai package required. Install with: pip install openai"
            )

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai"

    @property
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True

    @property
    def supports_ssml(self) -> bool:
        """OpenAI does not support SSML."""
        return False

    @property
    def supports_style_prompt(self) -> bool:
        """OpenAI supports natural language style prompts."""
        return True

    @property
    def max_text_length(self) -> int:
        """OpenAI maximum text length."""
        return 4096

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """
        Strip ElevenLabs audio tags that OpenAI doesn't support.

        Args:
            text: Text to preprocess
            config: Voice configuration

        Returns:
            Preprocessed text with audio tags removed
        """
        return re.sub(r"\[(whispers|laughs|pause|sighs)\]", "", text)

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
            config: Voice configuration (VoiceConfig or OpenAIVoiceConfig)
            output_format: Desired audio format
            quality: Audio quality tier (maps to tts-1 vs tts-1-hd)
            model: OpenAI model ID override

        Returns:
            AudioResult with synthesized audio

        Raises:
            TTSInvalidInputError: If text is empty or too long
            TTSInvalidVoiceError: If voice_id is invalid
            TTSError: For other API errors
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format)

        # Use tts-1 for standard quality, tts-1-hd for high quality
        selected_model = model
        if selected_model is None:
            selected_model = "tts-1-hd" if quality == AudioQuality.HIGH else "tts-1"

        kwargs = {
            "model": selected_model,
            "voice": config.voice_id,
            "input": text,
            "response_format": format_str,
            "speed": config.speed,  # OpenAI supports 0.25 - 4.0
        }

        # Add style prompt if using OpenAIVoiceConfig
        if isinstance(config, OpenAIVoiceConfig) and config.style_prompt:
            kwargs["instructions"] = config.style_prompt

        try:
            response = await self._client.audio.speech.create(**kwargs)
            audio_bytes = response.content

            return AudioResult(
                audio_bytes=audio_bytes,
                format=output_format,
                sample_rate=24000,  # OpenAI default
                channels=1,
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
            model: OpenAI model ID

        Yields:
            Audio data chunks as bytes
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format)

        # Use tts-1 for standard quality, tts-1-hd for high quality
        selected_model = model
        if selected_model is None:
            selected_model = "tts-1-hd" if quality == AudioQuality.HIGH else "tts-1"

        kwargs = {
            "model": selected_model,
            "voice": config.voice_id,
            "input": text,
            "response_format": format_str,
            "speed": config.speed,
        }

        if isinstance(config, OpenAIVoiceConfig) and config.style_prompt:
            kwargs["instructions"] = config.style_prompt

        try:
            async with self._client.audio.speech.with_streaming_response.create(
                **kwargs
            ) as response:
                async for chunk in response.iter_bytes():
                    yield chunk

        except Exception as e:
            self._handle_api_error(e)

    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """
        List available voices.

        OpenAI has fixed voices, no API to list them dynamically.
        All voices are optimized for English but work with other languages.

        Args:
            language_code: Ignored (OpenAI voices are multilingual)

        Returns:
            List of VoiceInfo objects for all available voices
        """
        return [
            VoiceInfo(
                voice_id=voice,
                name=voice.title(),
                provider="openai",
                language_codes=["en-US"],  # Optimized for English
                supports_ssml=False,
                supports_streaming=True,
            )
            for voice in self._VOICES
        ]

    def _get_provider_format(self, format: AudioFormat) -> str:
        """
        Map abstract format to OpenAI format string.

        Note: OpenAI doesn't support quality tiers per format.
        Use model selection (tts-1 vs tts-1-hd) for quality control.

        Args:
            format: Desired audio format

        Returns:
            OpenAI format string

        Raises:
            TTSInvalidInputError: If format not supported
        """
        if format not in self._FORMAT_MAP:
            raise TTSInvalidInputError(f"OpenAI does not support {format.value}")
        return self._FORMAT_MAP[format]

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert OpenAI errors to TTSPort exceptions.

        Uses SDK exception types for reliable detection, with string
        matching fallback for unknown errors.

        Args:
            error: Exception from OpenAI SDK

        Raises:
            TTSAuthenticationError: For authentication errors
            TTSRateLimitError: For rate limit errors
            TTSInvalidInputError: For bad request errors
            TTSInvalidVoiceError: For voice not found errors
            TTSQuotaExceededError: For quota errors
            TTSNetworkError: For connection errors
            TTSError: For other errors
        """
        # Try SDK-specific exception handling first
        try:
            from openai import (
                APIError,
                AuthenticationError,
                RateLimitError,
                BadRequestError,
                NotFoundError,
            )

            if isinstance(error, AuthenticationError):
                raise TTSAuthenticationError(
                    f"OpenAI authentication failed: {error}"
                ) from error

            if isinstance(error, RateLimitError):
                retry_after = None
                if hasattr(error, "response") and error.response:
                    retry_after_str = error.response.headers.get("Retry-After")
                    if retry_after_str:
                        retry_after = float(retry_after_str)
                raise TTSRateLimitError(
                    f"OpenAI rate limit exceeded: {error}",
                    retry_after_seconds=retry_after,
                ) from error

            if isinstance(error, BadRequestError):
                error_str = str(error).lower()
                if "voice" in error_str:
                    raise TTSInvalidVoiceError(
                        f"OpenAI invalid voice: {error}"
                    ) from error
                raise TTSInvalidInputError(
                    f"OpenAI invalid request: {error}"
                ) from error

            if isinstance(error, NotFoundError):
                raise TTSInvalidVoiceError(
                    f"OpenAI voice not found: {error}"
                ) from error

            if isinstance(error, APIError):
                if "insufficient_quota" in str(error).lower():
                    raise TTSQuotaExceededError(
                        f"OpenAI quota exceeded: {error}"
                    ) from error
                raise TTSError(f"OpenAI API error: {error}") from error

        except ImportError:
            pass  # SDK types not available, fall through to string matching

        # Fallback: string matching for unknown errors
        error_str = str(error).lower()

        if "invalid_api_key" in error_str or "unauthorized" in error_str:
            raise TTSAuthenticationError(
                f"OpenAI authentication failed: {error}"
            ) from error

        if "rate_limit" in error_str:
            raise TTSRateLimitError(
                f"OpenAI rate limit exceeded: {error}"
            ) from error

        if "insufficient_quota" in error_str:
            raise TTSQuotaExceededError(
                f"OpenAI quota exceeded: {error}"
            ) from error

        if "invalid_voice" in error_str:
            raise TTSInvalidVoiceError(
                f"OpenAI voice not found: {error}"
            ) from error

        if "connection" in error_str or "timeout" in error_str:
            raise TTSNetworkError(f"OpenAI network error: {error}") from error

        raise TTSError(f"OpenAI error: {error}") from error
