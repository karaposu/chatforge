# STTPort (Speech-to-Text) Design Document

## Overview

**STTPort** provides a unified interface for transcribing audio to text. This enables applications to use different transcription providers (Whisper, Deepgram, AssemblyAI) without coupling to specific implementations.

## Problem Statement

### Current State

Transcription is fragmented across different services:

```
OpenAI Realtime API  →  Built-in transcription (Whisper)
Whisper API          →  Separate, batch only
Deepgram             →  Streaming, real-time
AssemblyAI           →  Features like diarization
Google Cloud         →  Enterprise, many languages
```

No unified interface means:
- Code tightly coupled to specific provider
- Can't easily switch providers (cost, accuracy, features)
- Different APIs for streaming vs batch
- Hard to test without real API calls

### Desired State

```
chatforge/
  ports/
    stt.py  ← Unified interface
  adapters/
    stt/
      whisper.py      ← OpenAI Whisper API
      whisper_local.py ← Local Whisper (faster-whisper)
      deepgram.py     ← Real-time streaming
      assemblyai.py   ← Advanced features
      google.py       ← Google Cloud STT
      azure.py        ← Azure Speech Services
```

---

## Use Cases

### 1. Real-Time Voice Chat Transcription

```python
# Transcribe user's speech in real-time
stt = DeepgramSTTAdapter(api_key=key)

async with stt.stream() as session:
    async for chunk in audio.start_capture():
        await session.send_audio(chunk)

    async for result in session.results():
        if result.is_final:
            print(f"User said: {result.text}")
        else:
            print(f"Partial: {result.text}")
```

### 2. Batch Transcription (Audio Files)

```python
# Transcribe a recording
stt = WhisperSTTAdapter()

result = await stt.transcribe(
    audio=audio_bytes,
    language="en",
    timestamps=True,
)

print(f"Transcript: {result.text}")
for segment in result.segments:
    print(f"[{segment.start_ms}-{segment.end_ms}] {segment.text}")
```

### 3. Meeting Transcription with Speaker Diarization

```python
# Identify who said what
stt = AssemblyAISTTAdapter(api_key=key)

result = await stt.transcribe(
    audio=meeting_audio,
    diarization=True,
    speaker_count=4,
)

for utterance in result.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}")
```

### 4. Multi-Language Support

```python
# Auto-detect language
stt = WhisperSTTAdapter()

result = await stt.transcribe(
    audio=audio_bytes,
    language="auto",  # Auto-detect
)

print(f"Detected language: {result.language}")
print(f"Transcript: {result.text}")
```

### 5. Local/Offline Transcription

```python
# No API calls, runs locally
stt = WhisperLocalSTTAdapter(model="base")  # tiny, base, small, medium, large

result = await stt.transcribe(audio_bytes)
print(result.text)
```

### 6. Fallback Chain

```python
# Try fast provider first, fallback to accurate
stt = STTFallbackChain([
    DeepgramSTTAdapter(),      # Fast, streaming
    WhisperSTTAdapter(),       # Accurate fallback
])

result = await stt.transcribe(audio_bytes)
```

---

## Architecture

### Port Interface

```
┌─────────────────────────────────────────────────────────────┐
│                         STTPort                             │
│                   (Abstract Interface)                      │
├─────────────────────────────────────────────────────────────┤
│  Batch:                                                     │
│    transcribe(audio, language, ...) -> TranscriptResult     │
│                                                             │
│  Streaming:                                                 │
│    stream() -> STTStreamSession                             │
│                                                             │
│  Properties:                                                │
│    provider_name: str                                       │
│    supports_streaming: bool                                 │
│    supported_languages: list[str]                           │
│    supports_diarization: bool                               │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────┴───────┐   ┌──────┴──────┐   ┌────────┴────────┐
│    Whisper    │   │  Deepgram   │   │   AssemblyAI    │
│    Adapter    │   │   Adapter   │   │    Adapter      │
├───────────────┤   ├─────────────┤   ├─────────────────┤
│ OpenAI API    │   │ Real-time   │   │ Diarization     │
│ Batch only    │   │ Streaming   │   │ Sentiment       │
│ 25MB limit    │   │ Interim     │   │ Summarization   │
└───────────────┘   └─────────────┘   └─────────────────┘
        │
┌───────┴───────┐
│ WhisperLocal  │
│   Adapter     │
├───────────────┤
│ faster-whisper│
│ Offline       │
│ No API calls  │
└───────────────┘
```

### Streaming Architecture

```
┌────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Audio    │────►│  STTStreamSession │────►│  Results    │
│   Chunks   │     │                  │     │  (async)    │
└────────────┘     │  send_audio()    │     └─────────────┘
                   │  results()       │
                   │  close()         │
                   └──────────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
              WebSocket          gRPC
              (Deepgram)      (Google)
```

---

## Port Interface Specification

### Data Classes

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, AsyncIterator


class TranscriptType(Enum):
    """Type of transcript result."""
    PARTIAL = "partial"      # Interim, may change
    FINAL = "final"          # Complete, won't change


@dataclass
class WordTimestamp:
    """Word-level timing information."""
    word: str
    start_ms: int
    end_ms: int
    confidence: float = 1.0


@dataclass
class TranscriptSegment:
    """A segment of transcribed audio."""
    text: str
    start_ms: int
    end_ms: int
    confidence: float = 1.0
    words: list[WordTimestamp] = field(default_factory=list)
    speaker: Optional[str] = None  # For diarization


@dataclass
class TranscriptResult:
    """Complete transcription result."""
    text: str
    language: Optional[str] = None
    confidence: float = 1.0
    duration_ms: Optional[int] = None

    # Detailed segments
    segments: list[TranscriptSegment] = field(default_factory=list)

    # Diarization
    speakers: list[str] = field(default_factory=list)
    utterances: list[TranscriptSegment] = field(default_factory=list)

    # Metadata
    request_id: Optional[str] = None
    model: Optional[str] = None


@dataclass
class StreamingResult:
    """Result from streaming transcription."""
    text: str
    type: TranscriptType
    confidence: float = 1.0

    # Timing (if available)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None

    # Words (for final results)
    words: list[WordTimestamp] = field(default_factory=list)

    # Is this the last result?
    is_endpoint: bool = False


@dataclass
class STTConfig:
    """Configuration for transcription."""
    language: str = "en"              # BCP-47 code or "auto"

    # Features
    timestamps: bool = False          # Word-level timestamps
    diarization: bool = False         # Speaker identification
    speaker_count: Optional[int] = None
    punctuation: bool = True          # Auto-punctuation
    profanity_filter: bool = False

    # Model selection
    model: Optional[str] = None       # Provider-specific model

    # Audio format hints
    sample_rate: int = 24000
    channels: int = 1
    encoding: str = "pcm16"           # pcm16, flac, mp3, etc.


@dataclass
class STTCapabilities:
    """What the provider supports."""
    provider_name: str
    supports_streaming: bool = False
    supports_diarization: bool = False
    supports_timestamps: bool = True
    supports_interim_results: bool = False
    max_audio_duration_seconds: Optional[int] = None
    max_file_size_bytes: Optional[int] = None
    supported_languages: list[str] = field(default_factory=list)
    supported_formats: list[str] = field(default_factory=list)
```

### Exceptions

```python
class STTError(Exception):
    """Base exception for STT errors."""
    pass


class STTNetworkError(STTError):
    """Network or connection error."""
    pass


class STTAuthenticationError(STTError):
    """Invalid API key."""
    pass


class STTQuotaExceededError(STTError):
    """Usage quota exceeded."""
    pass


class STTAudioTooLongError(STTError):
    """Audio exceeds maximum duration."""
    pass


class STTUnsupportedFormatError(STTError):
    """Audio format not supported."""
    pass


class STTLanguageNotSupportedError(STTError):
    """Language not supported by provider."""
    pass
```

### Core Interface

```python
from abc import ABC, abstractmethod


class STTStreamSession(ABC):
    """
    Streaming transcription session.

    Usage:
        async with stt.stream() as session:
            # Send audio
            for chunk in audio_chunks:
                await session.send_audio(chunk)

            # Signal end of audio
            await session.finish()

            # Get results
            async for result in session.results():
                print(result.text)
    """

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """Send audio chunk to be transcribed."""
        pass

    @abstractmethod
    async def finish(self) -> None:
        """Signal end of audio stream."""
        pass

    @abstractmethod
    def results(self) -> AsyncIterator[StreamingResult]:
        """
        Iterate over transcription results.

        Yields:
            StreamingResult objects (partial and final)
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the session and release resources."""
        pass

    async def __aenter__(self) -> "STTStreamSession":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


class STTPort(ABC):
    """
    Abstract interface for Speech-to-Text providers.

    Supports both batch transcription (audio files) and
    streaming transcription (real-time audio).

    Example (batch):
        async with WhisperSTTAdapter() as stt:
            result = await stt.transcribe(audio_bytes)
            print(result.text)

    Example (streaming):
        async with DeepgramSTTAdapter() as stt:
            async with stt.stream() as session:
                for chunk in audio_stream:
                    await session.send_audio(chunk)

                async for result in session.results():
                    print(result.text)
    """

    # -------------------------------------------------------------------------
    # Abstract Properties
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'whisper', 'deepgram')."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this adapter supports streaming transcription."""
        pass

    # -------------------------------------------------------------------------
    # Batch Transcription
    # -------------------------------------------------------------------------

    @abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        config: STTConfig | None = None,
    ) -> TranscriptResult:
        """
        Transcribe audio to text (batch mode).

        Args:
            audio: Audio bytes (PCM16, WAV, MP3, etc.)
            config: Transcription configuration

        Returns:
            TranscriptResult with text and metadata

        Raises:
            STTAudioTooLongError: If audio exceeds max duration
            STTUnsupportedFormatError: If format not supported
            STTAuthenticationError: If API key invalid
            STTNetworkError: If network error occurs
        """
        pass

    # -------------------------------------------------------------------------
    # Streaming Transcription
    # -------------------------------------------------------------------------

    @abstractmethod
    def stream(
        self,
        config: STTConfig | None = None,
    ) -> STTStreamSession:
        """
        Start streaming transcription session.

        Args:
            config: Transcription configuration

        Returns:
            STTStreamSession for sending audio and receiving results

        Raises:
            STTError: If streaming not supported
        """
        pass

    # -------------------------------------------------------------------------
    # Capabilities
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_capabilities(self) -> STTCapabilities:
        """Get provider capabilities."""
        pass

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Release resources."""
        pass

    async def __aenter__(self) -> "STTPort":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
```

---

## Adapter Implementations

### 1. WhisperSTTAdapter (OpenAI API)

```python
# chatforge/adapters/stt/whisper.py

import httpx

class WhisperSTTAdapter(STTPort):
    """
    OpenAI Whisper API adapter.

    Features:
        - High accuracy
        - 98 languages
        - Word-level timestamps

    Limitations:
        - Batch only (no streaming)
        - 25MB file size limit
        - ~10 min audio max

    Requirements:
        OPENAI_API_KEY environment variable
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "whisper-1",
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model = model
        self._client: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        return "whisper"

    @property
    def supports_streaming(self) -> bool:
        return False  # Whisper API is batch only

    async def transcribe(
        self,
        audio: bytes,
        config: STTConfig | None = None,
    ) -> TranscriptResult:
        config = config or STTConfig()

        # Prepare request
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {
            "model": self._model,
            "response_format": "verbose_json",
        }

        if config.language != "auto":
            data["language"] = config.language

        if config.timestamps:
            data["timestamp_granularities"] = ["word", "segment"]

        # Make request
        response = await self._client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            files=files,
            data=data,
        )

        if response.status_code != 200:
            raise STTError(f"Whisper API error: {response.text}")

        result = response.json()

        # Parse response
        segments = []
        if "segments" in result:
            for seg in result["segments"]:
                words = []
                if "words" in seg:
                    words = [
                        WordTimestamp(
                            word=w["word"],
                            start_ms=int(w["start"] * 1000),
                            end_ms=int(w["end"] * 1000),
                        )
                        for w in seg["words"]
                    ]

                segments.append(TranscriptSegment(
                    text=seg["text"],
                    start_ms=int(seg["start"] * 1000),
                    end_ms=int(seg["end"] * 1000),
                    words=words,
                ))

        return TranscriptResult(
            text=result["text"],
            language=result.get("language"),
            segments=segments,
            duration_ms=int(result.get("duration", 0) * 1000),
            model=self._model,
        )

    def stream(self, config: STTConfig | None = None) -> STTStreamSession:
        raise STTError("Whisper API does not support streaming")

    def get_capabilities(self) -> STTCapabilities:
        return STTCapabilities(
            provider_name="whisper",
            supports_streaming=False,
            supports_diarization=False,
            supports_timestamps=True,
            max_file_size_bytes=25 * 1024 * 1024,  # 25MB
            supported_languages=["en", "es", "fr", "de", "ja", ...],  # 98 languages
            supported_formats=["mp3", "wav", "webm", "mp4", "m4a", "flac"],
        )
```

### 2. DeepgramSTTAdapter (Real-Time Streaming)

```python
# chatforge/adapters/stt/deepgram.py

import asyncio
import websockets
import json

class DeepgramStreamSession(STTStreamSession):
    """Deepgram WebSocket streaming session."""

    def __init__(self, ws, config: STTConfig):
        self._ws = ws
        self._config = config
        self._results_queue = asyncio.Queue()
        self._receive_task = None

    async def send_audio(self, chunk: bytes) -> None:
        await self._ws.send(chunk)

    async def finish(self) -> None:
        # Send close message
        await self._ws.send(json.dumps({"type": "CloseStream"}))

    async def results(self) -> AsyncIterator[StreamingResult]:
        while True:
            result = await self._results_queue.get()
            if result is None:  # End of stream
                break
            yield result

    async def _receive_loop(self):
        async for message in self._ws:
            data = json.loads(message)

            if data.get("type") == "Results":
                channel = data["channel"]["alternatives"][0]

                yield StreamingResult(
                    text=channel["transcript"],
                    type=TranscriptType.FINAL if data["is_final"] else TranscriptType.PARTIAL,
                    confidence=channel.get("confidence", 1.0),
                    words=[
                        WordTimestamp(
                            word=w["word"],
                            start_ms=int(w["start"] * 1000),
                            end_ms=int(w["end"] * 1000),
                            confidence=w.get("confidence", 1.0),
                        )
                        for w in channel.get("words", [])
                    ],
                )


class DeepgramSTTAdapter(STTPort):
    """
    Deepgram real-time STT adapter.

    Features:
        - True real-time streaming
        - Interim results
        - Low latency (~300ms)
        - Diarization
        - Custom vocabulary

    Requirements:
        DEEPGRAM_API_KEY environment variable
        pip install websockets
    """

    WEBSOCKET_URL = "wss://api.deepgram.com/v1/listen"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nova-2",
    ):
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        self._model = model

    @property
    def provider_name(self) -> str:
        return "deepgram"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def transcribe(
        self,
        audio: bytes,
        config: STTConfig | None = None,
    ) -> TranscriptResult:
        # Deepgram also supports batch via REST API
        config = config or STTConfig()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {self._api_key}",
                    "Content-Type": "audio/wav",
                },
                params={
                    "model": self._model,
                    "language": config.language,
                    "punctuate": config.punctuation,
                    "diarize": config.diarization,
                },
                content=audio,
            )

        data = response.json()
        # ... parse response
        return TranscriptResult(text=data["results"]["channels"][0]["alternatives"][0]["transcript"])

    def stream(self, config: STTConfig | None = None) -> STTStreamSession:
        config = config or STTConfig()

        # Build WebSocket URL with params
        params = {
            "model": self._model,
            "language": config.language,
            "punctuate": str(config.punctuation).lower(),
            "interim_results": "true",
            "encoding": "linear16",
            "sample_rate": config.sample_rate,
        }

        if config.diarization:
            params["diarize"] = "true"
            if config.speaker_count:
                params["diarize_version"] = "2"

        url = f"{self.WEBSOCKET_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        return DeepgramStreamSession(url, self._api_key, config)

    def get_capabilities(self) -> STTCapabilities:
        return STTCapabilities(
            provider_name="deepgram",
            supports_streaming=True,
            supports_diarization=True,
            supports_timestamps=True,
            supports_interim_results=True,
            supported_languages=["en", "es", "fr", "de", "ja", "ko", ...],
            supported_formats=["pcm16", "flac", "mp3", "wav", "ogg"],
        )
```

### 3. WhisperLocalSTTAdapter (Offline)

```python
# chatforge/adapters/stt/whisper_local.py

class WhisperLocalSTTAdapter(STTPort):
    """
    Local Whisper using faster-whisper.

    Features:
        - No API calls (offline)
        - Fast (CTranslate2 backend)
        - GPU support (CUDA)
        - No cost

    Requirements:
        pip install faster-whisper

    Models:
        tiny    - 39M params, ~1GB VRAM
        base    - 74M params, ~1GB VRAM
        small   - 244M params, ~2GB VRAM
        medium  - 769M params, ~5GB VRAM
        large-v3 - 1550M params, ~10GB VRAM
    """

    def __init__(
        self,
        model: str = "base",
        device: str = "auto",  # "cpu", "cuda", "auto"
        compute_type: str = "auto",  # "int8", "float16", "float32"
    ):
        from faster_whisper import WhisperModel

        self._model_name = model
        self._model = WhisperModel(
            model,
            device=device,
            compute_type=compute_type,
        )

    @property
    def provider_name(self) -> str:
        return "whisper-local"

    @property
    def supports_streaming(self) -> bool:
        return False  # Local Whisper is batch only

    async def transcribe(
        self,
        audio: bytes,
        config: STTConfig | None = None,
    ) -> TranscriptResult:
        config = config or STTConfig()

        # Convert bytes to numpy array
        import numpy as np
        audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

        # Run inference
        segments, info = self._model.transcribe(
            audio_array,
            language=None if config.language == "auto" else config.language,
            word_timestamps=config.timestamps,
        )

        # Collect results
        text_parts = []
        transcript_segments = []

        for segment in segments:
            text_parts.append(segment.text)

            words = []
            if config.timestamps and segment.words:
                words = [
                    WordTimestamp(
                        word=w.word,
                        start_ms=int(w.start * 1000),
                        end_ms=int(w.end * 1000),
                        confidence=w.probability,
                    )
                    for w in segment.words
                ]

            transcript_segments.append(TranscriptSegment(
                text=segment.text,
                start_ms=int(segment.start * 1000),
                end_ms=int(segment.end * 1000),
                words=words,
            ))

        return TranscriptResult(
            text=" ".join(text_parts),
            language=info.language,
            confidence=info.language_probability,
            segments=transcript_segments,
            model=self._model_name,
        )

    def stream(self, config: STTConfig | None = None) -> STTStreamSession:
        raise STTError("Local Whisper does not support streaming")

    def get_capabilities(self) -> STTCapabilities:
        return STTCapabilities(
            provider_name="whisper-local",
            supports_streaming=False,
            supports_diarization=False,
            supports_timestamps=True,
            supported_languages=["en", "es", "fr", ...],  # 98 languages
            supported_formats=["pcm16", "wav", "mp3", "flac"],
        )
```

### 4. AssemblyAISTTAdapter (Advanced Features)

```python
# chatforge/adapters/stt/assemblyai.py

class AssemblyAISTTAdapter(STTPort):
    """
    AssemblyAI adapter with advanced features.

    Features:
        - Speaker diarization
        - Sentiment analysis
        - Auto chapters
        - Content moderation
        - PII redaction
        - Summarization

    Requirements:
        ASSEMBLYAI_API_KEY environment variable
        pip install assemblyai
    """

    def __init__(self, api_key: str | None = None):
        import assemblyai as aai
        self._api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        aai.settings.api_key = self._api_key
        self._transcriber = aai.Transcriber()

    @property
    def provider_name(self) -> str:
        return "assemblyai"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def transcribe(
        self,
        audio: bytes,
        config: STTConfig | None = None,
    ) -> TranscriptResult:
        import assemblyai as aai

        config = config or STTConfig()

        # Build config
        aai_config = aai.TranscriptionConfig(
            language_code=config.language if config.language != "auto" else None,
            language_detection=config.language == "auto",
            punctuate=config.punctuation,
            speaker_labels=config.diarization,
        )

        if config.speaker_count:
            aai_config.speakers_expected = config.speaker_count

        # Transcribe
        transcript = await asyncio.to_thread(
            self._transcriber.transcribe,
            audio,
            config=aai_config,
        )

        # Parse results
        utterances = []
        if transcript.utterances:
            for u in transcript.utterances:
                utterances.append(TranscriptSegment(
                    text=u.text,
                    start_ms=u.start,
                    end_ms=u.end,
                    speaker=f"Speaker {u.speaker}",
                ))

        return TranscriptResult(
            text=transcript.text,
            language=transcript.language_code,
            confidence=transcript.confidence,
            utterances=utterances,
            speakers=[f"Speaker {i}" for i in range(len(set(u.speaker for u in transcript.utterances or [])))],
        )

    def get_capabilities(self) -> STTCapabilities:
        return STTCapabilities(
            provider_name="assemblyai",
            supports_streaming=True,
            supports_diarization=True,
            supports_timestamps=True,
            supports_interim_results=True,
            supported_languages=["en", "es", "fr", "de", ...],
            supported_formats=["mp3", "wav", "flac", "m4a", "webm"],
        )
```

---

## Comparison

| Provider | Streaming | Diarization | Accuracy | Latency | Cost | Offline |
|----------|-----------|-------------|----------|---------|------|---------|
| **Whisper (API)** | No | No | Excellent | High | $0.006/min | No |
| **Whisper (Local)** | No | No | Excellent | Varies | Free | Yes |
| **Deepgram** | Yes | Yes | Very Good | Low (~300ms) | $0.0043/min | No |
| **AssemblyAI** | Yes | Yes | Excellent | Medium | $0.00025/sec | No |
| **Google Cloud** | Yes | Yes | Very Good | Low | $0.006/15sec | No |
| **Azure** | Yes | Yes | Very Good | Low | $1/hr | No |

---

## Integration Examples

### With VoiceSession (Real-Time)

```python
from chatforge.adapters.stt import DeepgramSTTAdapter

# Create STT
stt = DeepgramSTTAdapter()

# Use alongside realtime voice
async with VoiceSession(...) as session:
    # OpenAI provides transcription, but we can also use our own
    async with stt.stream() as stt_session:
        async for chunk in audio.start_capture():
            # Send to AI
            await session.realtime.send_audio(chunk)

            # Also transcribe locally for logging
            await stt_session.send_audio(chunk)

        # Get transcripts
        async for result in stt_session.results():
            log_transcript(result.text)
```

### Batch Processing Pipeline

```python
from chatforge.adapters.stt import WhisperLocalSTTAdapter

stt = WhisperLocalSTTAdapter(model="medium")

# Process multiple files
for audio_file in audio_files:
    audio = audio_file.read_bytes()
    result = await stt.transcribe(audio, STTConfig(
        timestamps=True,
        language="auto",
    ))

    save_transcript(audio_file.stem, result)
```

### Meeting Transcription

```python
from chatforge.adapters.stt import AssemblyAISTTAdapter

stt = AssemblyAISTTAdapter()

result = await stt.transcribe(
    meeting_audio,
    STTConfig(
        diarization=True,
        speaker_count=4,
        timestamps=True,
    ),
)

# Generate meeting notes
print("## Meeting Transcript\n")
for utterance in result.utterances:
    time = f"[{utterance.start_ms // 1000}s]"
    print(f"{time} **{utterance.speaker}**: {utterance.text}")
```

---

## Migration Plan

### Phase 1: Core Port Interface

1. Create `chatforge/ports/stt.py` with STTPort interface
2. Define data classes (TranscriptResult, etc.)
3. Define exceptions

### Phase 2: Initial Adapters

1. WhisperSTTAdapter (OpenAI API)
2. WhisperLocalSTTAdapter (faster-whisper)
3. Unit tests with sample audio

### Phase 3: Streaming Support

1. DeepgramSTTAdapter with WebSocket streaming
2. STTStreamSession interface
3. Integration tests

### Phase 4: Advanced Features

1. AssemblyAISTTAdapter (diarization)
2. Google Cloud STT adapter
3. Azure Speech adapter

### Phase 5: Integration

1. Optional STT injection into VoiceSession
2. Transcript logging middleware
3. Documentation and examples

---

## Open Questions

1. **Streaming backpressure**: How to handle slow consumers?
   - Option A: Buffer results
   - Option B: Drop old partials
   - Option C: Configurable behavior

2. **Audio format conversion**: Should adapters handle format conversion?
   - Some require specific formats (Deepgram: linear16)
   - Could use AudioProcessingPort for conversion

3. **Caching**: Should we cache transcriptions?
   - Useful for repeated audio
   - Hash audio content as key

4. **Fallback chains**: How to implement automatic fallback?
   - Try provider A, fallback to B on error
   - Could be separate FallbackSTTAdapter

5. **Cost tracking**: Should we track API costs?
   - Useful for budgeting
   - Per-request and cumulative

---

## References

- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Deepgram API](https://developers.deepgram.com/docs)
- [AssemblyAI API](https://www.assemblyai.com/docs)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/docs)
- [Azure Speech Services](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
