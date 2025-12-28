# Deep Analysis: ChamberProtocolAI ElevenLabs TTS Implementation

Analysis of current TTS implementation and how a Chatforge TTS port could provide value.

---

## Problem Analysis

### Current Implementation Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  CURRENT TTS ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Unity Client                                                   │
│       │                                                          │
│       ▼                                                          │
│   POST /elevenlabs/tts                                          │
│       │                                                          │
│       ▼                                                          │
│   elevenlabs_api.py ──► elevenlabs_tts.py ──► ElevenLabs SDK    │
│       │                       │                     │            │
│       │                       │                     ▼            │
│       │                       │              ElevenLabs API      │
│       │                       │                     │            │
│       ▼                       ▼                     ▼            │
│   Base64 Response  ◄──  audio bytes  ◄──────  audio stream      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  TIGHT COUPLING: Every layer directly depends on ElevenLabs     │
└─────────────────────────────────────────────────────────────────┘
```

### Files Analyzed

| File | Purpose |
|------|---------|
| `ElevenlabsService/ElevenLabsV3.py` | Standalone FastAPI service with streaming |
| `src/utils/elevenlabs_tts.py` | Utility function for TTS conversion |
| `src/apis/elevenlabs_api.py` | FastAPI router endpoint |
| `src/models/elevenlabs_request.py` | Pydantic request model |
| `src/models/elevenlabs_response.py` | Pydantic response model |
| `test_elevenlabs.py` | Test script |

### Core Strengths

| Aspect | Implementation | Quality |
|--------|---------------|---------|
| **Audio Tag Support** | `[whispers]`, `[pause]`, `[laughs]` | ✅ Well-designed |
| **V3 Model Normalization** | Snaps stability to 0.0/0.5/1.0 | ✅ Handles quirks |
| **Base64 Response** | Unity-friendly encoding | ✅ Client-optimized |
| **Format Flexibility** | MP3, WAV at various sample rates | ✅ Good options |
| **Error Categorization** | Rate limit, quota, invalid voice | ✅ Meaningful errors |

### Core Weaknesses

| Issue | Location | Impact |
|-------|----------|--------|
| **Hardcoded Voice ID** | `JBFqnCBsd6RMkjVDRZzb` default | Character locked in |
| **No Caching** | Every call hits API | Cost, latency |
| **No Fallback** | Single provider | Outage = silence |
| **Duplicated Logic** | v3 normalization in 2 places | Maintenance burden |
| **Direct SDK Coupling** | `from elevenlabs import ElevenLabs` | Switching cost |
| **No Cost Tracking** | Missing usage metrics | Budget blindness |

---

## Multi-Dimensional Analysis

### Technical Perspective

**Current Pain Points:**

1. **Provider Lock-in**: Direct ElevenLabs SDK usage means:
   - No A/B testing between providers
   - No fallback when ElevenLabs has issues
   - Can't optimize cost per quality tier

2. **Missing Infrastructure:**
   ```python
   # Current: Raw SDK call every time
   audio_stream = client.text_to_speech.convert(text=text, ...)

   # Missing:
   # - Audio caching layer
   # - Request deduplication
   # - Usage tracking
   # - Quality monitoring
   ```

3. **Character Voice Management**:
   - Silüet's voice ID is hardcoded
   - What about multi-character games?
   - Voice versioning (if ElevenLabs changes voice)?

### Business Perspective

**Cost Analysis:**
- ElevenLabs pricing: ~$0.30/1000 characters (Pro tier)
- A typical Silüet response: 50-100 characters
- Cost per response: $0.015-0.03
- 10,000 daily responses = $150-300/day

**Multi-Provider Value:**

| Provider | Cost/1K chars | Quality | Latency |
|----------|---------------|---------|---------|
| ElevenLabs v3 | $0.30 | Excellent | ~500ms |
| OpenAI TTS | $0.015 | Good | ~300ms |
| Azure TTS | $0.016 | Good | ~200ms |
| Google TTS | $0.016 | Good | ~200ms |

**Insight**: OpenAI TTS is **20x cheaper** - could handle fallback/non-critical audio.

### User Perspective

**Player Experience Considerations:**

1. **Latency Budget**: Voice response must feel immediate
   - Current: API call → process → base64 → decode → play
   - Optimal: Pre-cache common phrases, stream long responses

2. **Audio Consistency**: Silüet's voice should be consistent
   - ElevenLabs voice cloning is provider-specific
   - Need voice abstraction that preserves character identity

3. **Graceful Degradation**:
   - If TTS fails, what happens?
   - Text fallback? Cached "I can't speak right now"?

---

## Chatforge TTS Port Design

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CHATFORGE TTS PORT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Application Layer                                                   │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                      get_tts(provider="elevenlabs")          │   │
│   │                              │                                │   │
│   │                      ┌───────┴───────┐                       │   │
│   │                      ▼               ▼                       │   │
│   │              TTSConfig         TTSFactory                    │   │
│   │              (settings)        (creates adapters)            │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                  │                                    │
│   Port Layer (Interface)         │                                    │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                         TTSPort                               │   │
│   │  ─────────────────────────────────────────────────────────   │   │
│   │  + synthesize(text, voice_id, **opts) -> AudioResult         │   │
│   │  + stream(text, voice_id, **opts) -> Iterator[bytes]         │   │
│   │  + list_voices() -> list[VoiceInfo]                          │   │
│   │  + get_voice(voice_id) -> VoiceInfo                          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                  │                                    │
│   Adapter Layer (Implementations)│                                    │
│   ┌──────────────┬───────────────┼───────────────┬──────────────┐   │
│   │ ElevenLabs   │   OpenAI      │    Azure      │   Google     │   │
│   │ TTSAdapter   │   TTSAdapter  │   TTSAdapter  │  TTSAdapter  │   │
│   └──────────────┴───────────────┴───────────────┴──────────────┘   │
│          │               │               │               │            │
│          ▼               ▼               ▼               ▼            │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    Provider APIs                              │   │
│   │    ElevenLabs    OpenAI TTS    Azure TTS    Google TTS       │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### TTSPort Interface

```python
# chatforge/ports/tts.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional

@dataclass
class AudioResult:
    """Result from TTS synthesis."""
    audio_bytes: bytes
    format: str  # "mp3", "wav", "opus"
    sample_rate: int
    duration_ms: Optional[int] = None
    characters_used: int = 0

@dataclass
class VoiceInfo:
    """Voice metadata."""
    voice_id: str
    name: str
    provider: str
    language: str
    gender: Optional[str] = None
    preview_url: Optional[str] = None

class TTSPort(ABC):
    """Port interface for Text-to-Speech providers."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        *,
        model: Optional[str] = None,
        output_format: str = "mp3",
        speed: float = 1.0,
        **provider_options
    ) -> AudioResult:
        """Convert text to speech, return complete audio."""
        pass

    @abstractmethod
    def stream(
        self,
        text: str,
        voice_id: str,
        *,
        model: Optional[str] = None,
        output_format: str = "mp3",
        **provider_options
    ) -> Iterator[bytes]:
        """Stream audio chunks as they're generated."""
        pass

    @abstractmethod
    def list_voices(self) -> list[VoiceInfo]:
        """List available voices for this provider."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier."""
        pass
```

### TTSConfig (Settings)

```python
# chatforge/config/tts.py
from pydantic_settings import BaseSettings

class TTSSettings(BaseSettings):
    """TTS configuration from environment variables."""

    # Provider selection
    provider: str = "elevenlabs"  # elevenlabs, openai, azure, google

    # Default voice settings
    default_voice_id: str | None = None
    default_model: str | None = None
    default_format: str = "mp3_44100_128"

    # ElevenLabs
    elevenlabs_api_key: str | None = None
    elevenlabs_default_voice: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model: str = "eleven_v3"

    # OpenAI TTS
    openai_tts_voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    openai_tts_model: str = "tts-1"  # tts-1, tts-1-hd

    # Azure
    azure_speech_key: str | None = None
    azure_speech_region: str = "eastus"

    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 24

    # Fallback chain
    fallback_providers: list[str] = []  # ["openai", "azure"]

    class Config:
        env_prefix = "TTS_"
        extra = "ignore"

tts_config = TTSSettings()
```

### Factory Function

```python
# chatforge/services/tts/factory.py
from chatforge.config.tts import tts_config
from chatforge.ports.tts import TTSPort

def get_tts(
    provider: str | None = None,
    **override_settings
) -> TTSPort:
    """
    Get TTS adapter based on provider configuration.

    Usage:
        tts = get_tts()  # Uses TTS_PROVIDER env var
        tts = get_tts(provider="openai")  # Explicit provider

        audio = tts.synthesize("Hello world", voice_id="alloy")
    """
    provider = provider or tts_config.provider

    if provider == "elevenlabs":
        return _get_elevenlabs_tts(**override_settings)
    elif provider == "openai":
        return _get_openai_tts(**override_settings)
    elif provider == "azure":
        return _get_azure_tts(**override_settings)
    elif provider == "google":
        return _get_google_tts(**override_settings)
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")
```

---

## Solution Options

### Option 1: Minimal Port (TTSPort Only)

**Description**: Create just the port interface and ElevenLabs adapter.

```python
# ChamberProtocolAI usage after migration
from chatforge.services.tts import get_tts

tts = get_tts(provider="elevenlabs")
audio = tts.synthesize(
    text="[whispers] Can you hear me?",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model="eleven_v3"
)
```

| Pros | Cons |
|------|------|
| Quick to implement | Limited value vs current |
| Clean abstraction | Still single-provider |
| Consistent with LLM pattern | No caching yet |

**Effort**: ~4 hours

---

### Option 2: Multi-Provider TTS with Fallback

**Description**: Full port with ElevenLabs + OpenAI TTS adapters and automatic fallback.

```python
# Automatic fallback chain
tts = get_tts(fallback=["openai"])  # Try ElevenLabs, fallback to OpenAI

# Or explicit selection per quality tier
premium_tts = get_tts(provider="elevenlabs")  # For Silüet dialogue
cheap_tts = get_tts(provider="openai")  # For system messages
```

| Pros | Cons |
|------|------|
| 99.9% uptime | More complex |
| Cost optimization | Voice consistency challenges |
| A/B testing capability | Different audio quality |

**Effort**: ~8 hours

---

### Option 3: Full TTS Service with Caching

**Description**: Complete TTS service with caching layer, usage tracking, and voice management.

```
┌─────────────────────────────────────────────────────────────┐
│                    CachedTTSService                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │ Text Hash   │────►│ Cache Check │────►│ Return Cache│   │
│  │ Generator   │     │ (Redis/Mem) │     │ if exists   │   │
│  └─────────────┘     └──────┬──────┘     └─────────────┘   │
│                             │ miss                          │
│                             ▼                               │
│                      ┌─────────────┐                        │
│                      │  TTSPort    │                        │
│                      │  Synthesis  │                        │
│                      └──────┬──────┘                        │
│                             │                               │
│                      ┌──────┴──────┐                        │
│                      │ Store Cache │                        │
│                      │ + Track Use │                        │
│                      └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Caching Strategy:**
```python
# Common Silüet phrases cached:
CACHE_PATTERNS = [
    r"^\[whispers\].*$",      # Whispered intros
    r"^Hmm\.{3}$",            # Thinking sounds
    r"^[Gg]üzel\.*$",         # Turkish "good"
    # etc.
]

# Hash-based deduplication:
# "Hello there" + voice_id + model → hash → lookup
```

| Pros | Cons |
|------|------|
| Massive cost savings | Infrastructure overhead |
| Sub-10ms for cached | Cache invalidation complexity |
| Usage analytics | Redis/storage dependency |

**Effort**: ~16 hours

---

## Recommendation

### Phased Approach

```
Phase 1: TTSPort Interface (Week 1)
├── Define TTSPort abstract class
├── Create ElevenLabsTTSAdapter
├── Create get_tts() factory
└── Migrate ChamberProtocolAI to use it

Phase 2: OpenAI TTS Adapter (Week 2)
├── Implement OpenAITTSAdapter
├── Add fallback chain logic
└── Voice mapping (Silüet → OpenAI approximation)

Phase 3: Caching Layer (Week 3)
├── Hash-based cache key generation
├── In-memory cache (start simple)
├── Cache hit/miss metrics
└── Pre-warm common phrases
```

### Immediate Value for ChamberProtocolAI

**Before (Current):**
```python
# src/utils/elevenlabs_tts.py
from elevenlabs import ElevenLabs
client = ElevenLabs(api_key=api_key)
audio_stream = client.text_to_speech.convert(...)
```

**After (With Chatforge TTS Port):**
```python
# src/utils/tts_service.py
from chatforge.services.tts import get_tts

class SiluetVoiceService:
    def __init__(self):
        self.tts = get_tts()  # Uses TTS_PROVIDER from .env
        self.voice_id = tts_config.elevenlabs_default_voice

    def speak(self, text: str, *, stream: bool = False):
        if stream:
            return self.tts.stream(text, self.voice_id)
        else:
            return self.tts.synthesize(text, self.voice_id)
```

**Benefits:**
1. **Consistency**: Same pattern as `get_llm()` - developers know it
2. **Testability**: Mock `TTSPort` in tests, no API calls
3. **Flexibility**: Switch providers via environment variable
4. **Future-proof**: Add new providers without changing app code

---

## Alternative Perspectives

### Contrarian View: "Just Use ElevenLabs SDK Directly"

**Argument**: ElevenLabs is the best TTS for character voices. Why abstract?

**Counter**:
- ElevenLabs had 3 major outages in 2024
- Their API changes frequently (v2 → v3 breaking changes)
- Abstraction cost is low, insurance value is high

### Future Considerations

1. **Real-time Voice Cloning**: ElevenLabs and PlayHT now support instant cloning
   - Port should accommodate `clone_voice(audio_sample) -> voice_id`

2. **Emotion Tags Standardization**:
   - ElevenLabs: `[whispers]`, `[laughs]`
   - OpenAI: Not supported
   - Need adapter to strip/convert tags per provider

3. **SSML Support**:
   - Some providers use SSML, others don't
   - Port could accept SSML and convert per-adapter

---

## Summary

| Aspect | Current State | With Chatforge TTS Port |
|--------|---------------|-------------------------|
| **Provider Coupling** | Tight (ElevenLabs only) | Loose (pluggable) |
| **Fallback** | None | Configurable chain |
| **Caching** | None | Optional layer |
| **Testing** | Requires API | Mockable interface |
| **Cost Visibility** | None | `AudioResult.characters_used` |
| **Voice Management** | Hardcoded | Configurable |

**Bottom Line**: The TTS port follows the exact same hexagonal architecture pattern that made the LLM migration successful. It would:
- Reduce vendor lock-in risk
- Enable cost optimization through provider selection
- Provide consistent developer experience
- Allow for future enhancements (caching, analytics) without app changes
