# RealtimeVoiceAPIPort: Gaps Requiring External Info

**Date:** 2025-01-01
**Scope:** AI provider real-time API connections (OpenAI, future Anthropic, etc.)

---

## Category 1: Requires External Documentation

### 1.1 OpenAI Realtime API Audio Protocol

**Questions to answer:**

| Question | Status |
|----------|--------|
| What audio format does it expect? (PCM16? Sample rate?) | Partially known (24kHz PCM16 from VoxStream refs) |
| Is audio base64 encoded in JSON messages? | Unknown |
| What chunk size does the API expect? | Unknown |
| Is there a maximum chunk size? | Unknown |
| How does the API signal end of audio response? | Unknown |

**Source:** OpenAI Realtime API documentation

---

### 1.2 OpenAI Server VAD Behavior

**Questions to answer:**

| Question | Status |
|----------|--------|
| How does server VAD detect speech end? | Unknown |
| What is the silence threshold? | Unknown |
| Can we configure VAD sensitivity? | Unknown |
| When exactly does it trigger response generation? | Unknown |

**Source:** OpenAI Realtime API documentation

---

### 1.3 OpenAI Message Protocol

**Questions to answer:**

Audio input:
```python
{
    "type": "input_audio_buffer.append",
    "audio": "???"  # Base64? Raw bytes? Format?
}
```

Audio output:
```python
{
    "type": "response.audio.delta",
    "delta": "???"  # Base64? Format?
}
```

Other messages to understand:
- `input_audio_buffer.commit`
- `input_audio_buffer.clear`
- `response.audio.done`
- `response.done`

**Source:** OpenAI Realtime API documentation

---

### 1.4 OpenAI Tool Calling in Realtime

**Questions to answer:**

| Question | Status |
|----------|--------|
| How are function calls signaled? | Unknown |
| How do we send function results back? | Unknown |
| Does audio continue during tool execution? | Unknown |
| How to resume after tool result? | Unknown |

**Source:** OpenAI Realtime API documentation

---

### 1.5 OpenAI Session Management

**Questions to answer:**

| Question | Status |
|----------|--------|
| How to configure session (voice, instructions)? | Unknown |
| Can we update session mid-conversation? | Unknown |
| How to handle session expiration? | Unknown |
| Rate limits and quotas? | Unknown |

**Source:** OpenAI Realtime API documentation

---

## Category 2: Future Provider Research

### 2.1 Anthropic Real-time API (Future)

**Status:** Not yet available

**When available, research:**
- Audio format requirements
- Message protocol
- VAD behavior
- Tool calling

---

### 2.2 Google Gemini Real-time (Future)

**Status:** Unknown availability

**When available, research:**
- Audio format requirements
- Message protocol
- Multimodal capabilities

---

## Category 3: Design Decisions Needed

### 3.1 Event Normalization

**Question:** How to normalize events across providers?

**OpenAI-specific events:**
- `response.audio.delta`
- `response.function_call_arguments.done`
- `input_audio_buffer.speech_started`

**Need to define:**
- `VoiceEventType` enum (provider-agnostic)
- `VoiceEvent` dataclass
- Translation layer in adapters

---

### 3.2 Format Conversion Responsibility

**Question:** Who converts audio formats?

**Options:**
- Option A: RealtimeVoiceAPIPort expects specific format, adapters convert
- Option B: Adapters accept any format, convert internally
- Option C: VoiceAgent handles conversion between AudioStreamPort and RealtimeVoiceAPIPort

**Recommendation:** Option A - Port defines expected format (PCM16, 24kHz), adapters handle provider-specific encoding (base64, etc.)

---

### 3.3 Connection State Machine

**Question:** What states should the port expose?

From existing design doc:
```
DISCONNECTED → CONNECTING → CONNECTED → RECONNECTING → DISCONNECTED/CLOSED
```

Need to finalize:
- State transitions
- Events emitted
- Error handling

---

## Summary: Blockers Before Implementation

### Must Resolve (Blockers):

| Gap | Category | How to Resolve |
|-----|----------|----------------|
| OpenAI audio format/encoding | External | Read OpenAI docs |
| OpenAI message protocol | External | Read OpenAI docs |
| Event normalization design | Design | Define VoiceEventType enum |

### Should Resolve (Important):

| Gap | Category | How to Resolve |
|-----|----------|----------------|
| OpenAI tool calling flow | External | Read OpenAI docs |
| OpenAI session management | External | Read OpenAI docs |
| Connection state machine | Design | Finalize states |

### Can Defer (Nice to Have):

| Gap | Category | How to Resolve |
|-----|----------|----------------|
| Anthropic API | Future | When available |
| Google Gemini | Future | When available |

---

## Related Documents

- `realtimevoiceapiport_design.md` - Existing design document
- `answers/openai_audio_format.md` - Partial info from VoxStream code

---

## Next Steps

1. **Read OpenAI Realtime API documentation** - Fill in protocol details
2. **Define VoiceEventType enum** - Normalized event types
3. **Design adapter translation layer** - OpenAI events → VoiceEvent
