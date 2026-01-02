# TTSService Usage Plan for ChamberProtocolAI

How to switch ChamberProtocolAI's ElevenLabs TTS endpoint to use chatforge's TTSService.

---

## Current Implementation (ChamberProtocolAI)

**Files:**
- `apis/elevenlabs_api.py` - FastAPI endpoint
- `utils/elevenlabs_tts.py` - Utility function
- `models/elevenlabs_request.py` - Request model
- `models/elevenlabs_response.py` - Response model

**Issues:**
- **Sync `ElevenLabs` client in async context** - Uses blocking sync client in async FastAPI endpoints (should use `AsyncElevenLabs`)
- String-based error handling
- Separate utility file to maintain
- Contains unnecessary v3 stability normalization code (see note below)

---

## New Implementation

### Why This Matters: Async vs Sync Client

**ChamberProtocolAI currently uses the sync client incorrectly:**

```python
# utils/elevenlabs_tts.py - WRONG APPROACH
from elevenlabs import ElevenLabs  # ❌ Sync client

eleven = ElevenLabs(api_key=api_key)

# Called from async FastAPI endpoint - blocks the event loop!
audio = eleven.text_to_speech.convert(...)  # ❌ No await, blocking call
```

**Chatforge uses the async client properly:**

```python
# chatforge/adapters/tts/elevenlabs.py - CORRECT APPROACH
from elevenlabs import AsyncElevenLabs  # ✅ Async client

self._client = AsyncElevenLabs(api_key=self._api_key)

# Properly awaitable
audio_stream = await self._client.text_to_speech.convert(...)  # ✅ Non-blocking
```

**Impact:**
- Sync client blocks the entire FastAPI event loop
- Other requests can't be processed while waiting for TTS
- Async client allows FastAPI to handle multiple requests concurrently

---

### Step 1: Install chatforge locally

```bash
cd /path/to/chatforge
pip install -e .
```

### Step 2: Replace elevenlabs_api.py

**Before (ChamberProtocolAI - sync client):**
```python
# utils/elevenlabs_tts.py
from elevenlabs import ElevenLabs  # ❌ Sync

def generate_audio(text: str, voice_id: str, ...) -> bytes:
    eleven = ElevenLabs(api_key=api_key)
    audio = eleven.text_to_speech.convert(...)  # ❌ Blocks
    return audio

# apis/elevenlabs_api.py
async def text_to_speech(request: ElevenLabsTTSRequest):
    audio = generate_audio(...)  # ❌ Calling sync from async
```

**After (Chatforge - async client):**

```python
from fastapi import APIRouter, HTTPException
import base64

from models.elevenlabs_request import ElevenLabsTTSRequest
from models.elevenlabs_response import ElevenLabsTTSResponse

from chatforge.services import TTSService  # ✅ Uses AsyncElevenLabs internally
from chatforge.ports.tts import VoiceConfig
from chatforge.ports.tts import (
    TTSRateLimitError,
    TTSQuotaExceededError,
    TTSInvalidVoiceError,
    TTSAuthenticationError,
    TTSError,
)

router = APIRouter()


@router.post(
    "/elevenlabs/tts",
    response_model=ElevenLabsTTSResponse,
    tags=["elevenlabs"],
    summary="Convert text to speech using ElevenLabs",
)
async def text_to_speech(request: ElevenLabsTTSRequest):
    """
    Convert text to speech using ElevenLabs API.
    Returns base64 encoded audio for Unity clients.
    """
    # All settings in VoiceConfig
    config = VoiceConfig(
        voice_id=request.voice_id,
        stability=request.voice_settings.stability if request.voice_settings else 0.5,
        quality="standard",  # mp3_44100_128
    )

    try:
        async with TTSService("elevenlabs") as tts:  # ✅ Proper async context manager
            result = await tts.generate(request.text, config, model=request.model_id)  # ✅ Properly awaited

        return ElevenLabsTTSResponse(
            audio_base64=base64.b64encode(result.audio_bytes).decode('utf-8'),
            format=request.output_format,
            text_length=len(request.text),
        )

    except TTSAuthenticationError:
        raise HTTPException(status_code=503, detail="ElevenLabs API key not configured")

    except TTSRateLimitError:
        raise HTTPException(status_code=429, detail="ElevenLabs rate limit exceeded")

    except TTSQuotaExceededError:
        raise HTTPException(status_code=402, detail="ElevenLabs quota exceeded")

    except TTSInvalidVoiceError:
        raise HTTPException(status_code=400, detail=f"Invalid voice ID: {request.voice_id}")

    except TTSError as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")
```

### Step 3: Delete utils/elevenlabs_tts.py

No longer needed.


---

## VoiceConfig Fields

```python
@dataclass
class VoiceConfig:
    voice_id: str
    language_code: str = "en-US"
    speed: float = 1.0
    stability: float = 0.5      # 0.0 (expressive) - 1.0 (consistent)
    quality: str = "standard"   # "low", "standard", "high"
```

---

## Quality Mapping

| VoiceConfig.quality | ElevenLabs format |
|---------------------|-------------------|
| `"low"` | `mp3_22050_32` |
| `"standard"` | `mp3_44100_128` |
| `"high"` | `mp3_44100_192` |

ChamberProtocolAI uses `mp3_44100_128` → `quality="standard"`

---

## What Changes

| Aspect | Before (ChamberProtocolAI) | After (Chatforge) |
|--------|---------------------------|-------------------|
| Client | Sync `ElevenLabs` (❌ blocks event loop) | Async `AsyncElevenLabs` (✅ non-blocking) |
| API calls | `audio = client.convert(...)` (no await) | `audio = await client.convert(...)` (proper async) |
| Error handling | String matching | Typed exceptions (`TTSRateLimitError`, etc.) |
| Config | Dict + separate params | `VoiceConfig` dataclass |
| Files | 2 (api + util) | 1 (api only) |
| Stability normalization | Unnecessary snapping to 0.0/0.5/1.0 | Direct passthrough (correct) |

---

## What Stays the Same

| Aspect | Value |
|--------|-------|
| Endpoint | `POST /elevenlabs/tts` |
| Request model | `ElevenLabsTTSRequest` |
| Response model | `ElevenLabsTTSResponse` |
| Default voice | `JBFqnCBsd6RMkjVDRZzb` (Silüet) |
| Default model | `eleven_v3` |
| Response format | Base64 encoded audio |

---

## Voice Settings

| ChamberProtocolAI | Chatforge | Status |
|-------------------|-----------|--------|
| `stability` | `VoiceConfig.stability` | Supported |
| `similarity_boost` | ElevenLabs default | Trusting API default |
| `style` | ElevenLabs default | Trusting API default |
| `use_speaker_boost` | ElevenLabs default | Trusting API default |

For stock voices like Silüet, ElevenLabs defaults work fine.

---


---

## Benefits

1. **True async (CRITICAL)** - Uses `AsyncElevenLabs` properly with `await`, doesn't block FastAPI event loop
   - Current code blocks all other requests while waiting for TTS
   - Chatforge allows concurrent request handling
2. **Typed errors** - No string matching, proper exception hierarchy
3. **Clean config** - Everything in `VoiceConfig` dataclass
4. **Less code** - Delete utility file (including unnecessary normalization code)
5. **Provider flexibility** - Can switch to OpenAI TTS with one line change
6. **Correct behavior** - No unnecessary stability value manipulation
7. **Better maintainability** - One less file to maintain, cleaner architecture

---

## Migration Checklist

- [ ] Install chatforge: `pip install -e /path/to/chatforge`
- [ ] Update `apis/elevenlabs_api.py`
- [ ] Delete `utils/elevenlabs_tts.py` (removes unnecessary normalization code)
- [ ] Test endpoint with various stability values (0.0 to 1.0)
- [ ] Test from Unity client

---


