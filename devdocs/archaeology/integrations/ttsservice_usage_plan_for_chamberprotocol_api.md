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
- Sync `ElevenLabs` client in async context
- String-based error handling
- Separate utility file to maintain

---

## New Implementation

### Step 1: Install chatforge locally

```bash
cd /path/to/chatforge
pip install -e .
```

### Step 2: Replace elevenlabs_api.py

```python
from fastapi import APIRouter, HTTPException
import base64

from models.elevenlabs_request import ElevenLabsTTSRequest
from models.elevenlabs_response import ElevenLabsTTSResponse

from chatforge.services import TTSService
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
        async with TTSService("elevenlabs") as tts:
            result = await tts.generate(request.text, config, model=request.model_id)

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

| Aspect | Before | After |
|--------|--------|-------|
| Client | Sync `ElevenLabs` | Async `AsyncElevenLabs` |
| Error handling | String matching | Typed exceptions |
| Config | Dict + separate params | `VoiceConfig` dataclass |
| Files | 2 (api + util) | 1 (api only) |

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

## Testing

```bash
curl -X POST http://localhost:8188/elevenlabs/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from Silüet, testing chatforge integration.",
    "voice_id": "JBFqnCBsd6RMkjVDRZzb"
  }'
```

---

## Benefits

1. **True async** - Native async with `AsyncElevenLabs`
2. **Typed errors** - No string matching
3. **Clean config** - Everything in `VoiceConfig`
4. **Less code** - Delete utility file
5. **Provider flexibility** - Can switch to OpenAI TTS easily

---

## Migration Checklist

- [ ] Install chatforge: `pip install -e /path/to/chatforge`
- [ ] Update `apis/elevenlabs_api.py`
- [ ] Delete `utils/elevenlabs_tts.py`
- [ ] Test endpoint
- [ ] Test from Unity client
