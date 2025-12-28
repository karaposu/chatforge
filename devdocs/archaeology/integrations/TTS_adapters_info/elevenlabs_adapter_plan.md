# ElevenLabs Adapter Implementation Plan

Detailed implementation guide for the ElevenLabs TTS adapter.

---

## Overview

| Aspect | Details |
|--------|---------|
| **File** | `chatforge/adapters/tts/elevenlabs.py` |
| **SDK** | `elevenlabs` (AsyncElevenLabs) |
| **API Docs** | https://elevenlabs.io/docs/api-reference |
| **Features** | Streaming, SSML, audio tags, voice cloning, word timestamps |

---

## Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
tts-elevenlabs = ["elevenlabs>=1.0.0"]
```

---

## Complete Implementation

```python
"""
ElevenLabs TTS Adapter

Implements TTSPort for ElevenLabs text-to-speech API.
Uses AsyncElevenLabs for native async support.
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


# =============================================================================
# Provider-Specific Config
# =============================================================================

@dataclass
class ElevenLabsVoiceConfig(VoiceConfig):
    """
    ElevenLabs-specific voice configuration.

    Attributes:
        stability: Controls voice consistency (0.0-1.0). Lower = more expressive.
        similarity_boost: How closely to match original voice (0.0-1.0).
        style_exaggeration: Amplify style of original voice (0.0-1.0).
        use_speaker_boost: Enhance speaker clarity.
    """
    stability: float = 0.5
    similarity_boost: float = 0.75
    style_exaggeration: float = 0.0
    use_speaker_boost: bool = True


# =============================================================================
# Adapter Implementation
# =============================================================================

class ElevenLabsTTSAdapter(TTSPort):
    """
    ElevenLabs TTS adapter implementation.

    Uses AsyncElevenLabs client for native async support.
    Supports streaming, SSML, and ElevenLabs-specific audio tags.

    Example:
        async with ElevenLabsTTSAdapter() as tts:
            config = ElevenLabsVoiceConfig(
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                stability=0.5,
            )
            result = await tts.synthesize("Hello world", config)
    """

    # -------------------------------------------------------------------------
    # Format Mappings
    # -------------------------------------------------------------------------

    # (AudioFormat, AudioQuality) -> ElevenLabs format string
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

    # Format string -> audio metadata
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

    # Available models
    MODELS = {
        "eleven_multilingual_v2": "Latest multilingual model (recommended)",
        "eleven_turbo_v2_5": "Low latency model",
        "eleven_turbo_v2": "Legacy turbo model",
        "eleven_monolingual_v1": "English-only model",
    }

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs adapter.

        Args:
            api_key: ElevenLabs API key. If not provided, reads from
                     ELEVENLABS_API_KEY environment variable.

        Raises:
            TTSAuthenticationError: If no API key provided or found.
            ImportError: If elevenlabs package not installed.
        """
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key parameter or set "
                "ELEVENLABS_API_KEY environment variable."
            )

        # Lazy import for optional dependency
        try:
            from elevenlabs import AsyncElevenLabs
            self._client = AsyncElevenLabs(api_key=self._api_key)
        except ImportError:
            raise ImportError(
                "elevenlabs package required. Install with: "
                "pip install 'chatforge[tts-elevenlabs]'"
            )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

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
        return False  # Uses audio tags like [whispers] instead

    @property
    def max_text_length(self) -> int:
        return 5000

    # -------------------------------------------------------------------------
    # Core Methods
    # -------------------------------------------------------------------------

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
        Convert text to speech.

        Args:
            text: Text to synthesize. May include audio tags like [whispers].
            config: Voice configuration. Use ElevenLabsVoiceConfig for full control.
            output_format: Desired audio format.
            quality: Audio quality tier.
            model: ElevenLabs model ID. Defaults to eleven_multilingual_v2.

        Returns:
            AudioResult with synthesized audio and metadata.

        Raises:
            TTSInvalidInputError: If text is empty or exceeds limit.
            TTSInvalidVoiceError: If voice_id not found.
            TTSAuthenticationError: If API key invalid.
            TTSRateLimitError: If rate limited.
            TTSQuotaExceededError: If quota exhausted.
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format, quality)
        format_info = self._FORMAT_INFO.get(format_str, {})

        # Build voice settings from config
        voice_settings = self._build_voice_settings(config)

        try:
            # Async call to ElevenLabs API
            audio_bytes = await self._client.text_to_speech.convert(
                voice_id=config.voice_id,
                text=text,
                model_id=model or "eleven_multilingual_v2",
                output_format=format_str,
                voice_settings=voice_settings,
            )

            # Handle async generator response
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
            text: Text to synthesize.
            config: Voice configuration.
            output_format: Desired audio format.
            quality: Audio quality tier.
            model: ElevenLabs model ID.

        Yields:
            Audio chunks as bytes.
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format, quality)
        voice_settings = self._build_voice_settings(config)

        try:
            audio_stream = await self._client.text_to_speech.convert_as_stream(
                voice_id=config.voice_id,
                text=text,
                model_id=model or "eleven_multilingual_v2",
                output_format=format_str,
                voice_settings=voice_settings,
            )

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
            language_code: Optional filter by language (e.g., "en", "es").

        Returns:
            List of VoiceInfo for available voices.
        """
        try:
            response = await self._client.voices.get_all()
            voices = []

            for voice in response.voices:
                # Safely access labels
                labels = getattr(voice, 'labels', None) or {}
                voice_languages = labels.get('language', '')

                # Filter by language if specified
                if language_code:
                    if language_code.lower() not in voice_languages.lower():
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
                    is_custom=getattr(voice, 'category', '') == "cloned",
                    quality_tier=labels.get('use_case'),
                ))

            return voices

        except Exception as e:
            self._handle_api_error(e)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _build_voice_settings(self, config: VoiceConfig) -> Optional[dict]:
        """Build ElevenLabs voice_settings dict from config."""
        if isinstance(config, ElevenLabsVoiceConfig):
            return {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style_exaggeration,
                "use_speaker_boost": config.use_speaker_boost,
            }
        return None

    def _get_provider_format(self, format: AudioFormat, quality: AudioQuality) -> str:
        """Map abstract format+quality to ElevenLabs format string."""
        key = (format, quality)
        if key not in self._FORMAT_MAP:
            raise TTSInvalidInputError(
                f"ElevenLabs does not support {format.value} at {quality.value} quality. "
                f"Supported: MP3, PCM, OGG_OPUS"
            )
        return self._FORMAT_MAP[key]

    def _calculate_duration(
        self,
        audio_bytes: bytes,
        format: AudioFormat,
        format_info: dict,
    ) -> Optional[int]:
        """Calculate audio duration in milliseconds from raw bytes."""
        if format == AudioFormat.PCM:
            sample_rate = format_info.get("sample_rate", 44100)
            # 16-bit mono PCM = 2 bytes per sample
            num_samples = len(audio_bytes) // 2
            return int((num_samples / sample_rate) * 1000)
        # Can't easily calculate for compressed formats without decoding
        return None

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert ElevenLabs SDK errors to TTSPort exceptions.

        Uses SDK exception types for reliable error detection.
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
                    # Extract retry-after header if available
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
            raise TTSNetworkError(
                f"ElevenLabs network error: {error}"
            ) from error

        # Generic error
        raise TTSError(f"ElevenLabs error: {error}") from error

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Release resources."""
        # AsyncElevenLabs handles its own cleanup
        pass
```

---

## Audio Tags Support

ElevenLabs supports special audio tags in text:

| Tag | Effect |
|-----|--------|
| `[whispers]text[/whispers]` | Whispered speech |
| `[laughs]` | Laughter |
| `[sighs]` | Sigh |
| `[pause]` | Short pause |
| `[breath]` | Breathing sound |

Example:
```python
text = "[sighs] I can't believe it... [whispers]this is amazing[/whispers]"
result = await tts.synthesize(text, config)
```

---

## Model Selection Guide

| Model | Latency | Quality | Languages | Use Case |
|-------|---------|---------|-----------|----------|
| `eleven_multilingual_v2` | Medium | Best | 29 | General purpose (recommended) |
| `eleven_turbo_v2_5` | Low | Good | 32 | Real-time applications |
| `eleven_turbo_v2` | Low | Good | English | Legacy, fast English |
| `eleven_monolingual_v1` | Medium | Good | English | English-only projects |

---

## Usage Examples

### Basic Synthesis

```python
from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality

async with ElevenLabsTTSAdapter() as tts:
    config = ElevenLabsVoiceConfig(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George
        stability=0.5,
        similarity_boost=0.75,
    )

    result = await tts.synthesize(
        "Hello, world!",
        config,
        output_format=AudioFormat.MP3,
        quality=AudioQuality.HIGH,
    )

    with open("output.mp3", "wb") as f:
        f.write(result.audio_bytes)
```

### Streaming to File

```python
async with ElevenLabsTTSAdapter() as tts:
    config = ElevenLabsVoiceConfig(voice_id="JBFqnCBsd6RMkjVDRZzb")

    with open("stream_output.mp3", "wb") as f:
        async for chunk in tts.stream("Long text to synthesize...", config):
            f.write(chunk)
```

### With Audio Tags

```python
text = """
[sighs] Another day at the office.
[whispers]But I have a secret plan.[/whispers]
[laughs] Just kidding!
"""

result = await tts.synthesize(text, config)
```

### List and Select Voice

```python
async with ElevenLabsTTSAdapter() as tts:
    # Get English voices
    voices = await tts.list_voices(language_code="en")

    for v in voices:
        print(f"{v.voice_id}: {v.name} ({v.gender})")
        if v.is_custom:
            print("  [Cloned Voice]")

    # Use first voice
    if voices:
        config = ElevenLabsVoiceConfig(voice_id=voices[0].voice_id)
        result = await tts.synthesize("Hello!", config)
```

---

## Error Handling

```python
from chatforge.ports.tts import (
    TTSError,
    TTSAuthenticationError,
    TTSRateLimitError,
    TTSQuotaExceededError,
    TTSInvalidVoiceError,
)

async with ElevenLabsTTSAdapter() as tts:
    try:
        result = await tts.synthesize(text, config)

    except TTSRateLimitError as e:
        if e.retry_after_seconds:
            await asyncio.sleep(e.retry_after_seconds)
            # Retry...
        else:
            await asyncio.sleep(60)

    except TTSQuotaExceededError:
        # Switch to cheaper provider or notify user
        pass

    except TTSInvalidVoiceError:
        # Fall back to default voice
        config.voice_id = "default-voice-id"

    except TTSAuthenticationError:
        # Check API key configuration
        pass

    except TTSError as e:
        # Generic error handling
        logger.error(f"TTS failed: {e}")
```

---

## Testing

```python
import pytest
from unittest.mock import patch, AsyncMock

from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality, TTSAuthenticationError


class TestElevenLabsAdapter:
    """Unit tests for ElevenLabs adapter."""

    def test_requires_api_key(self):
        """Should raise error if no API key provided."""
        import os
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSAuthenticationError):
                ElevenLabsTTSAdapter()

    def test_accepts_explicit_api_key(self):
        """Should accept explicit API key."""
        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
            adapter = ElevenLabsTTSAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"

    def test_reads_env_var(self):
        """Should read API key from environment."""
        import os
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'env-key'}):
            with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
                adapter = ElevenLabsTTSAdapter()
                assert adapter._api_key == "env-key"

    def test_format_mapping(self):
        """Should map format+quality to provider format."""
        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs'):
            adapter = ElevenLabsTTSAdapter(api_key="test")
            assert adapter._get_provider_format(AudioFormat.MP3, AudioQuality.HIGH) == "mp3_44100_192"
            assert adapter._get_provider_format(AudioFormat.PCM, AudioQuality.LOW) == "pcm_16000"

    @pytest.mark.asyncio
    async def test_synthesize_calls_api(self):
        """Should call ElevenLabs API with correct parameters."""
        mock_client = AsyncMock()
        mock_client.text_to_speech.convert.return_value = b"audio data"

        with patch('chatforge.adapters.tts.elevenlabs.AsyncElevenLabs', return_value=mock_client):
            adapter = ElevenLabsTTSAdapter(api_key="test")
            config = ElevenLabsVoiceConfig(voice_id="test-voice")

            result = await adapter.synthesize("Hello", config)

            mock_client.text_to_speech.convert.assert_called_once()
            assert result.audio_bytes == b"audio data"
            assert result.format == AudioFormat.MP3
```
