# TTSPort Design Specification

Based on analysis of ElevenLabs, OpenAI, Azure, and Google Cloud TTS capabilities.

---

## TTS Provider Capability Comparison

| Feature | ElevenLabs | OpenAI | Azure | Google |
|---------|------------|--------|-------|--------|
| **Basic TTS** | ✅ | ✅ | ✅ | ✅ |
| **HTTP Streaming** | ✅ | ✅ | ✅ (SDK) | ✅ (gRPC) |
| **WebSocket** | ✅ | ❌ | ❌ | ❌ |
| **SSML** | ✅ (optional) | ❌ | ✅ (primary) | ✅ |
| **Style Prompt** | ❌ (tags only) | ✅ `instructions` | ❌ | ✅ `prompt` |
| **Audio Tags** | ✅ `[whispers]` | ❌ | ❌ | ❌ |
| **Voice Settings** | stability, similarity, style, speed | ❌ | via SSML | pitch, rate, volume |
| **Multi-Speaker** | ❌ | ❌ | ❌ | ✅ Gemini |
| **Word Timestamps** | ✅ | ❌ | ✅ (visemes) | ❌ |
| **Custom Voice** | ✅ (clone) | ❌ | ✅ (approval) | ❌ |
| **Languages** | 70+ | ~50 | 100+ | 75+ |
| **Voices** | Many + cloning | 13 built-in | 400+ | 380+ |
| **Max Text Length** | ~5,000 chars | 4,096 chars | ~10 min audio | 5,000 bytes |

---

## TTSPort Interface

```python
# chatforge/ports/tts.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional
from enum import Enum

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
# Enums and Data Classes
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

@dataclass
class VoiceConfig:
    """
    Base voice configuration - provider-agnostic.

    For provider-specific settings, use the provider's config subclass:
    - ElevenLabsVoiceConfig
    - OpenAIVoiceConfig
    - AzureVoiceConfig
    - GoogleVoiceConfig
    """
    voice_id: str
    language_code: str = "en-US"

    # Universal voice tuning
    speed: float = 1.0  # 0.25 - 4.0

@dataclass
class ElevenLabsVoiceConfig(VoiceConfig):
    """ElevenLabs-specific voice configuration."""
    stability: float = 0.5              # 0.0 - 1.0
    similarity_boost: float = 0.75      # 0.0 - 1.0
    style_exaggeration: float = 0.0     # 0.0 - 1.0
    use_speaker_boost: bool = True

@dataclass
class OpenAIVoiceConfig(VoiceConfig):
    """OpenAI-specific voice configuration."""
    style_prompt: Optional[str] = None  # Natural language instructions

@dataclass
class AzureVoiceConfig(VoiceConfig):
    """Azure-specific voice configuration."""
    ssml: Optional[str] = None          # Full SSML document
    pitch: float = 0.0                  # -50% to +50%
    volume: float = 0.0                 # -100% to +100%

@dataclass
class GoogleVoiceConfig(VoiceConfig):
    """Google Cloud TTS-specific voice configuration."""
    style_prompt: Optional[str] = None  # Gemini prompt
    ssml: Optional[str] = None
    pitch: float = 0.0                  # -20 to +20 semitones
    volume_gain_db: float = 0.0         # -96 to +16

@dataclass
class AudioResult:
    """Result from TTS synthesis."""
    audio_bytes: bytes
    format: AudioFormat
    sample_rate: int = 44100
    bitrate_kbps: Optional[int] = None       # Actual bitrate used (for lossy formats)
    channels: int = 1                         # 1 = mono, 2 = stereo
    duration_ms: Optional[int] = None
    input_characters: int = 0
    billed_characters: Optional[int] = None  # Provider-reported if different

    # Optional metadata
    word_timestamps: Optional[list] = None  # ElevenLabs/Azure alignment
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
    is_custom: bool = False             # Cloned/custom voice
    quality_tier: Optional[str] = None  # "standard", "hd"

# =============================================================================
# TTSPort Interface (Async Primary)
# =============================================================================

class TTSPort(ABC):
    """
    Port interface for Text-to-Speech providers.

    All methods are async-first. Adapters must implement the abstract methods.

    Implementations:
    - ElevenLabsTTSAdapter
    - OpenAITTSAdapter
    - AzureTTSAdapter
    - GoogleTTSAdapter

    Raises:
        TTSError: Base class for all TTS errors
        TTSNetworkError: Network/connectivity issues
        TTSAuthenticationError: Invalid API key
        TTSQuotaExceededError: Quota/credits exhausted
        TTSRateLimitError: Rate limited (check retry_after_seconds)
        TTSInvalidVoiceError: Voice not found
        TTSInvalidInputError: Invalid text input
        TTSStreamingNotSupportedError: Streaming not available
    """

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
    # Core Methods (Async)
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
            text: Text to synthesize (may include audio tags for ElevenLabs)
            config: Voice configuration (use provider-specific subclass for full control)
            output_format: Desired audio format
            quality: Audio quality tier (adapters map to provider-specific formats)
            model: Provider-specific model ID

        Returns:
            AudioResult with audio bytes and metadata (includes actual sample_rate, bitrate)

        Raises:
            TTSInvalidInputError: If text exceeds max_text_length or is invalid
            TTSInvalidVoiceError: If voice_id is not found
            TTSNetworkError: On network failures
            TTSAuthenticationError: If API key is invalid
            TTSQuotaExceededError: If quota is exhausted
            TTSRateLimitError: If rate limited
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

        This method is abstract - providers that don't support streaming
        must raise TTSStreamingNotSupportedError.

        Args:
            text: Text to synthesize
            config: Voice configuration
            output_format: Desired audio format
            quality: Audio quality tier (adapters map to provider-specific formats)
            model: Provider-specific model ID

        Yields:
            Audio chunks as bytes

        Raises:
            TTSStreamingNotSupportedError: If provider doesn't support streaming
            TTSInvalidInputError: If text exceeds max_text_length
            TTSInvalidVoiceError: If voice_id is not found
            TTSNetworkError: On network failures
        """
        pass

    @abstractmethod
    async def list_voices(
        self,
        language_code: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """List available voices, optionally filtered by language."""
        pass

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def get_voice(self, voice_id: str) -> Optional[VoiceInfo]:
        """Get info for a specific voice."""
        voices = await self.list_voices()
        return next((v for v in voices if v.voice_id == voice_id), None)

    def _validate_input(self, text: str, config: VoiceConfig) -> None:
        """
        Validate input before synthesis.

        Called internally by synthesize() and stream().
        Override in adapters to add provider-specific validations.
        Raises TTSInvalidInputError on validation failure.
        """
        # Common validations
        if not text or not text.strip():
            raise TTSInvalidInputError("Text cannot be empty")

        self._validate_text_length(text)

    def _validate_text_length(self, text: str) -> None:
        """Validate text length. Called by _validate_input()."""
        if len(text) > self.max_text_length:
            raise TTSInvalidInputError(
                f"Text length {len(text)} exceeds {self.provider_name} "
                f"limit of {self.max_text_length} characters. "
                f"Split text into smaller chunks before calling synthesize()."
            )

    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        """
        Internal hook for text preprocessing before synthesis.

        Override in adapters to:
        - Strip unsupported tags for this provider
        - Convert style_prompt to provider-specific format
        - Apply SSML wrapping if needed
        """
        return text

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Release resources. Override if adapter holds connections."""
        pass

    async def __aenter__(self) -> "TTSPort":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
```

---

## Key Design Decisions

### 1. Async-First Interface

All core methods are async to support modern Python applications (FastAPI, aiohttp, etc.). TTS is inherently I/O-bound, making async the natural choice.

```python
# Async usage
async def speak(text: str):
    async with ElevenLabsTTSAdapter(api_key="...") as tts:
        result = await tts.synthesize(text, config)
        return result.audio_bytes
```

### 2. Explicit Exception Hierarchy

Clear exceptions for different failure modes:

```python
try:
    result = await tts.synthesize(text, config)
except TTSRateLimitError as e:
    await asyncio.sleep(e.retry_after_seconds or 60)
    # Retry...
except TTSQuotaExceededError:
    # Switch to cheaper provider
    tts = OpenAITTSAdapter(api_key="...")
except TTSInvalidVoiceError:
    # Fall back to default voice
    config.voice_id = "default"
```

### 3. Provider-Specific Config Subclasses

Base `VoiceConfig` for universal settings, provider subclasses for specific features:

```python
# Universal - works with any provider
config = VoiceConfig(voice_id="alloy", speed=1.2)

# ElevenLabs-specific
config = ElevenLabsVoiceConfig(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    stability=0.5,
    similarity_boost=0.75,
)

# OpenAI-specific
config = OpenAIVoiceConfig(
    voice_id="coral",
    style_prompt="Speak in a cheerful and positive tone",
)
```

### 4. Streaming is Abstract

No default implementation that silently buffers. Providers must either:
- Implement true streaming
- Raise `TTSStreamingNotSupportedError`

```python
class OpenAITTSAdapter(TTSPort):
    @property
    def supports_streaming(self) -> bool:
        return True  # OpenAI supports HTTP chunked streaming

    async def stream(self, text, config, **opts) -> AsyncIterator[bytes]:
        async with self.client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=config.voice_id,
            input=text,
        ) as response:
            async for chunk in response.iter_bytes():
                yield chunk

class SomeBasicAdapter(TTSPort):
    @property
    def supports_streaming(self) -> bool:
        return False

    async def stream(self, text, config, **opts) -> AsyncIterator[bytes]:
        raise TTSStreamingNotSupportedError(
            f"{self.provider_name} does not support streaming. Use synthesize() instead."
        )
```

### 5. All Capability Properties are Abstract

All capability discovery properties are abstract - adapters MUST implement all of them:

```python
class TTSPort(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_ssml(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_style_prompt(self) -> bool:
        pass

    @property
    @abstractmethod
    def max_text_length(self) -> int:
        pass
```

**Why all abstract?** No silent defaults. If an adapter forgets to implement one, Python raises an error immediately rather than returning a wrong default value.

```python
class OpenAITTSAdapter(TTSPort):
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
        return True  # OpenAI supports style via instructions

    @property
    def max_text_length(self) -> int:
        return 4096
```

### 6. Input Validation

The base `TTSPort` provides `_validate_input()` with common checks. Adapters override to add provider-specific validations:

```python
# Base TTSPort - common validations
def _validate_input(self, text: str, config: VoiceConfig) -> None:
    if not text or not text.strip():
        raise TTSInvalidInputError("Text cannot be empty")
    self._validate_text_length(text)
```

Adapters extend with provider-specific checks:

```python
# Azure - validate SSML format
class AzureTTSAdapter(TTSPort):
    def _validate_input(self, text: str, config: VoiceConfig) -> None:
        super()._validate_input(text, config)  # Common checks first

        if isinstance(config, AzureVoiceConfig) and config.ssml:
            if not config.ssml.strip().startswith("<speak"):
                raise TTSInvalidInputError("SSML must start with <speak> tag")


# Google - check conflicting options
class GoogleTTSAdapter(TTSPort):
    def _validate_input(self, text: str, config: VoiceConfig) -> None:
        super()._validate_input(text, config)  # Common checks first

        if isinstance(config, GoogleVoiceConfig):
            if config.ssml and config.style_prompt:
                raise TTSInvalidInputError(
                    "Cannot use both SSML and style_prompt together"
                )
```

Adapters call it at the start of `synthesize()`:

```python
async def synthesize(self, text: str, config: VoiceConfig, ...) -> AudioResult:
    self._validate_input(text, config)  # Validate first
    text = self._preprocess_text(text, config)
    # ... call provider API
```

### 7. Text Length Validation

The base `TTSPort` provides `_validate_text_length()` (called by `_validate_input()`):

```python
# In TTSPort base class (already provided)
def _validate_text_length(self, text: str) -> None:
    """Raises TTSInvalidInputError if text exceeds max_text_length."""
    if len(text) > self.max_text_length:
        raise TTSInvalidInputError(
            f"Text length {len(text)} exceeds {self.provider_name} "
            f"limit of {self.max_text_length} characters."
        )
```

Each adapter defines its limit and calls the validation:

```python
class ElevenLabsTTSAdapter(TTSPort):
    @property
    def max_text_length(self) -> int:
        return 5000  # ElevenLabs limit

    async def synthesize(self, text: str, config: VoiceConfig, ...) -> AudioResult:
        self._validate_text_length(text)  # Raises if too long
        text = self._preprocess_text(text, config)
        # ... actual synthesis
```

User gets a clear error if text is too long:

```python
try:
    result = await tts.synthesize(very_long_text, config)
except TTSInvalidInputError as e:
    print(e)  # "Text length 10000 exceeds elevenlabs limit of 5000 characters."
```

For long content, the **application** handles chunking:

```python
# Application-level (not in Chatforge)
if len(text) > tts.max_text_length:
    chunks = my_chunk_function(text, tts.max_text_length)
    for chunk in chunks:
        result = await tts.synthesize(chunk, config)
        yield result.audio_bytes
```

### 8. Text Preprocessing Hook

The base class provides `_preprocess_text()` - adapters override with provider-specific logic:

```python
# Base TTSPort - does nothing (default)
def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
    return text
```

Each adapter overrides as needed:

```python
# ElevenLabs - supports audio tags, keep them
class ElevenLabsTTSAdapter(TTSPort):
    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        # [whispers], [laughs], etc. are supported - keep as-is
        return text


# OpenAI - strip unsupported tags
class OpenAITTSAdapter(TTSPort):
    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        import re
        # Strip ElevenLabs audio tags that OpenAI doesn't understand
        return re.sub(r'\[(whispers|laughs|pause)\]', '', text)


# Azure - wrap in SSML if needed
class AzureTTSAdapter(TTSPort):
    def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
        if isinstance(config, AzureVoiceConfig) and config.ssml:
            return config.ssml  # Use provided SSML document
        # Wrap plain text in basic SSML
        return f"<speak>{text}</speak>"
```

Adapters call it internally in `synthesize()`:

```python
async def synthesize(self, text: str, config: VoiceConfig, ...) -> AudioResult:
    self._validate_text_length(text)
    text = self._preprocess_text(text, config)  # Transform text
    # ... call provider API
```

User doesn't need to worry about provider differences:

```python
text = "[whispers] Hello there"

# ElevenLabs - keeps the tag, whispers the audio
await elevenlabs_tts.synthesize(text, config)

# OpenAI - strips the tag automatically, normal speech
await openai_tts.synthesize(text, config)
```

### 9. Audio Format + Quality Mapping

Each adapter maintains an internal mapping table that converts `(AudioFormat, AudioQuality)` to provider-specific format strings:

```python
# chatforge/adapters/tts/azure.py
class AzureTTSAdapter(TTSPort):

    # Internal mapping table
    _FORMAT_MAP = {
        # (AudioFormat, AudioQuality) -> Azure SDK enum
        (AudioFormat.MP3, AudioQuality.LOW):
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
        (AudioFormat.MP3, AudioQuality.STANDARD):
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,
        (AudioFormat.MP3, AudioQuality.HIGH):
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateStereoMp3,

        (AudioFormat.WAV, AudioQuality.LOW):
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
        (AudioFormat.WAV, AudioQuality.STANDARD):
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
        (AudioFormat.WAV, AudioQuality.HIGH):
            speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
    }

    def _get_provider_format(
        self,
        format: AudioFormat,
        quality: AudioQuality
    ) -> speechsdk.SpeechSynthesisOutputFormat:
        """Map abstract format+quality to Azure-specific format."""
        key = (format, quality)
        if key not in self._FORMAT_MAP:
            raise TTSInvalidInputError(
                f"Azure does not support {format.value} at {quality.value} quality"
            )
        return self._FORMAT_MAP[key]
```

```python
# chatforge/adapters/tts/elevenlabs.py
class ElevenLabsTTSAdapter(TTSPort):

    _FORMAT_MAP = {
        (AudioFormat.MP3, AudioQuality.LOW): "mp3_22050_32",
        (AudioFormat.MP3, AudioQuality.STANDARD): "mp3_44100_128",
        (AudioFormat.MP3, AudioQuality.HIGH): "mp3_44100_192",
        (AudioFormat.PCM, AudioQuality.LOW): "pcm_16000",
        (AudioFormat.PCM, AudioQuality.STANDARD): "pcm_22050",
        (AudioFormat.PCM, AudioQuality.HIGH): "pcm_44100",
    }
```

```python
# chatforge/adapters/tts/openai.py
class OpenAITTSAdapter(TTSPort):

    # OpenAI doesn't support quality control - just format
    _FORMAT_MAP = {
        AudioFormat.MP3: "mp3",
        AudioFormat.WAV: "wav",
        AudioFormat.FLAC: "flac",
        AudioFormat.AAC: "aac",
        AudioFormat.OGG_OPUS: "opus",
        AudioFormat.PCM: "pcm",
    }

    def _get_provider_format(self, format: AudioFormat, quality: AudioQuality) -> str:
        # Quality is ignored for OpenAI
        if format not in self._FORMAT_MAP:
            raise TTSInvalidInputError(f"OpenAI does not support {format.value}")
        return self._FORMAT_MAP[format]
```

### 10. Adapter Responsibilities for AudioResult

Adapters MUST return a fully-populated `AudioResult`. If the API doesn't provide a value, adapters should calculate it when possible:

```python
@dataclass
class AudioResult:
    audio_bytes: bytes                       # Required
    format: AudioFormat                      # Required
    sample_rate: int = 44100                 # Required - from API or known default
    bitrate_kbps: Optional[int] = None       # From API or format mapping
    channels: int = 1                        # From API or known default
    duration_ms: Optional[int] = None        # From API or CALCULATED
    input_characters: int = 0                # Adapter knows this
    billed_characters: Optional[int] = None  # From API if available
```

**Example: Calculating duration when API doesn't provide it:**

```python
class ElevenLabsTTSAdapter(TTSPort):
    async def synthesize(self, text: str, config: VoiceConfig, ...) -> AudioResult:
        response = await self._call_api(text, config)

        # Try API value first, then calculate
        duration_ms = response.get("duration_ms")
        if duration_ms is None:
            duration_ms = self._calculate_duration(
                response["audio"], output_format, sample_rate
            )

        return AudioResult(
            audio_bytes=response["audio"],
            format=output_format,
            sample_rate=sample_rate,
            bitrate_kbps=self._get_bitrate(output_format, quality),
            duration_ms=duration_ms,  # Calculated if not from API
            input_characters=len(text),
        )

    def _calculate_duration(
        self,
        audio_bytes: bytes,
        format: AudioFormat,
        sample_rate: int
    ) -> Optional[int]:
        """Calculate duration from audio bytes."""
        if format == AudioFormat.PCM:
            # PCM 16-bit mono: 2 bytes per sample
            num_samples = len(audio_bytes) // 2
            return int((num_samples / sample_rate) * 1000)

        if format == AudioFormat.WAV:
            # Parse WAV header for duration
            return self._parse_wav_duration(audio_bytes)

        # MP3/OGG - can't easily calculate without decoder
        return None
```

**The contract:**
- Return API-provided values when available
- Calculate values when possible (PCM/WAV duration is straightforward)
- Return `None` only when truly unknown

The `AudioResult` reports what was actually used:

```python
result = await tts.synthesize(text, config, quality=AudioQuality.HIGH)
print(f"Sample rate: {result.sample_rate}")    # 48000
print(f"Bitrate: {result.bitrate_kbps} kbps")  # 192
print(f"Channels: {result.channels}")          # 2 (stereo)
```

### 11. API Key Handling

Adapters accept explicit `api_key` parameter OR fallback to environment variable:

```python
import os

class ElevenLabsTTSAdapter(TTSPort):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key or set ELEVENLABS_API_KEY env var."
            )

class OpenAITTSAdapter(TTSPort):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise TTSAuthenticationError(
                "API key required. Pass api_key or set OPENAI_API_KEY env var."
            )
```

**Standard environment variable names:**

| Provider | Environment Variable |
|----------|---------------------|
| ElevenLabs | `ELEVENLABS_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Azure | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` |
| Google | `GOOGLE_APPLICATION_CREDENTIALS` (file path) |

**Usage:**

```python
# Option 1: Explicit api_key (testing, multiple accounts)
tts = ElevenLabsTTSAdapter(api_key="sk-xxx")

# Option 2: From environment / .env file (recommended for production)
# .env:
#   ELEVENLABS_API_KEY=sk-xxx
#   OPENAI_API_KEY=sk-yyy

tts = ElevenLabsTTSAdapter()  # Auto-reads from env
tts = OpenAITTSAdapter()      # Auto-reads from env
```

---

## Chatforge Package Structure

```
chatforge/
├── ports/
│   └── tts.py              # TTSPort interface, exceptions, VoiceConfig, AudioResult
├── adapters/
│   └── tts/
│       ├── __init__.py
│       ├── elevenlabs.py   # ElevenLabsTTSAdapter
│       └── openai.py       # OpenAITTSAdapter
```

---

## Usage Examples

### Basic Usage - ElevenLabs

```python
from chatforge.ports.tts import AudioFormat, AudioQuality, TTSError
from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

async def main():
    # Uses ELEVENLABS_API_KEY from environment
    async with ElevenLabsTTSAdapter() as tts:
        config = ElevenLabsVoiceConfig(
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            stability=0.5,
            similarity_boost=0.75,
        )

        try:
            result = await tts.synthesize(
                "Hello world",
                config,
                output_format=AudioFormat.MP3,
                quality=AudioQuality.HIGH,  # Will use "mp3_44100_192"
            )
            print(f"Audio: {result.sample_rate}Hz, {result.bitrate_kbps}kbps")
            with open("output.mp3", "wb") as f:
                f.write(result.audio_bytes)
        except TTSError as e:
            print(f"TTS failed: {e}")
```

### Basic Usage - OpenAI

```python
from chatforge.adapters.tts.openai import OpenAITTSAdapter, OpenAIVoiceConfig

async def main():
    # Uses OPENAI_API_KEY from environment
    async with OpenAITTSAdapter() as tts:
        config = OpenAIVoiceConfig(
            voice_id="coral",
            style_prompt="Speak in a cheerful and positive tone",
        )
        result = await tts.synthesize("Welcome to our store!", config)
```

### Streaming

```python
from chatforge.ports.tts import TTSStreamingNotSupportedError
from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

async def stream_audio():
    async with ElevenLabsTTSAdapter(api_key="...") as tts:
        config = ElevenLabsVoiceConfig(voice_id="JBFqnCBsd6RMkjVDRZzb")

        if not tts.supports_streaming:
            raise TTSStreamingNotSupportedError("Use synthesize() instead")

        async for chunk in tts.stream("Long text to synthesize...", config):
            yield chunk  # Send to client, play, etc.
```

### Error Handling

```python
from chatforge.ports.tts import (
    TTSError,
    TTSRateLimitError,
    TTSQuotaExceededError,
    TTSInvalidVoiceError,
)

async def synthesize_with_retry(tts, text, config, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await tts.synthesize(text, config)
        except TTSRateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after_seconds or (2 ** attempt)
                await asyncio.sleep(wait_time)
            else:
                raise
        except TTSQuotaExceededError:
            raise  # Can't retry, need to add credits
        except TTSInvalidVoiceError:
            config.voice_id = "default-fallback-voice"
            # Retry with fallback
```

### List Voices

```python
async def find_voices():
    async with ElevenLabsTTSAdapter(api_key="...") as tts:
        voices = await tts.list_voices(language_code="en-US")
        for v in voices:
            print(f"{v.voice_id}: {v.name} ({v.gender})")
            if v.is_custom:
                print("  [Custom/Cloned Voice]")
```

### Application Factory Pattern (Optional)

If your application wants a factory, you create it:

```python
# myapp/tts_factory.py
from chatforge.ports.tts import TTSPort
from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter
from chatforge.adapters.tts.openai import OpenAITTSAdapter
import os

def get_tts(provider: str = None) -> TTSPort:
    """Application-level factory - you control this."""
    provider = provider or os.getenv("TTS_PROVIDER", "elevenlabs")

    if provider == "elevenlabs":
        return ElevenLabsTTSAdapter(api_key=os.getenv("ELEVENLABS_API_KEY"))
    elif provider == "openai":
        return OpenAITTSAdapter(api_key=os.getenv("OPENAI_API_KEY"))
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")
```

---

## Summary

| Aspect | Design Choice | Rationale |
|--------|---------------|-----------|
| **Interface style** | Async-first | TTS is I/O-bound, supports modern async apps |
| **Error handling** | Explicit exception hierarchy | Clear failure modes, actionable recovery |
| **Core method** | `synthesize()` (async) | All providers support this |
| **Streaming** | Abstract `stream()` | No silent buffering, explicit support required |
| **Voice config** | Base class + provider subclasses | Type-safe, extensible, Open-Closed Principle |
| **Audio format** | `AudioFormat` + `AudioQuality` enums | Abstract quality control, adapters map to provider formats |
| **Format mapping** | Adapter internal `_FORMAT_MAP` | Each adapter translates to provider-specific strings |
| **AudioResult** | Fully populated by adapter | Calculate missing values (e.g., duration) when possible |
| **Input validation** | `_validate_input()` hook | Common checks in base; adapters add provider-specific validation |
| **Text limits** | `_validate_text_length()` | Called by `_validate_input()`; app handles chunking |
| **Text preprocessing** | `_preprocess_text()` hook | Adapters override to strip/transform provider-specific syntax |
| **Style control** | In provider-specific config | `style_prompt` for OpenAI/Google, `ssml` for Azure |
| **Audio tags** | In text, adapter strips if unsupported | ElevenLabs-specific, graceful degradation via `_preprocess_text` |
| **Capability discovery** | Abstract properties | Runtime introspection, all must be implemented |
| **Lifecycle** | Async context manager | Clean resource management |
| **API keys** | Explicit or env var fallback | `api_key` param or `PROVIDER_API_KEY` env var |
