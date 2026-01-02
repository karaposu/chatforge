# Verdict: Streaming Ports Architecture

**Date:** 2025-01-01
**Status:** Decision Made

---

## The Question

Chatforge has several enhancement proposals for streaming-related ports:

- `devdocs/enhancements/textstreaming/streaming_port.md` - Text streaming to clients
- `devdocs/enhancements/audiostreamingport/` - Audio I/O across platforms
- `devdocs/enhancements/realtimevoiceapiport/` - Realtime AI API connections

**The core questions:**

1. Should streaming have its own port abstraction?
2. Should audio streaming be a separate port from text streaming?
3. Or should these just be services without ports (like LLMs use `get_llm()`)?
4. What's the most minimal, impactful improvement?

---

## Context: What is a Port?

In hexagonal architecture, a **port abstracts an external dependency** so domain logic doesn't couple to specific implementations.

| Good Port Candidates | Bad Port Candidates |
|---------------------|---------------------|
| External services (TTS providers) | Transport mechanisms (SSE vs WebSocket) |
| Hardware (audio devices) | Internal implementation details |
| AI providers (OpenAI vs Anthropic) | One-off utilities |

**The test:** "Would I swap this implementation for a different provider?"

---

## The Three Proposed Ports

### 1. StreamingPort (Text Streaming)

**Purpose:** Stream LLM tokens to clients via SSE or WebSocket.

```python
class StreamingPort(Protocol):
    async def stream_to_client(self, context_id, events) -> AsyncGenerator[bytes, None]: ...
```

**Analysis:**
- It abstracts **transport** (SSE vs WebSocket), not a **provider**
- The agent already produces `StreamEvent` objects
- Converting events to SSE/WebSocket format is an **API layer concern**
- You wouldn't "swap SSE for WebSocket" at runtime based on business logic

**Better approach:**
```python
# Agent yields events (domain layer)
async for event in agent.process_stream(message):
    yield event  # StreamEvent dataclass

# API layer handles transport (infrastructure layer)
@app.post("/chat/stream")
async def stream_chat(request: Request):
    async def generate():
        async for event in agent.process_stream(message):
            yield f"data: {json.dumps(event.to_dict())}\n\n"  # SSE format
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Verdict:** Skip StreamingPort. Keep `StreamEvent` as a dataclass only.

---

### 2. AudioStreamPort (Audio I/O)

**Purpose:** Abstract real-time audio capture and playback across platforms.

```python
class AudioStreamPort(ABC):
    async def start_capture(self) -> AsyncGenerator[bytes, None]: ...
    async def stop_capture(self) -> None: ...
    async def play_audio(self, chunk: bytes) -> None: ...
    async def stop_playback(self) -> None: ...
    def set_vad_callbacks(on_start, on_end) -> None: ...
```

**Analysis:**
- Abstracts **genuinely different implementations**:
  - `VoxStreamAdapter` - sounddevice/PortAudio (desktop)
  - `WebRTCAdapter` - WebSocket relay (web browser)
  - `TwilioAdapter` - Media Streams (phone calls)
- Domain logic (VoiceAgent) shouldn't know about sounddevice vs WebRTC
- Classic hexagonal: "I need audio in/out, don't care how it works"
- You **would** swap implementations based on deployment target

**Verdict:** Keep AudioStreamPort. This is a true port abstraction.

---

### 3. RealtimeVoiceAPIPort (AI API Connection)

**Purpose:** Abstract bidirectional streaming with AI providers.

```python
class RealtimeVoiceAPIPort(ABC):
    async def connect(self, config: VoiceSessionConfig) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_audio(self, chunk: bytes) -> None: ...
    async def send_text(self, text: str) -> None: ...
    async def send_tool_result(self, call_id, result) -> None: ...
    def events(self) -> AsyncGenerator[VoiceEvent, None]: ...
```

**Analysis:**
- Abstracts **AI providers** (similar to TTSPort):
  - `OpenAIRealtimeAdapter` - OpenAI Realtime API
  - Future: `AnthropicRealtimeAdapter`, `GoogleRealtimeAdapter`
- Normalizes provider-specific events to `VoiceEvent`
- Domain logic sees consistent events regardless of provider
- You **would** swap providers based on cost/quality/features

**Verdict:** Keep RealtimeVoiceAPIPort. This is a true port abstraction.

---

## Decision

### Keep These Two Ports

**AudioStreamPort** - For hardware audio abstraction
```
VoiceAgent
    │
    ▼
AudioStreamPort (interface)
    │
    ├── VoxStreamAdapter (desktop)
    ├── WebRTCAdapter (web browser)
    └── TwilioAdapter (phone calls)
```

**RealtimeVoiceAPIPort** - For AI provider abstraction
```
VoiceAgent
    │
    ▼
RealtimeVoiceAPIPort (interface)
    │
    ├── OpenAIRealtimeAdapter
    ├── AnthropicRealtimeAdapter (future)
    └── GoogleRealtimeAdapter (future)
```

### Skip StreamingPort

Text streaming is handled by:
1. Agent yields `StreamEvent` objects (domain layer)
2. API endpoint converts to SSE/WebSocket (infrastructure layer)

No port abstraction needed.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CHATFORGE PORTS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Existing:                                                       │
│  ├── TTSPort              → ElevenLabs, OpenAI TTS              │
│  ├── StoragePort          → SQLite, Postgres                    │
│  ├── TracingPort          → MLflow, LangSmith                   │
│  └── KnowledgePort        → Pinecone, Chroma                    │
│                                                                  │
│  NEW for Voice:                                                  │
│  ├── AudioStreamPort      → VoxStream, WebRTC, Twilio           │
│  └── RealtimeVoiceAPIPort → OpenAI Realtime, future providers   │
│                                                                  │
│  NOT Needed:                                                     │
│  └── StreamingPort        → API layer handles SSE/WebSocket     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Not Services-Only (like LLMs)?

LLMs use `get_llm()` factory without a port:
```python
llm = get_llm(provider="openai", model_name="gpt-4o-mini")
```

**Why ports are better for audio/realtime:**

1. **Dependency injection** - VoiceAgent accepts `AudioStreamPort`, easy to mock
2. **Explicit contracts** - Interface defines exactly what's needed
3. **Bidirectional streaming** - More complex than simple request/response
4. **Hardware abstraction** - Audio I/O is fundamentally different per platform

LLMs are simpler (call → response). Audio/realtime is continuous bidirectional streaming with state.

---

## Implementation Priority

| Port | Priority | Reason |
|------|----------|--------|
| RealtimeVoiceAPIPort | High | Enables voice AI with OpenAI Realtime |
| AudioStreamPort | High | Enables cross-platform audio |
| StreamingPort | Skip | Not needed, API layer handles |

---

## Files Affected

**Keep and refine:**
- `devdocs/enhancements/audiostreamingport/` - Valid proposals
- `devdocs/enhancements/realtimevoiceapiport/` - Valid proposals

**Archive or remove:**
- `devdocs/enhancements/textstreaming/streaming_port.md` - Replace with simple `StreamEvent` dataclass

---

## Summary

| Proposal | Verdict | Reason |
|----------|---------|--------|
| **StreamingPort** (text) | Skip | Transport is API layer concern |
| **AudioStreamPort** | Keep | True hardware abstraction |
| **RealtimeVoiceAPIPort** | Keep | True provider abstraction |

**The minimal impactful improvement:** Add `AudioStreamPort` and `RealtimeVoiceAPIPort` with corresponding services, skip `StreamingPort`.
