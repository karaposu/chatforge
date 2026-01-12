# Trace 10: TTS Port (Text-to-Speech)

Abstract interface for text-to-speech synthesis with multiple provider implementations.

---

## Entry Point

**File:** `chatforge/ports/tts.py:232`
**Interface:** `TTSPort` (Abstract Base Class)

**Implementations:**
- `chatforge/adapters/tts/openai.py` - OpenAI TTS
- `chatforge/adapters/tts/elevenlabs.py` - ElevenLabs TTS

**Primary Methods:**
```python
async def synthesize(text, config, output_format, quality, model) -> AudioResult
async def stream(text, config, output_format, quality, model) -> AsyncIterator[bytes]
async def list_voices(language_code=None) -> list[VoiceInfo]
```

**Callers:**
- Application voice pipelines
- TTS service wrappers
- Voice response handlers

---

## Execution Path: synthesize() (OpenAI)

```
synthesize(text, config, output_format, quality, model) -> AudioResult
    │
    ├─1─► Validate input
    │     │
    │     ├── _validate_input(text, config)
    │     │   └── Empty text → raise TTSInvalidInputError
    │     │
    │     └── _validate_text_length(text)
    │         └── len > max_text_length → raise TTSInvalidInputError
    │
    ├─2─► Preprocess text
    │     │
    │     └── _preprocess_text(text, config)
    │         └── Default: return as-is
    │         └── Subclass may: strip tags, normalize
    │
    ├─3─► Build API request
    │     │
    │     ├── model = model or "tts-1"
    │     ├── voice = config.voice_id
    │     ├── speed = config.speed
    │     └── response_format = map_format(output_format)
    │
    ├─4─► Call OpenAI API
    │     │
    │     └── response = await client.audio.speech.create(
    │             model=model,
    │             voice=voice,
    │             input=text,
    │             response_format=response_format,
    │             speed=speed,
    │         )
    │
    ├─5─► Handle errors
    │     │
    │     ├── AuthenticationError → TTSAuthenticationError
    │     ├── RateLimitError → TTSRateLimitError
    │     ├── BadRequestError → TTSInvalidVoiceError or TTSInvalidInputError
    │     └── APIError → TTSNetworkError
    │
    ├─6─► Read response
    │     │
    │     └── audio_bytes = response.content
    │
    └─7─► Return AudioResult
        │
        └── AudioResult(
                audio_bytes=audio_bytes,
                format=output_format,
                sample_rate=24000,  # OpenAI default
                input_characters=len(text),
            )
```

---

## Execution Path: stream() (ElevenLabs)

```
stream(text, config, output_format, quality, model) -> AsyncIterator[bytes]
    │
    ├─1─► Validate input
    │
    ├─2─► Build streaming request
    │     │
    │     ├── model_id = model or "eleven_monolingual_v1"
    │     ├── voice_id = config.voice_id
    │     └── settings = {stability, similarity_boost, ...}
    │
    ├─3─► Open streaming connection
    │     │
    │     └── async with client.text_to_speech.stream(
    │             voice_id=voice_id,
    │             text=text,
    │             model_id=model_id,
    │             voice_settings=settings,
    │         ) as stream:
    │
    └─4─► Yield chunks
        │
        └── async for chunk in stream:
                yield chunk
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| HTTP client | Constructor or context manager | close() or __aexit__ | Connection leak |
| API connection | Per-request | After response | Timeout |
| Response bytes | Buffer in memory | Return to caller | OOM for large audio |
| Stream connection | Per-stream | When generator exhausted | Hung stream |

**Context manager pattern:**
```python
async with OpenAITTSAdapter() as tts:
    result = await tts.synthesize(...)
# HTTP client closed automatically
```

---

## Error Path

```
TTSError hierarchy:
    │
    ├── TTSInvalidInputError
    │   ├── Empty text
    │   └── Text too long (max_text_length exceeded)
    │
    ├── TTSInvalidVoiceError
    │   └── Voice ID not found
    │
    ├── TTSAuthenticationError
    │   └── Invalid API key
    │
    ├── TTSRateLimitError
    │   └── Too many requests
    │   └── retry_after_seconds may be set
    │
    ├── TTSQuotaExceededError
    │   └── Credit limit reached
    │
    ├── TTSNetworkError
    │   └── Connection issues
    │
    └── TTSStreamingNotSupportedError
        └── Provider doesn't support streaming
```

---

## Performance Characteristics

| Metric | OpenAI | ElevenLabs | Notes |
|--------|--------|------------|-------|
| synthesize latency | 200-2000ms | 500-3000ms | Network + synthesis |
| First byte (stream) | 100-500ms | 200-800ms | Time to first chunk |
| Audio quality | Good | Excellent | Subjective |
| Cost per 1K chars | ~$0.015 | ~$0.03-0.30 | Varies by plan |

**Streaming benefit:**
- First audio plays sooner
- Memory: chunks vs full audio
- Better UX for long text

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| API request | External | synthesize/stream |
| Audio bytes in memory | Process | Response received |
| HTTP connection | Network | Per-request |

**No logging in port.** Adapters may log.

---

## Why This Design

**Unified interface:**
- Same API regardless of provider
- Easy to switch providers
- Test with mocks

**Streaming as core feature:**
- Modern TTS APIs support it
- Required for good UX
- AsyncIterator is natural fit

**VoiceConfig abstraction:**
- Provider-agnostic settings
- Adapters map to specific params
- Extensible via subclasses

**Exception hierarchy:**
- Specific error types
- Can catch broadly or narrowly
- Includes retry hints (rate limit)

---

## What Feels Incomplete

1. **No caching:**
   - Same text synthesized repeatedly
   - No result cache
   - Wastes money and time

2. **No SSML support in base:**
   - `supports_ssml` property exists
   - But no SSML helpers
   - Each adapter handles differently

3. **No chunking for long text:**
   - Exceeds max_text_length → error
   - Should auto-chunk
   - Concatenate results

4. **No word timestamps in all providers:**
   - AudioResult.word_timestamps defined
   - Not all providers support
   - No fallback

5. **No audio format conversion:**
   - Returns provider's format
   - Caller must convert
   - Should offer conversion option

---

## What Feels Vulnerable

1. **API keys in adapter:**
   - Stored for process lifetime
   - Could be logged
   - No rotation support

2. **Large text = large memory:**
   - Full audio bytes in memory
   - Long text = long audio
   - Could OOM

3. **No timeout on synthesis:**
   - Slow provider blocks forever
   - No cancellation
   - Should have timeout param

4. **Rate limit handling is caller's problem:**
   - Exception thrown
   - retry_after_seconds provided
   - But no built-in retry

---

## What Feels Bad Design

1. **quality param is string:**
   - "low", "standard", "high"
   - Could be enum (AudioQuality exists!)
   - Inconsistent with AudioQuality enum

2. **VoiceConfig has voice_id required:**
   - But some providers have default voice
   - Must always specify
   - Should allow None

3. **list_voices returns all, then filter:**
   - API may return hundreds
   - Filter in Python
   - Should filter server-side

4. **get_voice does linear search:**
   - Calls list_voices()
   - Iterates to find by ID
   - Should cache or direct lookup

5. **close() is optional:**
   - Can use without context manager
   - Easy to leak resources
   - Should enforce cleanup
