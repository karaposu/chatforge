# ElevenLabs v3 Stability Normalization

Documentation of the stability normalization requirement for ElevenLabs eleven_v3 models.

---

## The Problem

ElevenLabs' **eleven_v3** model family only accepts **three specific stability values**:

| Value | Mode | Description |
|-------|------|-------------|
| `0.0` | Creative | More expressive, variable output |
| `0.5` | Natural | Balanced (default) |
| `1.0` | Robust | Consistent, stable output |

If you send any other value (like `0.3` or `0.75`), the API may:
- Reject the request
- Round to an unexpected value
- Behave unpredictably

This is **different from older models** (like `eleven_multilingual_v2`) which accept any float between 0.0 and 1.0.

---

## Current State

### ChamberProtocolAI - Has the Fix

Location: `/Users/air/Desktop/ns/ChamberProtocolAI/src/utils/elevenlabs_tts.py`

```python
# Normalize voice settings for v3 models
if voice_settings and model_id.startswith("eleven_v3"):
    # v3 stability must be one of: 0.0 (Creative), 0.5 (Natural), 1.0 (Robust)
    if "stability" in voice_settings:
        allowed_values = [0.0, 0.5, 1.0]
        current = float(voice_settings["stability"])
        voice_settings["stability"] = min(allowed_values, key=lambda x: abs(x - current))
```

**Snapping behavior:**
- `0.00 - 0.24` → `0.0` (Creative)
- `0.25 - 0.74` → `0.5` (Natural)
- `0.75 - 1.00` → `1.0` (Robust)

### Chatforge - Missing the Fix

Location: `chatforge/adapters/tts/elevenlabs.py`

The `synthesize()` and `stream()` methods pass stability values directly without normalization:

```python
voice_settings = None
if isinstance(config, ElevenLabsVoiceConfig):
    voice_settings = {
        "stability": config.stability,  # Passed as-is, no v3 check
        "similarity_boost": config.similarity_boost,
        "style": config.style_exaggeration,
        "use_speaker_boost": config.use_speaker_boost,
    }
```

---

## Impact

| Scenario | Result |
|----------|--------|
| Using `eleven_multilingual_v2` (default) | Works fine, any stability value accepted |
| Using `eleven_v3` with `stability=0.5` | Works fine |
| Using `eleven_v3` with `stability=0.3` | May fail or behave unexpectedly |

Since Chatforge defaults to `eleven_multilingual_v2`, most users won't encounter this issue. However, if someone explicitly uses `eleven_v3`:

```python
result = await tts.synthesize(
    "Hello",
    config,
    model="eleven_v3"  # Using v3 model
)
```

And their config has `stability=0.3`, it could fail.

---

## Proposed Fix for Chatforge

### 1. Add Helper Method

Add to `ElevenLabsTTSAdapter` class in `chatforge/adapters/tts/elevenlabs.py`:

```python
def _normalize_voice_settings_for_model(
    self,
    voice_settings: Optional[dict],
    model_id: str,
) -> Optional[dict]:
    """
    Normalize voice settings for specific model requirements.

    ElevenLabs v3 models only accept stability values of 0.0, 0.5, or 1.0.
    This snaps any stability value to the nearest allowed value.

    Args:
        voice_settings: Voice settings dict or None
        model_id: ElevenLabs model ID

    Returns:
        Normalized voice settings dict
    """
    if not voice_settings:
        return voice_settings

    # v3 models require stability in [0.0, 0.5, 1.0]
    if model_id and model_id.startswith("eleven_v3"):
        if "stability" in voice_settings:
            allowed_values = [0.0, 0.5, 1.0]
            current = float(voice_settings["stability"])
            voice_settings["stability"] = min(
                allowed_values,
                key=lambda x: abs(x - current)
            )

    return voice_settings
```

### 2. Modify synthesize() Method

After building voice_settings (around line 207), add:

```python
# Build voice settings
voice_settings = None
if isinstance(config, ElevenLabsVoiceConfig):
    voice_settings = {
        "stability": config.stability,
        "similarity_boost": config.similarity_boost,
        "style": config.style_exaggeration,
        "use_speaker_boost": config.use_speaker_boost,
    }

# Normalize for v3 models
voice_settings = self._normalize_voice_settings_for_model(
    voice_settings,
    model or "eleven_multilingual_v2"
)
```

### 3. Modify stream() Method

Same change after building voice_settings (around line 272):

```python
voice_settings = None
if isinstance(config, ElevenLabsVoiceConfig):
    voice_settings = {
        "stability": config.stability,
        "similarity_boost": config.similarity_boost,
    }

# Normalize for v3 models
voice_settings = self._normalize_voice_settings_for_model(
    voice_settings,
    model or "eleven_multilingual_v2"
)
```

---

## Testing

After implementing, test with:

```python
import pytest
from chatforge.adapters.tts.elevenlabs import ElevenLabsTTSAdapter

class TestV3StabilityNormalization:

    def test_v3_stability_snaps_to_creative(self):
        adapter = ElevenLabsTTSAdapter(api_key="test")
        settings = {"stability": 0.1}
        result = adapter._normalize_voice_settings_for_model(settings, "eleven_v3")
        assert result["stability"] == 0.0

    def test_v3_stability_snaps_to_natural(self):
        adapter = ElevenLabsTTSAdapter(api_key="test")
        settings = {"stability": 0.4}
        result = adapter._normalize_voice_settings_for_model(settings, "eleven_v3")
        assert result["stability"] == 0.5

    def test_v3_stability_snaps_to_robust(self):
        adapter = ElevenLabsTTSAdapter(api_key="test")
        settings = {"stability": 0.9}
        result = adapter._normalize_voice_settings_for_model(settings, "eleven_v3")
        assert result["stability"] == 1.0

    def test_v2_stability_unchanged(self):
        adapter = ElevenLabsTTSAdapter(api_key="test")
        settings = {"stability": 0.3}
        result = adapter._normalize_voice_settings_for_model(settings, "eleven_multilingual_v2")
        assert result["stability"] == 0.3  # Unchanged

    def test_none_settings_returns_none(self):
        adapter = ElevenLabsTTSAdapter(api_key="test")
        result = adapter._normalize_voice_settings_for_model(None, "eleven_v3")
        assert result is None
```

---

## Related Files

| File | Description |
|------|-------------|
| `chatforge/adapters/tts/elevenlabs.py` | ElevenLabs adapter (needs fix) |
| `chatforge/ports/tts.py` | TTS port interface |
| `ChamberProtocolAI/src/utils/elevenlabs_tts.py` | Reference implementation with fix |

---

## References

- ElevenLabs v3 model documentation
- ChamberProtocolAI implementation (discovered 2024-12)

---

## Status

- [ ] Add `_normalize_voice_settings_for_model()` helper
- [ ] Update `synthesize()` method
- [ ] Update `stream()` method
- [ ] Add unit tests
- [ ] Integration test with actual eleven_v3 model
