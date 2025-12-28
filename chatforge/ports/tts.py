"""
TTS Port - Abstract interface for Text-to-Speech providers.

This port defines the contract for TTS synthesis.
Implementations include ElevenLabs, OpenAI, Azure, and Google Cloud TTS.

The core application depends only on this interface, enabling:
- Easy swapping of TTS providers
- Cost optimization (switch to cheaper provider)
- Fallback strategies
- Mock implementations for testing

Usage:
    from chatforge.ports.tts import TTSPort, VoiceConfig, AudioFormat

    async with MyTTSAdapter() as tts:
        config = VoiceConfig(voice_id="voice-123")
        result = await tts.synthesize("Hello world", config)

        with open("output.mp3", "wb") as f:
            f.write(result.audio_bytes)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional


__all__ = [
    # Exceptions
    "TTSError",
    "TTSNetworkError",
    "TTSAuthenticationError",
    "TTSQuotaExceededError",
    "TTSRateLimitError",
    "TTSInvalidVoiceError",
    "TTSInvalidInputError",
    "TTSStreamingNotSupportedError",
    # Enums
    "AudioFormat",
    "AudioQuality",
    # Data classes
    "VoiceConfig",
    "AudioResult",
    "VoiceInfo",
    # Port
    "TTSPort",
]


# =============================================================================
# Exceptions
# =============================================================================


class TTSError(Exception):
    """Base exception for all TTS errors."""

    pass


class TTSNetworkError(TTSError):
    """Network connectivity or timeout errors."""

    pass


class TTSAuthenticationError(TTSError):
    """Invalid or expired API key."""

    pass


class TTSQuotaExceededError(TTSError):
    """Usage quota or credit limit exceeded."""

    pass


class TTSRateLimitError(TTSError):
    """Too many requests, rate limited."""

    def __init__(self, message: str, retry_after_seconds: Optional[float] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class TTSInvalidVoiceError(TTSError):
    """Voice ID not found or not accessible."""

    pass


class TTSInvalidInputError(TTSError):
    """Invalid input text (too long, invalid characters, bad SSML)."""

    pass


class TTSStreamingNotSupportedError(TTSError):
    """Provider does not support streaming synthesis."""

    pass


# =============================================================================
# Enums
# =============================================================================


class AudioFormat(str, Enum):
    """Common audio formats across providers."""

    MP3 = "mp3"
    WAV = "wav"
    OGG_OPUS = "ogg_opus"
    PCM = "pcm"
    FLAC = "flac"
    AAC = "aac"


class AudioQuality(str, Enum):
    """
    Audio quality tier - adapters map to provider-specific formats.

    LOW: Smallest file size, acceptable quality (e.g., 22kHz, 32kbps)
    STANDARD: Balanced quality and size (e.g., 44.1kHz, 128kbps)
    HIGH: Best quality, larger files (e.g., 48kHz, 192kbps)
    """

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class VoiceConfig:
    """
    Base voice configuration - provider-agnostic.

    For provider-specific settings, use the provider's config subclass
    (e.g., ElevenLabsVoiceConfig, OpenAIVoiceConfig).

    Attributes:
        voice_id: Provider-specific voice identifier
        language_code: BCP-47 language code (default: en-US)
        speed: Speech rate multiplier (0.25 - 4.0, default: 1.0)
    """

    voice_id: str
    language_code: str = "en-US"
    speed: float = 1.0  # 0.25 - 4.0


@dataclass
class AudioResult:
    """
    Result from TTS synthesis.

    Attributes:
        audio_bytes: Raw audio data
        format: Audio format (MP3, WAV, etc.)
        sample_rate: Sample rate in Hz (e.g., 44100)
        bitrate_kbps: Bitrate in kbps (for compressed formats)
        channels: Number of audio channels (1=mono, 2=stereo)
        duration_ms: Audio duration in milliseconds
        input_characters: Number of input characters
        billed_characters: Characters billed (may differ from input)
        word_timestamps: Optional word-level timing info
        request_id: Provider request ID for debugging
    """

    audio_bytes: bytes
    format: AudioFormat
    sample_rate: int = 44100
    bitrate_kbps: Optional[int] = None
    channels: int = 1
    duration_ms: Optional[int] = None
    input_characters: int = 0
    billed_characters: Optional[int] = None
    word_timestamps: Optional[list] = None
    request_id: Optional[str] = None


@dataclass
class VoiceInfo:
    """
    Voice metadata from provider.

    Attributes:
        voice_id: Provider-specific voice identifier
        name: Human-readable voice name
        provider: Provider name (elevenlabs, openai, etc.)
        language_codes: Supported language codes
        gender: Voice gender (male, female, neutral)
        description: Voice description
        preview_url: URL to voice sample
        supports_ssml: Whether SSML input is supported
        supports_streaming: Whether streaming is supported
        is_custom: Whether this is a cloned/custom voice
        quality_tier: Provider's quality tier label
    """

    voice_id: str
    name: str
    provider: str
    language_codes: list[str] = field(default_factory=list)
    gender: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    supports_ssml: bool = False
    supports_streaming: bool = True
    is_custom: bool = False
    quality_tier: Optional[str] = None


# =============================================================================
# TTSPort Interface
# =============================================================================


class TTSPort(ABC):
    """
    Abstract port interface for Text-to-Speech providers.

    All methods are async-first. Adapters must implement abstract methods.

    Example:
        async with ElevenLabsTTSAdapter() as tts:
            config = VoiceConfig(voice_id="voice-123")

            # Full synthesis
            result = await tts.synthesize("Hello world", config)

            # Streaming
            async for chunk in tts.stream("Hello world", config):
                audio_player.write(chunk)

            # List voices
            voices = await tts.list_voices(language_code="en")
    """

    # -------------------------------------------------------------------------
    # Abstract Properties
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'elevenlabs', 'openai')."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this adapter supports streaming synthesis."""
        pass

    @property
    @abstractmethod
    def supports_ssml(self) -> bool:
        """Whether this adapter supports SSML input."""
        pass

    @property
    @abstractmethod
    def supports_style_prompt(self) -> bool:
        """Whether this adapter supports natural language style prompts."""
        pass

    @property
    @abstractmethod
    def max_text_length(self) -> int:
        """Maximum characters per synthesis request."""
        pass

    # -------------------------------------------------------------------------
    # Abstract Methods
    # -------------------------------------------------------------------------

    @abstractmethod
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
        Convert text to speech, return complete audio.

        Args:
            text: Text to synthesize
            config: Voice configuration
            output_format: Desired audio format
            quality: Audio quality tier
            model: Provider-specific model override

        Returns:
            AudioResult with audio bytes and metadata

        Raises:
            TTSInvalidInputError: If text is empty or too long
            TTSInvalidVoiceError: If voice_id is invalid
            TTSAuthenticationError: If API key is invalid
            TTSRateLimitError: If rate limited
            TTSNetworkError: If network error occurs
        """
        pass

    @abstractmethod
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
            model: Provider-specific model override

        Yields:
            Audio data chunks as bytes

        Raises:
            TTSStreamingNotSupportedError: If streaming not supported
            TTSInvalidInputError: If text is empty or too long
            TTSInvalidVoiceError: If voice_id is invalid
        """
        pass

    @abstractmethod
    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """
        List available voices, optionally filtered by language.

        Args:
            language_code: Optional language filter (e.g., "en", "en-US")

        Returns:
            List of VoiceInfo objects
        """
        pass

    # -------------------------------------------------------------------------
    # Utility Methods (with default implementations)
    # -------------------------------------------------------------------------

    async def get_voice(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        Get info for a specific voice.

        Args:
            voice_id: Voice identifier to look up

        Returns:
            VoiceInfo if found, None otherwise
        """
        voices = await self.list_voices()
        return next((v for v in voices if v.voice_id == voice_id), None)

    def _validate_input(self, text: str, config: VoiceConfig) -> None:
        """
        Validate input before synthesis.

        Args:
            text: Text to validate
            config: Voice configuration

        Raises:
            TTSInvalidInputError: If validation fails
        """
        if not text or not text.strip():
            raise TTSInvalidInputError("Text cannot be empty")
        self._validate_text_length(text)

    def _validate_text_length(self, text: str) -> None:
        """
        Validate text length against provider limit.

        Args:
            text: Text to validate

        Raises:
            TTSInvalidInputError: If text exceeds max length
        """
        if len(text) > self.max_text_length:
            raise TTSInvalidInputError(
                f"Text length {len(text)} exceeds {self.provider_name} "
                f"limit of {self.max_text_length} characters."
            )

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """
        Internal hook for text preprocessing.

        Override in subclasses to strip unsupported tags, normalize text, etc.

        Args:
            text: Text to preprocess
            config: Voice configuration

        Returns:
            Preprocessed text
        """
        return text

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """
        Release resources.

        Override in subclasses if cleanup is needed (e.g., closing HTTP clients).
        """
        pass

    async def __aenter__(self) -> "TTSPort":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context manager, releasing resources."""
        await self.close()
