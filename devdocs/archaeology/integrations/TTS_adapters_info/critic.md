# TTSPort Design Specification - Critical Analysis

---

### 5. Text Length Limits Not Addressed

**The Problem**: Providers have different text length limits:

| Provider | Limit |
|----------|-------|
| ElevenLabs | ~5,000 chars |
| OpenAI | 4,096 chars |
| Azure | 10 minutes of audio |
| Google | 5,000 bytes |

**Questions Unanswered**:
- Should adapters auto-chunk long text?
- Should port expose `max_text_length` property?
- What happens when limit exceeded?

**Recommendation**:
```python
class TTSPort(ABC):
    @property
    @abstractmethod
    def max_text_length(self) -> int:
        """Maximum characters per request."""
        pass

    def chunk_text(self, text: str) -> list[str]:
        """Split text into synthesizable chunks."""
        # Default implementation with sentence boundary detection
        pass
```

---

### 6. Audio Format Mapping is Incomplete

**The Problem**: AudioFormat enum doesn't map to all provider formats.

```python
class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG_OPUS = "ogg_opus"
    PCM = "pcm"
    FLAC = "flac"
    AAC = "aac"
```

**Missing**:
- Sample rate specifications (ElevenLabs: `mp3_44100_128` vs `mp3_22050_32`)
- Bit depth for PCM (16-bit, 24-bit)
- Azure's complex format enum (`Audio16Khz128KBitRateMonoMp3`)
- ulaw/alaw for telephony

**Recommendation**:
```python
@dataclass
class AudioConfig:
    format: AudioFormat
    sample_rate: int = 44100
    bit_depth: int = 16
    channels: int = 1
    bitrate_kbps: Optional[int] = None  # For lossy formats
```

---

### 7. No Rate Limiting Strategy

**The Problem**: Providers have strict rate limits:

| Provider | Limits |
|----------|--------|
| ElevenLabs | Varies by plan (10-100+ concurrent) |
| OpenAI | 500 RPM |
| Azure | Varies by tier |
| Google | Varies by tier |

**Impact**: Applications will hit rate limits and fail unexpectedly.

**Recommendation**: Either:
1. Document that rate limiting is application responsibility
2. Add optional rate limiter interface
3. Expose rate limit info for applications to use

```python
@dataclass
class RateLimitInfo:
    requests_remaining: Optional[int]
    reset_at: Optional[datetime]

class TTSPort(ABC):
    def get_rate_limit_info(self) -> Optional[RateLimitInfo]:
        """Return current rate limit status if available."""
        return None
```

---

### 8. preprocess_text() Has Unclear Semantics

**The Problem**: The spec says preprocess_text can:
- Strip unsupported tags
- Convert style_prompt to provider-specific format
- Apply SSML wrapping

But it's unclear when it's called and by whom.

```python
def preprocess_text(self, text: str, config: VoiceConfig) -> str:
    return text  # Default does nothing
```

**Questions**:
- Is it called automatically by synthesize()?
- Should applications call it explicitly?
- Should it be private (_preprocess_text)?

**Recommendation**: Make it private and call internally:

```python
def synthesize(self, text: str, config: VoiceConfig, ...) -> AudioResult:
    processed_text = self._preprocess_text(text, config)
    return self._do_synthesis(processed_text, config, ...)

def _preprocess_text(self, text: str, config: VoiceConfig) -> str:
    """Internal hook for text preprocessing."""
    return text
```

---

### 9. VoiceInfo Lacks Critical Metadata

**The Problem**: VoiceInfo is missing important decision-making data:

```python
@dataclass
class VoiceInfo:
    voice_id: str
    name: str
    provider: str
    language_codes: list[str]
    gender: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    supports_ssml: bool = False
    supports_streaming: bool = True
```

**Missing**:
- Voice age/style category (child, young adult, elderly)
- Use case suitability (narration, conversation, announcement)
- Pricing tier (standard vs. premium)
- Quality tier (tts-1 vs tts-1-hd)
- Supported audio formats
- Custom/cloned vs. built-in

**Recommendation**:
```python
@dataclass
class VoiceInfo:
    # ... existing fields ...

    # Additional metadata
    category: Optional[str] = None  # "narration", "conversational", etc.
    age_group: Optional[str] = None  # "child", "adult", "elderly"
    is_custom: bool = False  # Custom/cloned voice
    quality_tier: Optional[str] = None  # "standard", "hd"
    supported_formats: list[AudioFormat] = field(default_factory=list)
```

---

### 10. No Caching Interface

**The Problem**: TTS is expensive. The spec mentions caching in the analysis but provides no interface.

**Cost Reality**:
- ElevenLabs: $0.30/1K chars
- OpenAI: $0.015/1K chars
- Same text = same audio = wasteful to regenerate

**Recommendation**: Optional caching interface:

```python
from abc import ABC, abstractmethod

class TTSCache(ABC):
    @abstractmethod
    def get(self, text: str, config: VoiceConfig, format: AudioFormat) -> Optional[bytes]:
        pass

    @abstractmethod
    def set(self, text: str, config: VoiceConfig, format: AudioFormat, audio: bytes) -> None:
        pass

class TTSPort(ABC):
    def __init__(self, cache: Optional[TTSCache] = None):
        self._cache = cache
```

Or leave caching entirely to application layer (decorator pattern).

---

## Minor Issues

### 11. Inconsistent Capability Discovery

Some capabilities are properties, some are methods:

```python
@property
def supports_streaming(self) -> bool: pass

@property
def supports_ssml(self) -> bool: pass

@property
def supports_style_prompt(self) -> bool:
    return False  # Why is this one not abstract?
```

**Recommendation**: Make all capability properties abstract and consistent:

```python
@property
@abstractmethod
def supports_streaming(self) -> bool: pass

@property
@abstractmethod
def supports_ssml(self) -> bool: pass

@property
@abstractmethod
def supports_style_prompt(self) -> bool: pass
```

---

### 12. AudioResult.duration_ms Optional But Important

**The Problem**: Duration is optional but essential for:
- Progress tracking
- Billing calculations
- UI display

```python
duration_ms: Optional[int] = None
```

Most providers return duration. It should be encouraged.

---

### 13. No Input Validation Contract

**The Problem**: What validates input before synthesis?

- Empty text?
- Text with only whitespace?
- Invalid SSML?
- Conflicting options (ssml + style_prompt)?

**Recommendation**: Add validation method:

```python
def validate(self, text: str, config: VoiceConfig) -> list[str]:
    """Return list of validation warnings/errors."""
    errors = []
    if not text.strip():
        errors.append("Text cannot be empty")
    if config.ssml and config.style_prompt:
        errors.append("Cannot use both SSML and style_prompt")
    return errors
```

---

### 14. Characters Used vs. Billed Characters

**The Problem**: `characters_used` in AudioResult is ambiguous.

```python
characters_used: int = 0
```

- Is this input characters or billed characters?
- ElevenLabs bills differently for SSML tags
- OpenAI counts differently

**Recommendation**: Rename and clarify:

```python
@dataclass
class AudioResult:
    input_characters: int = 0
    billed_characters: Optional[int] = None  # Provider-reported billing
```

---

### 15. No Lifecycle Methods

**The Problem**: No way to:
- Initialize client connections
- Close/cleanup resources
- Check health/connectivity

**Recommendation**: Add optional lifecycle methods:

```python
class TTSPort(ABC):
    def close(self) -> None:
        """Release resources. Optional."""
        pass

    def __enter__(self) -> "TTSPort":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def health_check(self) -> bool:
        """Check if provider is accessible. Optional."""
        return True
```

---

## Edge Cases Not Handled

### E1. Voice ID Changes
- Provider changes voice ID format
- Voice gets deprecated/removed
- Custom voice expires

### E2. Concurrent Requests
- Same text synthesized simultaneously
- Race conditions with caching
- Connection pool exhaustion

### E3. Network Failures Mid-Stream
- What happens if connection drops during streaming?
- Partial audio recovery?

### E4. Character Encoding
- Unicode normalization (NFC vs NFD)
- Emoji handling (some providers strip them)
- RTL text (Arabic, Hebrew)

### E5. SSML + Audio Tags Conflict
- User provides SSML with ElevenLabs audio tags
- Which takes precedence?

---

## Enhancement Opportunities

### EO1. Batch Synthesis API
For synthesizing multiple texts efficiently:

```python
def synthesize_batch(
    self,
    items: list[tuple[str, VoiceConfig]],
    output_format: AudioFormat = AudioFormat.MP3,
) -> list[AudioResult]:
    """Synthesize multiple texts. Default implementation calls synthesize() in loop."""
    return [self.synthesize(text, config, output_format=output_format)
            for text, config in items]
```

### EO2. Voice Similarity Search
For finding similar voices across providers:

```python
def find_similar_voices(
    self,
    reference_voice_id: str,
    target_provider: Optional[str] = None,
) -> list[VoiceInfo]:
    pass
```

### EO3. Cost Estimation
Before synthesis:

```python
def estimate_cost(self, text: str, model: Optional[str] = None) -> float:
    """Estimate cost in USD for synthesizing this text."""
    pass
```

### EO4. Word-Level Timestamps
For alignment/captioning:

```python
@dataclass
class WordTimestamp:
    word: str
    start_ms: int
    end_ms: int

@dataclass
class AudioResult:
    # ... existing ...
    word_timestamps: Optional[list[WordTimestamp]] = None
```

---

## Consistency Issues

| Issue | Location | Problem |
|-------|----------|---------|
| Abstract vs default | `supports_style_prompt` | Has default `False` unlike other `supports_*` |
| Return type | `get_voice()` | Returns `Optional[VoiceInfo]` but `list_voices()` returns `list` |
| Method naming | `synthesize` vs `stream` | Verbs are inconsistent (one is action, one is noun-like) |
| Parameter order | All methods | `text, config` but could argue `config, text` for currying |

---

## Security Considerations

### API Key Handling
The spec shows API keys passed to constructors:

```python
tts = ElevenLabsTTSAdapter(api_key="your-api-key")
```

**Concerns**:
- Keys in code/logs
- No mention of secure storage
- No key rotation support

**Recommendation**: Document best practices:
```python
# Good: Environment variable
tts = ElevenLabsTTSAdapter(api_key=os.environ["ELEVENLABS_API_KEY"])

# Good: Secrets manager
from chatforge.security import get_secret
tts = ElevenLabsTTSAdapter(api_key=get_secret("elevenlabs"))
```

---

## Summary of Recommendations

### Must Fix Before Implementation
1. Define exception hierarchy
2. Add async variants or make async primary
3. Fix streaming default implementation
4. Address text length limits

### Should Fix
5. Consider VoiceConfig inheritance or extras pattern
6. Add AudioConfig for format specification
7. Clarify preprocess_text semantics
8. Add lifecycle methods (close, context manager)

### Nice to Have
9. Batch synthesis API
10. Cost estimation
11. Caching interface
12. Enhanced VoiceInfo metadata

---

## Conclusion

The TTSPort design is a good starting point but needs hardening before production use. The critical issues around error handling, async support, and streaming semantics must be addressed. The VoiceConfig god object is the biggest architectural smell and should be reconsidered.

Estimated effort to address all issues: **Medium** (1-2 weeks of focused work)

Priority order:
1. Error handling contract (Critical for reliability)
2. Async support (Critical for modern Python apps)
3. Text length limits (Critical for production use)
4. Streaming semantics (Critical for long-form audio)
5. Everything else (Important but not blocking)
