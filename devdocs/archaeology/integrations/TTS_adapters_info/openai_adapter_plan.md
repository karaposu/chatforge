# OpenAI Adapter Implementation Plan

Detailed implementation guide for the OpenAI TTS adapter.

---

## Overview

| Aspect | Details |
|--------|---------|
| **File** | `chatforge/adapters/tts/openai.py` |
| **SDK** | `openai` (AsyncOpenAI) |
| **API Docs** | https://platform.openai.com/docs/guides/text-to-speech |
| **Features** | Streaming, style prompts (instructions), speed control |

---

## Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
tts-openai = ["openai>=1.0.0"]
```

---

## Complete Implementation

```python
"""
OpenAI TTS Adapter

Implements TTSPort for OpenAI text-to-speech API.
Uses AsyncOpenAI for native async support.
Supports style prompts via the instructions parameter.
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


# =============================================================================
# Provider-Specific Config
# =============================================================================

@dataclass
class OpenAIVoiceConfig(VoiceConfig):
    """
    OpenAI-specific voice configuration.

    Attributes:
        style_prompt: Natural language instructions for speech style.
                      Example: "Speak in a cheerful and positive tone"
    """
    style_prompt: Optional[str] = None


# =============================================================================
# Adapter Implementation
# =============================================================================

class OpenAITTSAdapter(TTSPort):
    """
    OpenAI TTS adapter implementation.

    Uses AsyncOpenAI client for native async support.
    Supports style control via natural language prompts.

    Example:
        async with OpenAITTSAdapter() as tts:
            config = OpenAIVoiceConfig(
                voice_id="coral",
                style_prompt="Speak warmly, like greeting an old friend",
            )
            result = await tts.synthesize("Hello!", config)
    """

    # -------------------------------------------------------------------------
    # Format Mappings
    # -------------------------------------------------------------------------

    # OpenAI format names (no quality control - uses model for that)
    _FORMAT_MAP = {
        AudioFormat.MP3: "mp3",
        AudioFormat.WAV: "wav",
        AudioFormat.FLAC: "flac",
        AudioFormat.AAC: "aac",
        AudioFormat.OGG_OPUS: "opus",
        AudioFormat.PCM: "pcm",
    }

    # Available voices with descriptions
    _VOICES = {
        "alloy": "Neutral, balanced",
        "ash": "Soft, gentle",
        "ballad": "Warm, storytelling",
        "coral": "Clear, friendly",
        "echo": "Soft, reflective",
        "fable": "Expressive, British",
        "nova": "Energetic, friendly",
        "onyx": "Deep, authoritative",
        "sage": "Calm, wise",
        "shimmer": "Bright, optimistic",
        "verse": "Versatile, natural",
    }

    # Models
    MODELS = {
        "tts-1": "Standard quality, lower latency",
        "tts-1-hd": "High definition, best quality",
    }

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key. If not provided, reads from
                     OPENAI_API_KEY environment variable.

        Raises:
            TTSAuthenticationError: If no API key provided or found.
            ImportError: If openai package not installed.
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key parameter or set "
                "OPENAI_API_KEY environment variable."
            )

        # Lazy import for optional dependency
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        except ImportError:
            raise ImportError(
                "openai package required. Install with: "
                "pip install 'chatforge[tts-openai]'"
            )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_ssml(self) -> bool:
        return False  # OpenAI doesn't support SSML

    @property
    def supports_style_prompt(self) -> bool:
        return True  # Via instructions parameter

    @property
    def max_text_length(self) -> int:
        return 4096

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
            text: Text to synthesize.
            config: Voice configuration. Use OpenAIVoiceConfig for style prompts.
            output_format: Desired audio format.
            quality: Audio quality tier. HIGH uses tts-1-hd model.
            model: OpenAI model ID. Overrides quality-based selection.

        Returns:
            AudioResult with synthesized audio and metadata.

        Raises:
            TTSInvalidInputError: If text is empty or exceeds limit.
            TTSInvalidVoiceError: If voice_id not valid.
            TTSAuthenticationError: If API key invalid.
            TTSRateLimitError: If rate limited.
            TTSQuotaExceededError: If quota exhausted.
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format)
        selected_model = self._get_model(model, quality)

        # Build request kwargs
        kwargs = {
            "model": selected_model,
            "voice": config.voice_id,
            "input": text,
            "response_format": format_str,
            "speed": config.speed,  # 0.25 - 4.0
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
                sample_rate=24000,  # OpenAI outputs 24kHz
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
            text: Text to synthesize.
            config: Voice configuration.
            output_format: Desired audio format.
            quality: Audio quality tier.
            model: OpenAI model ID.

        Yields:
            Audio chunks as bytes.
        """
        self._validate_input(text, config)
        text = self._preprocess_text(text, config)

        format_str = self._get_provider_format(output_format)
        selected_model = self._get_model(model, quality)

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

        Note: OpenAI has a fixed set of voices, no API to list them.
        All voices support all languages (optimized for English).

        Args:
            language_code: Ignored - all voices support all languages.

        Returns:
            List of VoiceInfo for available voices.
        """
        return [
            VoiceInfo(
                voice_id=voice_id,
                name=voice_id.title(),
                provider="openai",
                language_codes=["en-US"],  # Optimized for English
                description=description,
                supports_ssml=False,
                supports_streaming=True,
            )
            for voice_id, description in self._VOICES.items()
        ]

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """
        Strip ElevenLabs audio tags that OpenAI doesn't support.

        OpenAI will read these literally, so we remove them for compatibility
        when switching from ElevenLabs.
        """
        # Remove audio tags like [whispers], [laughs], etc.
        return re.sub(r'\[(whispers|laughs|pause|sighs|breath)\]', '', text)

    def _get_provider_format(self, format: AudioFormat) -> str:
        """Map AudioFormat to OpenAI format string."""
        if format not in self._FORMAT_MAP:
            raise TTSInvalidInputError(
                f"OpenAI does not support {format.value}. "
                f"Supported: mp3, wav, flac, aac, opus, pcm"
            )
        return self._FORMAT_MAP[format]

    def _get_model(self, model: Optional[str], quality: AudioQuality) -> str:
        """
        Select model based on explicit choice or quality tier.

        Args:
            model: Explicit model ID (overrides quality).
            quality: Quality tier for automatic selection.

        Returns:
            Model ID string.
        """
        if model is not None:
            return model
        # HIGH quality uses HD model
        return "tts-1-hd" if quality == AudioQuality.HIGH else "tts-1"

    def _handle_api_error(self, error: Exception) -> NoReturn:
        """
        Convert OpenAI SDK errors to TTSPort exceptions.

        Uses SDK exception types for reliable error detection.
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
                # Extract retry-after if available
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
                # Check for quota errors
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

        if "invalid" in error_str and "voice" in error_str:
            raise TTSInvalidVoiceError(
                f"OpenAI voice not found: {error}"
            ) from error

        if "connection" in error_str or "timeout" in error_str:
            raise TTSNetworkError(
                f"OpenAI network error: {error}"
            ) from error

        # Generic error
        raise TTSError(f"OpenAI error: {error}") from error

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Release resources."""
        # AsyncOpenAI handles its own cleanup
        pass
```

---

## Voice Guide

| Voice | Style | Best For |
|-------|-------|----------|
| `alloy` | Neutral, balanced | General purpose |
| `ash` | Soft, gentle | Meditation, calm content |
| `ballad` | Warm, storytelling | Audiobooks, narratives |
| `coral` | Clear, friendly | Customer service, tutorials |
| `echo` | Soft, reflective | Poetry, introspective content |
| `fable` | Expressive, British | Character voices, drama |
| `nova` | Energetic, friendly | Marketing, upbeat content |
| `onyx` | Deep, authoritative | Announcements, serious content |
| `sage` | Calm, wise | Educational, advisory |
| `shimmer` | Bright, optimistic | Children's content, cheerful |
| `verse` | Versatile, natural | General purpose |

---

## Model Selection

| Model | Quality | Latency | Cost | Use Case |
|-------|---------|---------|------|----------|
| `tts-1` | Good | Low | Lower | Real-time, interactive |
| `tts-1-hd` | Best | Higher | Higher | Pre-recorded, quality-critical |

The adapter automatically selects:
- `AudioQuality.HIGH` → `tts-1-hd`
- `AudioQuality.STANDARD` or `LOW` → `tts-1`

---

## Style Prompts (Instructions)

OpenAI supports natural language style control via the `instructions` parameter:

```python
config = OpenAIVoiceConfig(
    voice_id="coral",
    style_prompt="Speak in a warm, friendly tone as if greeting an old friend. "
                 "Be enthusiastic but not over the top."
)
```

### Effective Style Prompts

| Goal | Example Prompt |
|------|----------------|
| Excited | "Speak with enthusiasm and energy, like announcing exciting news" |
| Calm | "Speak slowly and calmly, like a meditation guide" |
| Professional | "Speak in a professional, business-like manner" |
| Storytelling | "Speak like narrating a bedtime story, warm and engaging" |
| News anchor | "Speak clearly and authoritatively, like a news broadcaster" |

---

## Usage Examples

### Basic Synthesis

```python
from chatforge.adapters.tts.openai import OpenAITTSAdapter, OpenAIVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality

async with OpenAITTSAdapter() as tts:
    config = OpenAIVoiceConfig(voice_id="coral")

    result = await tts.synthesize(
        "Hello, world!",
        config,
        output_format=AudioFormat.MP3,
        quality=AudioQuality.HIGH,  # Uses tts-1-hd
    )

    with open("output.mp3", "wb") as f:
        f.write(result.audio_bytes)
```

### With Style Prompt

```python
async with OpenAITTSAdapter() as tts:
    config = OpenAIVoiceConfig(
        voice_id="nova",
        style_prompt="Speak with excitement and energy, like announcing a prize winner!",
        speed=1.1,  # Slightly faster
    )

    result = await tts.synthesize(
        "Congratulations! You've won the grand prize!",
        config,
    )
```

### Streaming

```python
async with OpenAITTSAdapter() as tts:
    config = OpenAIVoiceConfig(voice_id="onyx")

    with open("stream_output.mp3", "wb") as f:
        async for chunk in tts.stream("Long text to synthesize...", config):
            f.write(chunk)
```

### Speed Control

```python
# Slow speech (0.25 - 4.0)
config = OpenAIVoiceConfig(voice_id="sage", speed=0.8)

# Fast speech
config = OpenAIVoiceConfig(voice_id="nova", speed=1.5)
```

### Cost-Effective Usage

```python
# Use tts-1 for drafts/testing (faster, cheaper)
result = await tts.synthesize(text, config, quality=AudioQuality.STANDARD)

# Use tts-1-hd for final output (better quality)
result = await tts.synthesize(text, config, quality=AudioQuality.HIGH)
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

async with OpenAITTSAdapter() as tts:
    try:
        result = await tts.synthesize(text, config)

    except TTSRateLimitError as e:
        if e.retry_after_seconds:
            await asyncio.sleep(e.retry_after_seconds)
        else:
            await asyncio.sleep(60)
        # Retry...

    except TTSQuotaExceededError:
        # Check billing, add credits
        pass

    except TTSInvalidVoiceError:
        # Use valid voice from list
        config.voice_id = "alloy"

    except TTSAuthenticationError:
        # Check API key
        pass

    except TTSError as e:
        logger.error(f"TTS failed: {e}")
```

---

## Comparison with ElevenLabs

| Feature | OpenAI | ElevenLabs |
|---------|--------|------------|
| **Cost** | ~$0.015/1K chars | ~$0.30/1K chars |
| **Quality** | Good (HD: Excellent) | Excellent |
| **Voices** | 11 built-in | 100s + cloning |
| **Style Control** | Natural language prompts | Audio tags + settings |
| **SSML** | No | Yes |
| **Streaming** | Yes | Yes |
| **Voice Cloning** | No | Yes |
| **Latency** | Low (tts-1) | Medium |

**When to use OpenAI:**
- Cost-sensitive applications (20x cheaper)
- Simple style requirements
- Real-time/interactive (tts-1 model)

**When to use ElevenLabs:**
- Maximum voice quality needed
- Voice cloning required
- Complex audio effects (whispers, laughs)
- SSML control needed

---

## Testing

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from chatforge.adapters.tts.openai import OpenAITTSAdapter, OpenAIVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality, TTSAuthenticationError


class TestOpenAIAdapter:
    """Unit tests for OpenAI adapter."""

    def test_requires_api_key(self):
        """Should raise error if no API key provided."""
        import os
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSAuthenticationError):
                OpenAITTSAdapter()

    def test_accepts_explicit_api_key(self):
        """Should accept explicit API key."""
        with patch('chatforge.adapters.tts.openai.AsyncOpenAI'):
            adapter = OpenAITTSAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"

    def test_model_selection_by_quality(self):
        """Should select model based on quality tier."""
        with patch('chatforge.adapters.tts.openai.AsyncOpenAI'):
            adapter = OpenAITTSAdapter(api_key="test")
            assert adapter._get_model(None, AudioQuality.HIGH) == "tts-1-hd"
            assert adapter._get_model(None, AudioQuality.STANDARD) == "tts-1"
            assert adapter._get_model(None, AudioQuality.LOW) == "tts-1"

    def test_explicit_model_overrides_quality(self):
        """Explicit model should override quality-based selection."""
        with patch('chatforge.adapters.tts.openai.AsyncOpenAI'):
            adapter = OpenAITTSAdapter(api_key="test")
            assert adapter._get_model("tts-1", AudioQuality.HIGH) == "tts-1"

    def test_preprocess_strips_audio_tags(self):
        """Should strip ElevenLabs audio tags."""
        with patch('chatforge.adapters.tts.openai.AsyncOpenAI'):
            adapter = OpenAITTSAdapter(api_key="test")
            config = OpenAIVoiceConfig(voice_id="test")

            result = adapter._preprocess_text(
                "[whispers]Hello[/whispers] [laughs] world",
                config
            )
            assert "[whispers]" not in result
            assert "[laughs]" not in result

    @pytest.mark.asyncio
    async def test_synthesize_includes_style_prompt(self):
        """Should include instructions when style_prompt is set."""
        mock_response = MagicMock()
        mock_response.content = b"audio data"

        mock_client = AsyncMock()
        mock_client.audio.speech.create.return_value = mock_response

        with patch('chatforge.adapters.tts.openai.AsyncOpenAI', return_value=mock_client):
            adapter = OpenAITTSAdapter(api_key="test")
            config = OpenAIVoiceConfig(
                voice_id="coral",
                style_prompt="Speak cheerfully",
            )

            await adapter.synthesize("Hello", config)

            call_kwargs = mock_client.audio.speech.create.call_args[1]
            assert call_kwargs["instructions"] == "Speak cheerfully"

    @pytest.mark.asyncio
    async def test_list_voices_returns_all(self):
        """Should return all available voices."""
        with patch('chatforge.adapters.tts.openai.AsyncOpenAI'):
            adapter = OpenAITTSAdapter(api_key="test")
            voices = await adapter.list_voices()

            assert len(voices) == 11
            voice_ids = [v.voice_id for v in voices]
            assert "alloy" in voice_ids
            assert "coral" in voice_ids
            assert "nova" in voice_ids
```
