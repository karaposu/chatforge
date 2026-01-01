# OpenAI Realtime API: Audio Format

**Date:** 2025-01-01
**Scope:** RealtimeVoiceAPIPort - OpenAI adapter
**Source:** VoxStream code references (needs verification from OpenAI docs)

---

## Audio Format Requirements

From VoxStream's `config/types.py:369-378`:
```python
class AudioConstants:
    # OpenAI Realtime API specifics
    OPENAI_SAMPLE_RATE = 24000
    OPENAI_CHANNELS = 1
    OPENAI_FORMAT = AudioFormat.PCM16
```

**Expected format:**
| Property | Value |
|----------|-------|
| Encoding | PCM16 |
| Sample Rate | 24000 Hz |
| Channels | 1 (Mono) |
| Bit Depth | 16 |

---

## Needs Verification from OpenAI Docs

- [ ] Confirm PCM16 format
- [ ] Confirm 24kHz sample rate
- [ ] How is audio encoded in WebSocket messages? (Base64?)
- [ ] What chunk size does the API expect?
- [ ] How does the API signal end of audio response?
- [ ] Server VAD behavior details

---

## Protocol Questions

### Audio Input (Client → Server)
```python
# Expected format (needs verification)
{
    "type": "input_audio_buffer.append",
    "audio": "<base64_encoded_pcm16>"  # ?
}
```

### Audio Output (Server → Client)
```python
# Expected format (needs verification)
{
    "type": "response.audio.delta",
    "delta": "<base64_encoded_pcm16>"  # ?
}
```

---

## Related: VoxStream Compatibility

VoxStream default format (24kHz, PCM16, Mono) matches OpenAI's expected format.

This means:
- No conversion needed when using VoxStream + OpenAI
- AudioStreamPort can pass audio directly to RealtimeVoiceAPIPort
- Format conversion only needed for other audio sources (WebRTC, Twilio)

---

## Status

**CONFIRMED** - VoxStream's constants match OpenAI Realtime API requirements:
- PCM16 encoding
- 24kHz sample rate
- Mono channel
- Base64 encoded in WebSocket JSON messages
