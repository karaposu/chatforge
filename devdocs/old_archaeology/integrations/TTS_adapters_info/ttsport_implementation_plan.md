# TTSPort Implementation Plan

A detailed step-by-step guide for implementing the TTSPort in Chatforge.

---

## Overview

### What We're Building

| Component | Description |
|-----------|-------------|
| `chatforge/ports/tts.py` | TTSPort interface, exceptions, data classes |
| `chatforge/adapters/tts/__init__.py` | Adapter exports |
| `chatforge/adapters/tts/elevenlabs.py` | ElevenLabs adapter |
| `chatforge/adapters/tts/openai.py` | OpenAI adapter |
| `tests/ports/test_tts.py` | Port unit tests |
| `tests/adapters/tts/test_elevenlabs.py` | ElevenLabs adapter tests |
| `tests/adapters/tts/test_openai.py` | OpenAI adapter tests |

### Dependencies

```toml
# pyproject.toml additions
[project.optional-dependencies]
tts = [
    "elevenlabs>=1.0.0",
    "openai>=1.0.0",
]
tts-elevenlabs = ["elevenlabs>=1.0.0"]
tts-openai = ["openai>=1.0.0"]

# Test dependencies
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

---

## Phase 1: Core Port Interface

**Goal**: Create the foundational port interface that all adapters will implement.

### Step 1.1: Create Port File Structure

```bash
mkdir -p chatforge/ports
mkdir -p chatforge/adapters/tts
touch chatforge/ports/tts.py
touch chatforge/adapters/tts/__init__.py
```

### Step 1.2: Implement Exceptions

**File**: `chatforge/ports/tts.py`

```python
"""
TTS Port - Abstract interface for Text-to-Speech providers.

This port defines the contract for TTS synthesis.
Implementations include ElevenLabs, OpenAI, Azure, and Google Cloud TTS.

The core application depends only on this interface, enabling:
- Easy swapping of TTS providers
- Cost optimization (switch to cheaper provider)
- Fallback strategies
- Mock implementations for testing
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional
from enum import Enum

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
```

**Checklist**:
- [ ] All exceptions defined
- [ ] TTSRateLimitError has retry_after_seconds attribute
- [ ] Proper inheritance hierarchy
- [ ] `__all__` exports defined

### Step 1.3: Implement Enums

```python
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
```

**Checklist**:
- [ ] AudioFormat covers all common formats
- [ ] AudioQuality has clear documentation
- [ ] Both inherit from str for JSON serialization

### Step 1.4: Implement Data Classes

```python
# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class VoiceConfig:
    """
    Base voice configuration - provider-agnostic.

    For provider-specific settings, use the provider's config subclass.
    """
    voice_id: str
    language_code: str = "en-US"
    speed: float = 1.0  # 0.25 - 4.0


@dataclass
class AudioResult:
    """Result from TTS synthesis."""
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
    """Voice metadata from provider."""
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
```

**Checklist**:
- [ ] VoiceConfig has sensible defaults
- [ ] AudioResult includes all metadata fields
- [ ] VoiceInfo uses field(default_factory=list) for mutable defaults

### Step 1.5: Implement TTSPort Abstract Class

```python
# =============================================================================
# TTSPort Interface
# =============================================================================

class TTSPort(ABC):
    """
    Abstract port interface for Text-to-Speech providers.

    All methods are async-first. Adapters must implement abstract methods.
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
        """Convert text to speech, return complete audio."""
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
        """Stream audio chunks as they're generated."""
        pass

    @abstractmethod
    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """List available voices, optionally filtered by language."""
        pass

    # -------------------------------------------------------------------------
    # Utility Methods (with default implementations)
    # -------------------------------------------------------------------------

    async def get_voice(self, voice_id: str) -> Optional[VoiceInfo]:
        """Get info for a specific voice."""
        voices = await self.list_voices()
        return next((v for v in voices if v.voice_id == voice_id), None)

    def _validate_input(self, text: str, config: VoiceConfig) -> None:
        """Validate input before synthesis."""
        if not text or not text.strip():
            raise TTSInvalidInputError("Text cannot be empty")
        self._validate_text_length(text)

    def _validate_text_length(self, text: str) -> None:
        """Validate text length."""
        if len(text) > self.max_text_length:
            raise TTSInvalidInputError(
                f"Text length {len(text)} exceeds {self.provider_name} "
                f"limit of {self.max_text_length} characters."
            )

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """Internal hook for text preprocessing."""
        return text

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Release resources."""
        pass

    async def __aenter__(self) -> "TTSPort":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
```

**Checklist**:
- [ ] All abstract properties defined
- [ ] All abstract methods defined
- [ ] Default implementations for utility methods
- [ ] Async context manager support
- [ ] Proper type hints throughout

---

## Phase 2: ElevenLabs Adapter

**Goal**: Implement the first concrete adapter for ElevenLabs.

### Step 2.1: Create Adapter File

**File**: `chatforge/adapters/tts/elevenlabs.py`

```python
"""
ElevenLabs TTS Adapter

Implements TTSPort for ElevenLabs text-to-speech API.
Supports both HTTP streaming and standard synthesis.
"""

import os
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
```

### Step 2.2: Implement ElevenLabsVoiceConfig

```python
from dataclasses import dataclass

@dataclass
class ElevenLabsVoiceConfig(VoiceConfig):
    """ElevenLabs-specific voice configuration."""
    stability: float = 0.5
    similarity_boost: float = 0.75
    style_exaggeration: float = 0.0
    use_speaker_boost: bool = True
```

### Step 2.3: Implement Format Mapping

```python
class ElevenLabsTTSAdapter(TTSPort):
    """ElevenLabs TTS adapter implementation."""

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
```

### Step 2.4: Implement Constructor and Properties

```python
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs adapter.

        Args:
            api_key: ElevenLabs API key. If not provided, reads from
                     ELEVENLABS_API_KEY environment variable.
        """
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key or set ELEVENLABS_API_KEY env var."
            )

        # Lazy import to avoid dependency if not using ElevenLabs
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
        return "elevenlabs"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_ssml(self) -> bool:
        return True

    @property
    def supports_style_prompt(self) -> bool:
        return False  # Uses audio tags instead

    @property
    def max_text_length(self) -> int:
        return 5000
```

### Step 2.5: Implement synthesize()

```python
    async def synthesize(
        self,
        text: str,
        config: VoiceConfig,
        *,
        output_format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.STANDARD,
        model: Optional[str] = None,
    ) -> AudioResult:
        """Synthesize text to speech."""
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
            # Call ElevenLabs API (async)
            audio_bytes = await self._client.text_to_speech.convert(
                voice_id=config.voice_id,
                text=text,
                model_id=model or "eleven_multilingual_v2",
                output_format=format_str,
                voice_settings=voice_settings,
            )

            # Collect bytes if async generator
            if hasattr(audio_bytes, '__aiter__'):
                chunks = []
                async for chunk in audio_bytes:
                    chunks.append(chunk)
                audio_bytes = b"".join(chunks)
            elif hasattr(audio_bytes, '__iter__') and not isinstance(audio_bytes, bytes):
                audio_bytes = b"".join(audio_bytes)

            return AudioResult(
                audio_bytes=audio_bytes,
                format=output_format,
                sample_rate=format_info.get("sample_rate", 44100),
                bitrate_kbps=format_info.get("bitrate_kbps"),
                channels=1,
                duration_ms=self._calculate_duration(audio_bytes, output_format, format_info),
                input_characters=len(text),
            )

        except Exception as e:
            self._handle_api_error(e)

    def _get_provider_format(self, format: AudioFormat, quality: AudioQuality) -> str:
        """Map abstract format+quality to ElevenLabs format string."""
        key = (format, quality)
        if key not in self._FORMAT_MAP:
            raise TTSInvalidInputError(
                f"ElevenLabs does not support {format.value} at {quality.value} quality"
            )
        return self._FORMAT_MAP[key]
```

### Step 2.6: Implement stream()

```python
    async def stream(
        self,
        text: str,
        config: VoiceConfig,
        *,
        output_format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.STANDARD,
        model: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks."""
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
            # Get async stream from ElevenLabs
            audio_stream = await self._client.text_to_speech.convert_as_stream(
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
```

### Step 2.7: Implement list_voices()

```python
    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """List available voices."""
        try:
            # Async call to get all voices
            response = await self._client.voices.get_all()
            voices = []

            for voice in response.voices:
                # Safely access labels (may be None or missing)
                labels = getattr(voice, 'labels', None) or {}
                voice_languages = labels.get('language', '')

                # Filter by language if specified
                if language_code and language_code.lower() not in voice_languages.lower():
                    continue

                voices.append(VoiceInfo(
                    voice_id=voice.voice_id,
                    name=voice.name,
                    provider="elevenlabs",
                    language_codes=[voice_languages] if voice_languages else [],
                    gender=labels.get('gender'),
                    description=getattr(voice, 'description', None),
                    preview_url=getattr(voice, 'preview_url', None),
                    supports_ssml=True,
                    supports_streaming=True,
                    is_custom=voice.category == "cloned",
                ))

            return voices

        except Exception as e:
            self._handle_api_error(e)
```

### Step 2.8: Implement Error Handling

```python
    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert ElevenLabs errors to TTSPort exceptions.

        Uses SDK exception types for reliable detection, with string
        matching fallback for unknown errors.
        """
        # Try SDK-specific exception handling first
        try:
            from elevenlabs.core.api_error import ApiError

            if isinstance(error, ApiError):
                status = getattr(error, 'status_code', None)

                if status == 401:
                    raise TTSAuthenticationError(
                        f"ElevenLabs authentication failed: {error}"
                    ) from error

                if status == 429:
                    headers = getattr(error, 'headers', {}) or {}
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
            raise TTSAuthenticationError(f"ElevenLabs authentication failed: {error}") from error

        if "rate limit" in error_str or "too many requests" in error_str:
            raise TTSRateLimitError(f"ElevenLabs rate limit exceeded: {error}") from error

        if "quota" in error_str or "insufficient" in error_str:
            raise TTSQuotaExceededError(f"ElevenLabs quota exceeded: {error}") from error

        if "voice" in error_str and ("not found" in error_str or "invalid" in error_str):
            raise TTSInvalidVoiceError(f"ElevenLabs voice not found: {error}") from error

        if "connection" in error_str or "timeout" in error_str:
            raise TTSNetworkError(f"ElevenLabs network error: {error}") from error

        raise TTSError(f"ElevenLabs error: {error}") from error

    def _calculate_duration(
        self,
        audio_bytes: bytes,
        format: AudioFormat,
        format_info: dict,
    ) -> Optional[int]:
        """Calculate audio duration in milliseconds."""
        if format == AudioFormat.PCM:
            sample_rate = format_info.get("sample_rate", 44100)
            # 16-bit mono PCM = 2 bytes per sample
            num_samples = len(audio_bytes) // 2
            return int((num_samples / sample_rate) * 1000)
        return None  # Can't easily calculate for compressed formats
```

**Checklist**:
- [ ] Constructor with api_key and env var fallback
- [ ] All abstract properties implemented
- [ ] synthesize() with full AudioResult
- [ ] stream() as async generator
- [ ] list_voices() with filtering
- [ ] Error mapping to TTS exceptions
- [ ] Duration calculation for PCM

---

## Phase 3: OpenAI Adapter

**Goal**: Implement the second adapter for OpenAI TTS.

### Step 3.1: Create Adapter File

**File**: `chatforge/adapters/tts/openai.py`

```python
"""
OpenAI TTS Adapter

Implements TTSPort for OpenAI text-to-speech API.
Supports style prompts via instructions parameter.
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
    TTSStreamingNotSupportedError,
)

__all__ = [
    "OpenAITTSAdapter",
    "OpenAIVoiceConfig",
]


@dataclass
class OpenAIVoiceConfig(VoiceConfig):
    """OpenAI-specific voice configuration."""
    style_prompt: Optional[str] = None
```

### Step 3.2: Implement OpenAITTSAdapter

```python
class OpenAITTSAdapter(TTSPort):
    """OpenAI TTS adapter implementation."""

    # OpenAI supports these formats (no quality control)
    _FORMAT_MAP = {
        AudioFormat.MP3: "mp3",
        AudioFormat.WAV: "wav",
        AudioFormat.FLAC: "flac",
        AudioFormat.AAC: "aac",
        AudioFormat.OGG_OPUS: "opus",
        AudioFormat.PCM: "pcm",
    }

    # Available voices
    _VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable",
               "nova", "onyx", "sage", "shimmer", "verse"]

    def __init__(self, api_key: Optional[str] = None):
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
        return "openai"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_ssml(self) -> bool:
        return False

    @property
    def supports_style_prompt(self) -> bool:
        return True

    @property
    def max_text_length(self) -> int:
        return 4096

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """Strip ElevenLabs audio tags that OpenAI doesn't support."""
        return re.sub(r'\[(whispers|laughs|pause|sighs)\]', '', text)

    async def synthesize(
        self,
        text: str,
        config: VoiceConfig,
        *,
        output_format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.STANDARD,
        model: Optional[str] = None,
    ) -> AudioResult:
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format)

        # Build request kwargs
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
        # OpenAI has fixed voices, no API to list them
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
        if format not in self._FORMAT_MAP:
            raise TTSInvalidInputError(f"OpenAI does not support {format.value}")
        return self._FORMAT_MAP[format]

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert OpenAI errors to TTSPort exceptions.

        Uses SDK exception types for reliable detection, with string
        matching fallback for unknown errors.
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
                if hasattr(error, 'response') and error.response:
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
            raise TTSAuthenticationError(f"OpenAI authentication failed: {error}") from error

        if "rate_limit" in error_str:
            raise TTSRateLimitError(f"OpenAI rate limit exceeded: {error}") from error

        if "insufficient_quota" in error_str:
            raise TTSQuotaExceededError(f"OpenAI quota exceeded: {error}") from error

        if "invalid_voice" in error_str:
            raise TTSInvalidVoiceError(f"OpenAI voice not found: {error}") from error

        if "connection" in error_str or "timeout" in error_str:
            raise TTSNetworkError(f"OpenAI network error: {error}") from error

        raise TTSError(f"OpenAI error: {error}") from error
```

**Checklist**:
- [ ] OpenAIVoiceConfig with style_prompt
- [ ] _preprocess_text strips audio tags
- [ ] synthesize() with instructions support
- [ ] stream() using with_streaming_response
- [ ] list_voices() returns static list
- [ ] Error mapping

---

## Phase 4: Adapter Package Setup

### Step 4.1: Create __init__.py

**File**: `chatforge/adapters/tts/__init__.py`

```python
"""
TTS Adapters

Concrete implementations of the TTSPort interface.
"""

from chatforge.adapters.tts.elevenlabs import (
    ElevenLabsTTSAdapter,
    ElevenLabsVoiceConfig,
)
from chatforge.adapters.tts.openai import (
    OpenAITTSAdapter,
    OpenAIVoiceConfig,
)

__all__ = [
    "ElevenLabsTTSAdapter",
    "ElevenLabsVoiceConfig",
    "OpenAITTSAdapter",
    "OpenAIVoiceConfig",
]
```

### Step 4.2: Update Main Package __init__.py

Add to `chatforge/__init__.py`:

```python
# TTS Port and Adapters
from chatforge.ports.tts import (
    TTSPort,
    VoiceConfig,
    AudioResult,
    VoiceInfo,
    AudioFormat,
    AudioQuality,
    TTSError,
)
```

---

## Phase 5: Testing

### Step 5.1: Port Unit Tests

**File**: `tests/ports/test_tts.py`

```python
"""Unit tests for TTSPort interface."""

import pytest
from dataclasses import dataclass
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
        return [
            VoiceInfo(voice_id="v1", name="Voice 1", provider="mock"),
            VoiceInfo(voice_id="v2", name="Voice 2", provider="mock"),
        ]


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
    async def test_valid_text_succeeds(self, adapter):
        """Verify that valid text synthesizes successfully."""
        config = VoiceConfig(voice_id="test")
        result = await adapter.synthesize("Hello", config)
        assert result.audio_bytes == b"mock audio data"
        assert result.input_characters == 5

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, adapter):
        """Verify that stream() yields audio chunks."""
        config = VoiceConfig(voice_id="test")
        chunks = []
        async for chunk in adapter.stream("Hello", config):
            chunks.append(chunk)
        assert len(chunks) == 2
        assert chunks[0] == b"chunk1"

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


class TestAudioFormat:
    """Test AudioFormat enum."""

    def test_format_values(self):
        """Verify enum values match expected strings."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG_OPUS.value == "ogg_opus"

    def test_format_is_string(self):
        """Verify AudioFormat inherits from str for JSON serialization."""
        assert isinstance(AudioFormat.MP3, str)
```

### Step 5.2: ElevenLabs Adapter Tests

**File**: `tests/adapters/tts/test_elevenlabs.py`

```python
"""Tests for ElevenLabs TTS adapter."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from chatforge.adapters.tts.elevenlabs import (
    ElevenLabsTTSAdapter,
    ElevenLabsVoiceConfig,
)
from chatforge.ports.tts import (
    AudioFormat,
    AudioQuality,
    TTSAuthenticationError,
)


class TestElevenLabsAdapter:
    """Test ElevenLabs adapter initialization and properties."""

    def test_requires_api_key(self):
        """Verify that adapter raises error when no API key is provided."""
        import os
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSAuthenticationError):
                ElevenLabsTTSAdapter()

    def test_accepts_explicit_api_key(self):
        """Verify that explicit api_key parameter is accepted."""
        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
            adapter = ElevenLabsTTSAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"

    def test_reads_env_var(self):
        """Verify that API key is read from environment variable."""
        import os
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'env-key'}):
            with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
                adapter = ElevenLabsTTSAdapter()
                assert adapter._api_key == "env-key"

    def test_properties(self):
        """Verify adapter properties return expected values."""
        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
            adapter = ElevenLabsTTSAdapter(api_key="test")
            assert adapter.provider_name == "elevenlabs"
            assert adapter.supports_streaming is True
            assert adapter.supports_ssml is True
            assert adapter.max_text_length == 5000

    def test_format_mapping(self):
        """Verify format+quality maps to correct provider format string."""
        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
            adapter = ElevenLabsTTSAdapter(api_key="test")
            assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.HIGH) == "mp3_44100_192"
            assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.LOW) == "mp3_22050_32"
            assert adapter._get_provider_format(AudioFormat.PCM, AudioQuality.STANDARD) == "pcm_22050"
```

### Step 5.3: Integration Tests (Manual)

**File**: `tests/adapters/tts/test_integration.py`

```python
"""
Integration tests for TTS adapters.

These tests require actual API keys and make real API calls.
Run with: pytest tests/adapters/tts/test_integration.py -v --run-integration
"""

import pytest
import os

# Skip all tests if no API keys
pytestmark = pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY") and not os.getenv("OPENAI_API_KEY"),
    reason="No TTS API keys configured"
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

    @pytest.mark.asyncio
    async def test_list_voices(self):
        """Test that list_voices returns available voices from the account."""
        from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter

        async with ElevenLabsTTSAdapter() as tts:
            voices = await tts.list_voices()
            assert len(voices) > 0
            assert all(v.provider == "elevenlabs" for v in voices)
```

---

## Phase 6: Documentation

### Step 6.1: Update Package Documentation

Add docstrings and usage examples to all modules.

### Step 6.2: Create README for TTS

**File**: `chatforge/adapters/tts/README.md`

```markdown
# TTS Adapters

Text-to-Speech adapters for Chatforge.

## Quick Start

```python
from chatforge.adapters.tts import ElevenLabsTTSAdapter
from chatforge.ports.tts import VoiceConfig

async with ElevenLabsTTSAdapter() as tts:
    config = VoiceConfig(voice_id="your-voice-id")
    result = await tts.synthesize("Hello world", config)

    with open("output.mp3", "wb") as f:
        f.write(result.audio_bytes)
```

## Available Adapters

- `ElevenLabsTTSAdapter` - ElevenLabs API
- `OpenAITTSAdapter` - OpenAI TTS API

## Environment Variables

- `ELEVENLABS_API_KEY` - ElevenLabs API key
- `OPENAI_API_KEY` - OpenAI API key
```

---

## Implementation Order Summary

| Step | Component | Estimated Effort |
|------|-----------|------------------|
| 1 | Port interface (exceptions, enums, dataclasses, TTSPort) | Medium |
| 2 | ElevenLabs adapter | Medium |
| 3 | OpenAI adapter | Medium |
| 4 | Package setup (__init__.py files) | Low |
| 5 | Unit tests | Medium |
| 6 | Integration tests | Low |
| 7 | Documentation | Low |

---

## Potential Challenges

### 1. Async Generator Return Type
The `stream()` method returns `AsyncIterator[bytes]` but is declared with `@abstractmethod`. Python's type system handles this fine, but ensure tests verify the async iteration works.

### 2. ElevenLabs SDK Changes
The ElevenLabs SDK may change. Pin version in requirements and handle API differences gracefully.

### 3. Error Message Parsing
Error detection relies on string matching. This is fragile - consider using SDK-specific exception types when available.

### 4. Format Mapping Completeness
Not all format/quality combinations may be valid. Validate against provider documentation.

---

## Success Criteria

- [ ] All tests pass
- [ ] Both adapters work with real API keys
- [ ] Error handling covers common failure modes
- [ ] Documentation is complete
- [ ] Package exports are correct
- [ ] Type hints are complete and correct
