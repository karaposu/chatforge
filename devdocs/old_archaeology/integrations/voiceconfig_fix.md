# VoiceConfig Refactoring Summary

Discussion and changes made to VoiceConfig and TTSService.

---

## The Problem

`TTSService.generate()` had a simplified API that didn't expose voice settings like `stability`:

```python
# Old TTSService - no way to customize stability
result = await tts.generate(text, voice_id="...")  # Stuck with defaults
```

Meanwhile, using adapters directly allowed full control via `VoiceConfig`:

```python
# Adapter - full control
config = VoiceConfig(voice_id="...", stability=0.3)
result = await tts.synthesize(text, config)
```

---

## What is Stability?

Controls how consistent vs. expressive the voice output is:

| Value | Effect |
|-------|--------|
| **Low (0.0-0.3)** | More expressive, emotional, varied |
| **Mid (0.5)** | Balanced, natural |
| **High (0.8-1.0)** | Consistent, predictable |

---

## What About similarity_boost?

`similarity_boost` controls how closely output matches the original voice sample.

**Decision:** Keep it in `ElevenLabsVoiceConfig` only, not in base `VoiceConfig`.

**Reason:** It's mainly relevant for cloned voices, not standard TTS with stock voices. Most users don't need it.

---

## Changes Made

### 1. Added `stability` to base VoiceConfig

**File:** `chatforge/ports/tts.py`

```python
@dataclass
class VoiceConfig:
    voice_id: str
    language_code: str = "en-US"
    speed: float = 1.0
    stability: float = 0.5  # NEW - 0.0 (expressive) to 1.0 (consistent)
```

### 2. Updated ElevenLabsTTSAdapter

**File:** `chatforge/adapters/tts/elevenlabs.py`

Now reads `stability` from base `VoiceConfig`:

```python
# Always use stability from base config
voice_settings = {
    "stability": config.stability,
}
# Add ElevenLabs-specific settings only if using ElevenLabsVoiceConfig
if isinstance(config, ElevenLabsVoiceConfig):
    voice_settings.update({
        "similarity_boost": config.similarity_boost,
        "style": config.style_exaggeration,
        "use_speaker_boost": config.use_speaker_boost,
    })
```

### 3. Changed default model to eleven_v3

**File:** `chatforge/adapters/tts/elevenlabs.py`

```python
# Old
model_id=model or "eleven_multilingual_v2"

# New
model_id=model or "eleven_v3"
```

---

## Pending Change: TTSService Should Accept VoiceConfig

### Current (redundant)

```python
async def generate(
    self,
    text: str,
    *,
    voice_id: str | None = None,  # Redundant - already in VoiceConfig
    quality: ...,
    output_format: ...,
)
```

### Proposed (clean)

```python
async def generate(
    self,
    text: str,
    config: VoiceConfig,  # All voice settings here
    *,
    quality: ...,         # Synthesis settings stay
    output_format: ...,
)
```

### Why?

1. **Consistency** - Same pattern as adapter
2. **Full control** - Users can customize stability, speed, etc.
3. **No redundancy** - VoiceConfig already has voice_id
4. **Future-proof** - New VoiceConfig fields automatically available

### Clean Separation

| Parameter | Contains |
|-----------|----------|
| `VoiceConfig` | Voice settings (voice_id, stability, speed) |
| `quality`, `output_format`, `model` | Synthesis/output settings |

---

## Usage After Changes

```python
from chatforge.services import TTSService
from chatforge.ports.tts import VoiceConfig

# Simple usage with defaults
config = VoiceConfig(voice_id="JBFqnCBsd6RMkjVDRZzb")

# Custom stability and quality
config = VoiceConfig(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    stability=0.3,  # More expressive
    quality="high",  # Audio quality
)

async with TTSService("elevenlabs") as tts:
    result = await tts.generate("Hello!", config)
```

---

## Status

- [x] Add `stability` to base `VoiceConfig`
- [x] Update `ElevenLabsTTSAdapter` to use `config.stability`
- [x] Change default model to `eleven_v3`
- [x] Update `TTSService.generate()` to accept `VoiceConfig` instead of `voice_id`
- [x] Update `TTSService.stream()` to accept `VoiceConfig` instead of `voice_id`
