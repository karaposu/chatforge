# AudioStreamPort: Understanding Enrichment

**Date:** 2025-01-01
**Purpose:** Identify knowledge gaps and required confirmations before implementation

---

## Overview

Before implementing AudioStreamPort, we need to deeply understand:

1. **VoxStream library** - The primary adapter target
2. **Audio fundamentals** - Formats, sample rates, conversions
3. **Provider requirements** - What OpenAI Realtime API expects
4. **Platform differences** - Desktop vs Web vs Phone
5. **Edge cases** - Errors, permissions, device changes
6. **Use cases** - Real-world scenarios to support

---

## 1. VoxStream Library Investigation

### Questions to Answer

| Question | Why It Matters | How to Find Out |
|----------|----------------|-----------------|
| What is VoxStream's exact public API? | Our adapter wraps it | Read VoxStream source code |
| How does `start_capture_stream()` work? | Core capture method | Test with actual code |
| What type does capture return? `asyncio.Queue` or `AsyncGenerator`? | Affects our interface design | Read source + test |
| How does VAD callback registration work? | Need to expose VAD events | Read AudioManager code |
| What is the VAD state machine? | Understand speech detection flow | Read VADetector code |
| How does `play_audio()` vs `queue_playback()` differ? | Two playback modes | Test latency differences |
| What happens on `interrupt_playback()`? | Barge-in behavior | Test with actual audio |
| How does ProcessingMode affect latency? | REALTIME vs BALANCED vs QUALITY | Measure actual latency |
| What errors can VoxStream throw? | Error handling design | Read error handling code |
| How to list/select audio devices? | Device configuration | Read configure_devices() |

### Code to Inspect

```
voxstream/
├── voxstream.py              # Main facade - INSPECT THIS
├── config/
│   └── types.py              # ProcessingMode, StreamConfig - INSPECT THIS
├── audio/
│   ├── audio_manager.py      # Manages capture/playback - INSPECT THIS
│   ├── direct_capture.py     # Microphone capture - INSPECT THIS
│   ├── direct_player.py      # Immediate playback
│   ├── buffered_player.py    # Queued playback
│   └── vad.py                # Voice activity detection - INSPECT THIS
└── utils/
    └── metrics.py            # Audio levels, etc.
```

### Tests to Run

```python
# Test 1: Basic capture
from voxstream import VoxStream
vs = VoxStream()
queue = await vs.start_capture_stream()
# What type is queue? asyncio.Queue?
# What type are items in queue? bytes? numpy array?

# Test 2: VAD callbacks
# How do we register speech_start/speech_end callbacks?
# Does VoxStream expose this directly or through AudioManager?

# Test 3: Playback modes
vs.play_audio(chunk)       # Immediate - measure latency
vs.queue_playback(chunk)   # Buffered - measure latency
# What's the actual difference?

# Test 4: Interrupt behavior
vs.queue_playback(long_audio)
await asyncio.sleep(0.5)
vs.interrupt_playback()
# Does it stop immediately? Is there a fade out?
```

---

## 2. Audio Format Investigation

### Questions to Answer

| Question | Why It Matters | How to Find Out |
|----------|----------------|-----------------|
| What format does OpenAI Realtime API expect? | Must match | Read OpenAI docs |
| What format does OpenAI Realtime API produce? | Must handle | Test with actual API |
| What format does VoxStream capture produce? | Conversion needed? | Test capture output |
| What format does VoxStream playback expect? | Conversion needed? | Test playback input |
| Is conversion needed between VoxStream ↔ OpenAI? | Performance impact | Compare formats |
| How to convert between formats efficiently? | Latency sensitive | Research libraries |

### Format Details to Confirm

```python
# OpenAI Realtime API (need to confirm)
OPENAI_FORMAT = {
    "encoding": "pcm16",      # 16-bit PCM? Confirm
    "sample_rate": 24000,     # 24kHz? Confirm
    "channels": 1,            # Mono? Confirm
    "byte_order": "little",   # Little endian? Confirm
}

# VoxStream default (need to confirm)
VOXSTREAM_FORMAT = {
    "encoding": "???",        # PCM16? Float32?
    "sample_rate": 24000,     # Configurable?
    "channels": 1,            # Mono only?
    "chunk_size": "???",      # Bytes? Samples? Duration?
}

# Questions:
# - Does VoxStream output bytes or numpy arrays?
# - If numpy, what dtype? float32? int16?
# - Do we need to convert numpy → bytes for OpenAI?
```

### Audio Math to Verify

```python
# Chunk size calculation
sample_rate = 24000          # samples per second
channels = 1                 # mono
bit_depth = 16               # bits per sample
chunk_duration_ms = 100      # milliseconds

samples_per_chunk = sample_rate * chunk_duration_ms / 1000  # = 2400
bytes_per_sample = bit_depth / 8                             # = 2
bytes_per_chunk = samples_per_chunk * channels * bytes_per_sample  # = 4800

# Verify this matches actual VoxStream output
```

---

## 3. OpenAI Realtime API Investigation

### Questions to Answer

| Question | Why It Matters | How to Find Out |
|----------|----------------|-----------------|
| Exact audio format for input? | Must send correct format | OpenAI docs + test |
| Exact audio format for output? | Must handle correctly | OpenAI docs + test |
| How is audio sent? Base64? Binary? | Protocol design | OpenAI docs |
| What's the chunk size expectation? | Buffering strategy | OpenAI docs + test |
| How does server VAD work? | Affects client VAD needs | OpenAI docs |
| When does server VAD trigger response? | Turn-taking behavior | Test with API |
| How to handle audio during tool calls? | Pause/resume behavior | Test with API |

### Protocol Messages to Understand

```python
# Client → Server (audio input)
{
    "type": "input_audio_buffer.append",
    "audio": "base64_encoded_audio_here"  # What format exactly?
}

# Server → Client (audio output)
{
    "type": "response.audio.delta",
    "delta": "base64_encoded_audio_here"  # What format exactly?
}

# Questions:
# - Is audio always base64 encoded?
# - What's the chunk size in deltas?
# - Is there a "response.audio.done" to know when to flush?
```

---

## 4. Platform Differences Investigation

### Desktop (VoxStream)

| Aspect | Question | Status |
|--------|----------|--------|
| Audio capture | How does sounddevice callback work? | Need to verify |
| Audio playback | Direct vs buffered differences? | Need to test |
| VAD | Client-side VAD behavior? | Need to understand |
| Latency | Actual end-to-end latency? | Need to measure |
| Device selection | How to enumerate/select devices? | Need to verify |

### Web Browser (Future)

| Aspect | Question | Status |
|--------|----------|--------|
| Audio capture | MediaStream API → WebSocket? | Need to design |
| Audio format | Browser outputs Float32 48kHz? | Need to verify |
| Conversion | Who converts format? Server? Browser? | Need to decide |
| VAD | Browser-side or server-side? | Need to decide |
| Latency | WebSocket relay latency? | Need to estimate |

### Phone/Twilio (Future)

| Aspect | Question | Status |
|--------|----------|--------|
| Audio format | μ-law 8kHz? | Need to verify |
| Conversion | μ-law ↔ PCM16 conversion? | Need to implement |
| Resampling | 8kHz ↔ 24kHz? | Need to implement |
| Latency | Telephony latency expectations? | Need to research |

---

## 5. Error Handling Investigation

### Error Scenarios to Handle

| Scenario | What Happens? | How to Handle? |
|----------|---------------|----------------|
| No microphone connected | ? | Graceful error |
| Microphone permission denied | ? | Clear error message |
| Audio device disconnected mid-capture | ? | Reconnect or error? |
| Speaker not available | ? | Silent fail or error? |
| Audio buffer overflow | ? | Drop frames or block? |
| VoxStream initialization fails | ? | Fallback or error? |
| OpenAI connection lost during audio | ? | Buffer or drop? |

### Questions to Answer

```python
# What exceptions does VoxStream raise?
# - On device not found?
# - On permission denied?
# - On buffer issues?

# How to detect device changes?
# - Does sounddevice notify?
# - Do we need to poll?

# What happens if we call play_audio() with wrong format?
# - Silent? Error? Corruption?
```

---

## 6. VAD Behavior Investigation

### Questions to Answer

| Question | Why It Matters | How to Find Out |
|----------|----------------|-----------------|
| How does VoxStream VAD work? | Core feature | Read VADetector code |
| What triggers speech_start? | Sensitivity tuning | Test with real speech |
| What triggers speech_end? | Silence duration | Test with real speech |
| What is pre-buffer? | Audio before speech | Understand implementation |
| Can VAD be disabled? | Some use cases don't need it | Check config options |
| Server VAD vs Client VAD? | Who decides turn-taking? | Design decision |

### VAD State Machine to Understand

```
VoxStream VAD states (need to confirm):

    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │   SILENCE ──(energy > threshold)──► SPEECH_STARTING │
    │      ▲                                     │        │
    │      │                           (sustained)        │
    │      │                                     ▼        │
    │   (silence)◄──── SPEECH_ENDING ◄──── SPEECH         │
    │                       │                             │
    │                  (timeout)                          │
    │                       ▼                             │
    │                  callback(audio)                    │
    │                                                     │
    └─────────────────────────────────────────────────────┘

Questions:
- Is this the actual state machine?
- What are the transition thresholds?
- How is pre-buffer implemented?
- What audio is passed to speech_end callback?
```

---

## 7. Use Cases to Support

### Primary Use Cases

| Use Case | Description | Requirements |
|----------|-------------|--------------|
| **Voice chat** | User speaks, AI responds | Capture → AI → Playback |
| **Barge-in** | User interrupts AI | Stop playback immediately |
| **Continuous conversation** | Multiple turns | Seamless capture/playback |
| **Push-to-talk** | Manual control | No VAD, explicit start/stop |
| **Audio level display** | UI feedback | Real-time level monitoring |

### Edge Cases to Consider

| Edge Case | Description | How to Handle? |
|-----------|-------------|----------------|
| Background noise | Constant low-level noise | VAD threshold tuning |
| Multiple speakers | Other people talking | Not our problem? |
| Echo/feedback | AI audio picked up by mic | Echo cancellation? |
| Long silence | User doesn't respond | Timeout? Keep listening? |
| Very short utterance | "Yes", "No" | Don't miss short speech |
| Slow network | Audio chunks delayed | Buffer? Notify? |

---

## 8. Integration Points Investigation

### With RealtimeVoiceAPIPort

```python
# How do these two ports interact?

class VoiceAgent:
    def __init__(self, audio: AudioStreamPort, realtime: RealtimeVoiceAPIPort):
        self.audio = audio
        self.realtime = realtime

    async def run(self):
        # Capture → AI
        async for chunk in self.audio.start_capture():
            await self.realtime.send_audio(chunk)
            # Question: What format does send_audio expect?
            # Question: Should we convert here or in adapter?

        # AI → Playback
        async for event in self.realtime.events():
            if event.type == "audio.chunk":
                await self.audio.play_chunk(event.data)
                # Question: What format is event.data?
                # Question: Should we convert here or in adapter?
```

### Format Conversion Responsibility

```
Option A: Adapters handle conversion
    VoxStreamAdapter converts VoxStream format ↔ standard format
    OpenAIAdapter converts OpenAI format ↔ standard format
    VoiceAgent sees consistent format

Option B: VoiceAgent handles conversion
    Adapters pass through native format
    VoiceAgent converts between formats
    More flexible but more complex

Option C: Define standard format in ports
    All adapters MUST use PCM16 24kHz mono
    Conversion happens at adapter boundary
    Simple for VoiceAgent

Which option is best?
```

---

## 9. Confirmation Checklist

### Before Implementation, Confirm:

**VoxStream:**
- [ ] Exact return type of `start_capture_stream()`
- [ ] Exact format of captured audio (bytes? numpy? dtype?)
- [ ] How to register VAD callbacks
- [ ] VAD state machine behavior
- [ ] Difference between `play_audio()` and `queue_playback()`
- [ ] `interrupt_playback()` behavior
- [ ] Error types and when they occur
- [ ] Device enumeration API

**Audio Formats:**
- [ ] OpenAI Realtime API input format (encoding, sample rate, channels)
- [ ] OpenAI Realtime API output format
- [ ] VoxStream native format
- [ ] Conversion requirements (if any)
- [ ] Chunk size expectations

**Design Decisions:**
- [ ] Who handles format conversion? (Adapter vs Agent)
- [ ] Standard format for port interface? (PCM16 24kHz mono?)
- [ ] Server VAD vs Client VAD for OpenAI?
- [ ] Error handling strategy
- [ ] Device change handling strategy

---

## 10. Action Items

### Immediate (Before Coding)

1. **Read VoxStream source code**
   - `voxstream.py` - Main API
   - `audio/audio_manager.py` - Capture/playback management
   - `audio/vad.py` - VAD implementation

2. **Test VoxStream behavior**
   - Write test script for capture
   - Write test script for playback
   - Write test script for VAD
   - Measure actual latency

3. **Read OpenAI Realtime API docs**
   - Audio format specifications
   - Message protocol for audio
   - Server VAD behavior

4. **Design decision: Standard format**
   - Decide on port interface format
   - Document conversion responsibilities

### After Confirmation

5. **Implement port interface**
   - Based on confirmed understanding

6. **Implement VoxStreamAdapter**
   - With proper format handling

7. **Write comprehensive tests**
   - Based on edge cases identified

---

## 11. Questions for VoxStream Author

If VoxStream documentation is insufficient:

1. What format does `start_capture_stream()` yield? (bytes? numpy?)
2. How do I register VAD callbacks? (direct method? AudioManager?)
3. What's the recommended way to handle barge-in?
4. Does VoxStream handle echo cancellation?
5. What errors should I expect and handle?
6. Is there a way to get audio device change notifications?

---

## Summary

**Key uncertainties before implementation:**

| Area | Uncertainty Level | Action |
|------|-------------------|--------|
| VoxStream API | Medium | Read source code |
| VoxStream VAD | High | Read + test |
| Audio formats | Medium | Read docs + test |
| OpenAI format | Low | Read docs |
| Error handling | High | Read + test |
| Platform differences | Medium | Research |

**Do not start implementation until:**
1. VoxStream capture/playback/VAD behavior is confirmed
2. Audio format compatibility is verified
3. Design decisions are made (conversion responsibility, standard format)
