# TTS Integration Plan: Chatforge → ChamberProtocolAI

## Executive Summary

**Question:** Can chatforge's TTSService replace the ElevenLabs implementation in ChamberProtocolAI?

**Answer:** Yes, but with considerations. The TTSService provides a cleaner abstraction, but ChamberProtocolAI uses some ElevenLabs-specific features that require using the adapter layer, not just the service layer.

---

## Current ChamberProtocolAI Implementation

### Architecture
```
elevenlabs_api.py (FastAPI endpoint)
        ↓
elevenlabs_tts.py (utility function)
        ↓
ElevenLabs SDK (sync client)
```

### Key Features Used
| Feature | Value | Notes |
|---------|-------|-------|
| Default voice | `JBFqnCBsd6RMkjVDRZzb` (Silüet) | Project-specific voice |
| Default model | `eleven_v3` | Latest model |
| Voice settings | stability, similarity_boost, style, use_speaker_boost | Full control |
| Output format | Direct string `mp3_44100_128` | Not abstracted |
| v3 normalization | Snaps stability to 0.0/0.5/1.0 | Model-specific logic |
| Response | Base64 encoded audio | For Unity client |

### Current Code Flow
```python
# 1. API receives request with voice_settings
request.voice_settings = {stability: 0.7, similarity_boost: 0.8, ...}

# 2. v3 stability normalization
if model_id.startswith("eleven_v3"):
    stability = snap_to_nearest([0.0, 0.5, 1.0])

# 3. Direct ElevenLabs SDK call
client.text_to_speech.convert(
    text=text,
    voice_id=voice_id,
    model_id=model_id,
    output_format="mp3_44100_128",  # Direct format string
    voice_settings=settings
)

# 4. Base64 encode for Unity
audio_base64 = base64.b64encode(audio_bytes)
```

---

## Chatforge TTSService Analysis

### Architecture
```
TTSService (high-level)
     ↓
TTSPort (interface)
     ↓
ElevenLabsTTSAdapter (implementation)
     ↓
AsyncElevenLabs SDK (async client)
```

### What TTSService Provides
| Feature | Implementation | Notes |
|---------|---------------|-------|
| Provider abstraction | `TTSService("elevenlabs")` | Can swap to OpenAI |
| Simple quality API | `quality="standard"` | Maps to format internally |
| Async-first | Uses `AsyncElevenLabs` | Better for FastAPI |
| Streaming | `async for chunk in tts.stream()` | Built-in |
| Error handling | Typed exceptions | Clean error mapping |

### What TTSService Doesn't Expose Directly
| Feature | Gap | Solution |
|---------|-----|----------|
| Direct format string | Uses quality enum | Use adapter directly |
| Voice settings | Abstracted away | Use `ElevenLabsVoiceConfig` |
| v3 normalization | Not implemented | Add to adapter or API layer |
| Model selection | Limited | Pass `model` parameter |

---

## Comparison Matrix

| Aspect | ChamberProtocol | TTSService | ElevenLabsTTSAdapter |
|--------|-----------------|------------|---------------------|
| Voice settings control | ✅ Full | ❌ Limited | ✅ Full |
| Direct format string | ✅ Yes | ❌ No (quality-based) | ⚠️ Via format mapping |
| v3 stability snap | ✅ Yes | ❌ No | ❌ No |
| Async support | ❌ Sync | ✅ Async | ✅ Async |
| Provider swapping | ❌ No | ✅ Yes | ❌ No |
| Error typing | ⚠️ String matching | ✅ Typed exceptions | ✅ Typed exceptions |
| Base64 output | ✅ Yes | ❌ No (bytes) | ❌ No (bytes) |

---

## Integration Options

### Option 1: Use TTSService (Simplest, Limited)
**When:** You want provider flexibility and don't need fine voice control.

```python
from chatforge.services import TTSService

@router.post("/elevenlabs/tts")
async def text_to_speech(request: ElevenLabsTTSRequest):
    async with TTSService("elevenlabs") as tts:
        result = await tts.generate(
            request.text,
            voice_id=request.voice_id,
            quality="standard",
        )
        return ElevenLabsTTSResponse(
            audio_base64=base64.b64encode(result.audio_bytes).decode(),
            format="mp3",
            text_length=len(request.text)
        )
```

**Pros:**
- Simplest code
- Can swap to OpenAI easily
- Async-first

**Cons:**
- Loses voice_settings control (stability, similarity_boost)
- No v3 model normalization
- Quality-based format, not direct string

---

### Option 2: Use ElevenLabsTTSAdapter (Full Control)
**When:** You need all ElevenLabs-specific features.

```python
from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality

@router.post("/elevenlabs/tts")
async def text_to_speech(request: ElevenLabsTTSRequest):
    async with ElevenLabsTTSAdapter() as tts:
        config = ElevenLabsVoiceConfig(
            voice_id=request.voice_id,
            stability=normalize_v3_stability(request.voice_settings.stability),
            similarity_boost=request.voice_settings.similarity_boost,
            style_exaggeration=request.voice_settings.style,
            use_speaker_boost=request.voice_settings.use_speaker_boost,
        )

        result = await tts.synthesize(
            request.text,
            config,
            output_format=AudioFormat.MP3,
            quality=AudioQuality.STANDARD,
            model=request.model_id,
        )

        return ElevenLabsTTSResponse(
            audio_base64=base64.b64encode(result.audio_bytes).decode(),
            format=request.output_format,
            text_length=result.input_characters
        )

def normalize_v3_stability(stability: float) -> float:
    """Snap to v3 allowed values."""
    allowed = [0.0, 0.5, 1.0]
    return min(allowed, key=lambda x: abs(x - stability))
```

**Pros:**
- Full voice settings control
- Proper async
- Typed errors
- Can add v3 normalization in API layer

**Cons:**
- Tied to ElevenLabs (no provider swapping)
- More code than current implementation

---

### Option 3: Extend TTSService for ChamberProtocol (Recommended)
**When:** You want the best of both worlds.

Create a thin extension that adds ChamberProtocol-specific needs:

```python
# In ChamberProtocolAI: src/services/tts_service.py

from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig
from chatforge.ports.tts import AudioFormat, AudioQuality
import base64

class ChamberTTSService:
    """TTS service with ChamberProtocol-specific defaults and features."""

    DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"  # Silüet
    DEFAULT_MODEL = "eleven_v3"

    def __init__(self):
        self._adapter = ElevenLabsTTSAdapter()

    async def __aenter__(self):
        await self._adapter.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self._adapter.__aexit__(*args)

    async def generate(
        self,
        text: str,
        voice_id: str = None,
        model_id: str = None,
        voice_settings: dict = None,
        output_format: str = "mp3_44100_128",
    ) -> tuple[str, int]:  # Returns (base64_audio, text_length)
        """Generate TTS with ChamberProtocol defaults."""

        voice_id = voice_id or self.DEFAULT_VOICE
        model_id = model_id or self.DEFAULT_MODEL

        # Build config with v3 normalization
        config = self._build_config(voice_id, model_id, voice_settings)

        # Map format string to chatforge types
        audio_format, quality = self._parse_format(output_format)

        result = await self._adapter.synthesize(
            text=text,
            config=config,
            output_format=audio_format,
            quality=quality,
            model=model_id,
        )

        # Return base64 for Unity
        audio_base64 = base64.b64encode(result.audio_bytes).decode()
        return audio_base64, result.input_characters

    def _build_config(self, voice_id: str, model_id: str, settings: dict) -> ElevenLabsVoiceConfig:
        """Build config with v3 stability normalization."""
        if not settings:
            return ElevenLabsVoiceConfig(voice_id=voice_id)

        stability = settings.get("stability", 0.5)

        # v3 stability normalization
        if model_id.startswith("eleven_v3"):
            stability = min([0.0, 0.5, 1.0], key=lambda x: abs(x - stability))

        return ElevenLabsVoiceConfig(
            voice_id=voice_id,
            stability=stability,
            similarity_boost=settings.get("similarity_boost", 0.75),
            style_exaggeration=settings.get("style", 0.0),
            use_speaker_boost=settings.get("use_speaker_boost", True),
        )

    def _parse_format(self, format_str: str) -> tuple[AudioFormat, AudioQuality]:
        """Parse format string like 'mp3_44100_128' to chatforge types."""
        if "mp3" in format_str:
            fmt = AudioFormat.MP3
        elif "wav" in format_str:
            fmt = AudioFormat.WAV
        else:
            fmt = AudioFormat.MP3

        if "192" in format_str or "44100" in format_str:
            quality = AudioQuality.HIGH
        elif "128" in format_str:
            quality = AudioQuality.STANDARD
        else:
            quality = AudioQuality.LOW

        return fmt, quality
```

**Usage in API:**
```python
from services.tts_service import ChamberTTSService

@router.post("/elevenlabs/tts")
async def text_to_speech(request: ElevenLabsTTSRequest):
    async with ChamberTTSService() as tts:
        audio_base64, text_length = await tts.generate(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id,
            voice_settings=request.voice_settings.dict() if request.voice_settings else None,
            output_format=request.output_format,
        )

        return ElevenLabsTTSResponse(
            audio_base64=audio_base64,
            format=request.output_format,
            text_length=text_length
        )
```

**Pros:**
- Uses chatforge's robust ElevenLabs adapter (async, proper errors)
- Preserves ChamberProtocol-specific logic (v3 normalization, defaults)
- Clean separation of concerns
- Easy to extend for future needs

**Cons:**
- Slightly more code upfront
- Tied to ElevenLabs (but that's intentional for this API)

---

## Recommendation

**Use Option 3: Extend with ChamberTTSService**

Rationale:
1. **Preserves existing behavior** - Same defaults, v3 normalization, base64 output
2. **Gets chatforge benefits** - Async client, typed errors, tested adapter
3. **Clean architecture** - Service layer in ChamberProtocol wraps chatforge adapter
4. **Future-ready** - Can add more providers or features without changing API

---

## Migration Steps

1. **Add chatforge dependency** to ChamberProtocolAI
   ```bash
   pip install chatforge[tts-elevenlabs]
   ```

2. **Create `src/services/tts_service.py`** with ChamberTTSService

3. **Update `elevenlabs_api.py`** to use ChamberTTSService

4. **Delete `utils/elevenlabs_tts.py`** (replaced by chatforge adapter)

5. **Test** with existing Unity client

---

## What Chatforge Could Add (Future)

To make TTSService more directly usable:

1. **Voice settings passthrough** - Allow passing provider-specific settings
   ```python
   await tts.generate("Hello", voice_settings={"stability": 0.3})
   ```

2. **Format string support** - Accept direct format strings
   ```python
   await tts.generate("Hello", output_format="mp3_44100_128")
   ```

3. **Model normalization hooks** - Allow adapters to normalize settings per model

These would make Option 1 viable for more use cases.
