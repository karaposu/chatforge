# Trace 04: RealtimeVoiceAPIPort (OpenAI Realtime)

Real-time bidirectional voice communication with AI. Enables voice assistants with interruption support.

---

## Entry Point

**File:** `chatforge/ports/realtime_voice.py:271`
**Interface:** `RealtimeVoiceAPIPort` (Abstract Base Class)

**Implementation:** `chatforge/adapters/realtime/openai/adapter.py`
**Class:** `OpenAIRealtimeAdapter`

**Primary Methods:**
```python
async def connect(config: VoiceSessionConfig) -> None
async def send_audio(chunk: bytes) -> None
async def send_text(text: str, trigger_response: bool = True) -> None
async def interrupt() -> None
async def events() -> AsyncGenerator[VoiceEvent, None]
async def disconnect() -> None
```

**Callers:**
- `VoiceAssistant` in examples
- Application voice handlers
- WebRTC signaling servers (future)

---

## Execution Path: Full Voice Session

```
async with OpenAIRealtimeAdapter(api_key) as realtime:
    │
    ├─► __aenter__()
    │   └── Return self (no setup needed yet)
    │
    ├─► connect(VoiceSessionConfig(...))
    │   │
    │   ├─1─► Acquire _lock (thread safety)
    │   │
    │   ├─2─► Validate not already connected
    │   │     └── Already connected → raise RealtimeSessionError
    │   │
    │   ├─3─► Build WebSocket config
    │   │     URL: wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview
    │   │     Headers: Authorization: Bearer {api_key}
    │   │              OpenAI-Beta: realtime=v1
    │   │
    │   ├─4─► Create WebSocketClient with reconnect policy
    │   │     └── ExponentialBackoff(base=1.0, factor=2.0, max=30.0)
    │   │
    │   ├─5─► Wire up callbacks
    │   │     ├── on_disconnect → _on_disconnect
    │   │     ├── on_connect → _on_reconnect_success
    │   │     └── on_reconnecting → _on_reconnecting
    │   │
    │   ├─6─► await _ws.connect()
    │   │     └── Connection error → RealtimeConnectionError
    │   │     └── 401 → RealtimeAuthenticationError
    │   │
    │   ├─7─► Start receive loop: asyncio.create_task(_receive_loop())
    │   │
    │   ├─8─► Send session config: _ws.send_json(session_update(config))
    │   │
    │   ├─9─► Wait for session.created event
    │   │     └── await _session_ready.wait() with 10s timeout
    │   │     └── Timeout → RealtimeConnectionError("Session initialization timeout")
    │   │
    │   └─10─ Emit CONNECTED event to queue
    │
    │   [Concurrent loops start here]
    │
    ├─► send_audio(chunk)  [Loop A - Capture]
    │   │
    │   ├── Check connected (_ensure_connected)
    │   │
    │   ├── Build message: input_audio_buffer_append(chunk)
    │   │   └── Base64 encode audio bytes
    │   │
    │   └── await _ws.send_json(message)
    │       └── Queue full → RealtimeRateLimitError("backpressure")
    │
    ├─► async for event in events():  [Loop B - Receive]
    │   │
    │   ├── await _event_queue.get()
    │   │
    │   ├── Check for _STOP_SENTINEL → exit
    │   │
    │   └── yield VoiceEvent
    │       │
    │       ├── AUDIO_CHUNK → bytes for playback
    │       ├── TRANSCRIPT → text of AI speech
    │       ├── INPUT_TRANSCRIPT → text of user speech
    │       ├── SPEECH_STARTED → user started speaking
    │       ├── SPEECH_ENDED → user stopped speaking
    │       ├── TOOL_CALL → AI wants to call function
    │       └── ... other event types
    │
    ├─► interrupt()  [On barge-in]
    │   │
    │   └── await _send_message(response_cancel())
    │
    └─► __aexit__()
        │
        └── await disconnect()
            │
            ├── Cancel _receive_task
            ├── await _ws.disconnect()
            ├── Clear state
            └── Queue _STOP_SENTINEL to stop events()
```

---

## Execution Path: _receive_loop

```
_receive_loop()  [Background task]
    │
    └── async for msg in _ws.messages():
        │
        ├─1─► Parse JSON: raw = json.loads(msg.as_text())
        │
        ├─2─► Translate to VoiceEvent: translate_event(raw)
        │     │
        │     │   [translator.py - OpenAI event → VoiceEvent]
        │     │
        │     ├── session.created → SESSION_CREATED
        │     ├── response.audio.delta → AUDIO_CHUNK (base64 decode)
        │     ├── response.audio.done → AUDIO_DONE
        │     ├── input_audio_buffer.speech_started → SPEECH_STARTED
        │     ├── input_audio_buffer.speech_stopped → SPEECH_ENDED
        │     ├── response.audio_transcript.delta → TRANSCRIPT
        │     ├── conversation.item.input_audio_transcription.completed → INPUT_TRANSCRIPT
        │     ├── response.function_call_arguments.done → TOOL_CALL
        │     ├── error → ERROR
        │     └── unknown → None (skip)
        │
        ├─3─► Handle session ready
        │     └── If SESSION_CREATED or SESSION_UPDATED → _session_ready.set()
        │
        ├─4─► Log errors
        │     └── If ERROR → logger.warning(code, message)
        │
        └─5─► Queue event: _event_queue.put_nowait(event)
              └── Queue full → drop event, log warning
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| WebSocket connection | connect() | disconnect() or __aexit__ | Hung connection if not closed |
| _receive_task | connect() | disconnect() | Task cancellation |
| _event_queue | __init__ | Never (fixed size) | Queue overflow drops events |
| asyncio.Lock | Per-operation | Automatic | Potential deadlock |

**Event queue:**
- Bounded: `maxsize=1000`
- Overflow: Events dropped with warning
- Sentinel: `_STOP_SENTINEL` signals end

**Reconnection:**
- Auto-reconnect enabled by default
- Exponential backoff: 1s → 2s → 4s → ... → 30s max
- Max attempts: 5 (configurable)
- On reconnect: Re-sends session config

---

## Error Path

```
Connection Errors:
    │
    ├── Network failure during connect()
    │   └── raise RealtimeConnectionError
    │
    ├── 401 Unauthorized
    │   └── raise RealtimeAuthenticationError
    │
    ├── Session timeout (no session.created within 10s)
    │   └── raise RealtimeConnectionError("Session initialization timeout")
    │
    └── Connection lost mid-session
        ├── _on_disconnect callback fires
        ├── DISCONNECTED event queued
        └── Auto-reconnect attempts (if enabled)

Send Errors:
    │
    ├── Not connected
    │   └── raise RealtimeSessionError("Not connected")
    │
    └── Send queue full (backpressure)
        └── raise RealtimeRateLimitError("Send queue full")

Message Processing Errors:
    │
    ├── Invalid JSON
    │   └── Log exception, queue ERROR event
    │
    └── Invalid base64 audio
        └── Return None from translator, skip event
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Latency (send) | <1ms | Queue, not network |
| Latency (event) | 50-200ms | WebSocket + AI processing |
| Memory (queue) | ~4MB max | 1000 events × ~4KB each |
| Reconnect time | 1-30s | Exponential backoff |

**Bottlenecks:**
1. Event queue capacity (1000 events)
2. WebSocket send queue (backpressure)
3. AI response latency

**Real-time requirements:**
- Audio must be sent continuously (24kHz, ~48KB/s)
- Events must be consumed to avoid queue overflow
- Interruption latency affects user experience

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| WebSocket connect | Network | connect() |
| Log: "OpenAI error: X" | adapter | ERROR event |
| Log: "Event queue full" | adapter | Queue overflow |
| CONNECTED event | queue | Successful connect |
| DISCONNECTED event | queue | Connection lost |
| RECONNECTING event | queue | Reconnect attempt |

---

## Why This Design

**WebSocket infrastructure reuse:**
- Uses shared `WebSocketClient` class
- Gets reconnection, metrics, heartbeat for free
- Consistent behavior across adapters

**Bounded event queue:**
- Prevents unbounded memory growth
- Drop oldest if overwhelmed
- Size 1000 should handle bursts

**Translator pattern:**
- OpenAI events → normalized VoiceEvent
- Provider-agnostic consumer code
- Easy to add new providers

**Async generator for events:**
- Natural Python iteration
- Backpressure via queue
- Clean cancellation

---

## What Feels Incomplete

1. **No audio format conversion:**
   - Assumes PCM16 24kHz in and out
   - No resampling
   - No codec support

2. **No conversation history preservation:**
   - Session lost on disconnect
   - No way to resume conversation
   - Must restart from scratch

3. **No usage/cost tracking:**
   - USAGE_UPDATED event received but not exposed
   - No token counting
   - No cost estimation

4. **Tool results not fully integrated:**
   - `send_tool_result` exists
   - No example of tool execution loop
   - Not clear how to wire up tools

5. **No audio level/quality metrics:**
   - No VU meter
   - No silence detection stats
   - No quality indicators

---

## What Feels Vulnerable

1. **Queue overflow drops events:**
   - AUDIO_CHUNK drops cause audio gaps
   - TOOL_CALL drops break functionality
   - No priority queuing

2. **Reconnect loses context:**
   - Re-sends session config
   - Doesn't replay conversation
   - User may hear repeated greeting

3. **API key in memory:**
   - Stays for process lifetime
   - Logged in connection URL (model param only, but still)

4. **No rate limiting on send:**
   - Can spam send_audio
   - May exceed OpenAI limits
   - Backpressure only on local queue

5. **Event processing errors:**
   - One bad event logs error but continues
   - Could miss important events
   - No dead letter queue

---

## What Feels Bad Design

1. **Single consumer for events():**
   - "Only one consumer should iterate events()"
   - But no enforcement
   - Multiple consumers would steal events

2. **Lock on every operation:**
   - `_ensure_connected()` doesn't need lock
   - Send operations could be lock-free
   - Lock contention under load

3. **Mixed sync/async patterns:**
   - Callbacks are sync (`on_disconnect`)
   - But may need to do async work
   - `asyncio.create_task` to bridge

4. **Sentinel value for stop:**
   - `_STOP_SENTINEL = object()`
   - Mixed types in queue (VoiceEvent | object)
   - Could use None or typed enum

5. **Model hardcoded:**
   - `DEFAULT_MODEL = "gpt-4o-realtime-preview-2025-06-03"`
   - Date in model name will become stale
   - Should be "latest" or config-based
