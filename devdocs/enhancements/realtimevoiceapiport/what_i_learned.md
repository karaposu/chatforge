# What I Learned: RealtimeVoiceAPIPort Implementation

*Lessons learned from implementing the RealtimeVoiceAPIPort and OpenAI Realtime adapter.*

---

## 1. WebSocketMessage API Mismatch

**Issue:** The implementation plan assumed `WebSocketMessage` had an `as_json()` method, but it only has `as_text()` and `as_bytes()`.

**Symptom:**
```
AttributeError: 'WebSocketMessage' object has no attribute 'as_json'
```

**Fix:** Parse JSON manually from text:
```python
# Wrong (assumed API)
raw = msg.as_json()

# Correct
raw = json.loads(msg.as_text())
```

**Lesson:** Always verify the actual API of infrastructure components before writing adapters. The implementation plan was written based on assumed interfaces rather than the actual `WebSocketMessage` class.

---

## 2. Session Initialization Event Ordering

**Observation:** OpenAI Realtime API sends events in this order during connection:
1. `session.created` - Session initialized
2. `session.updated` - After our config is applied (may come twice)
3. `conversation.item` - Conversation state

**Key insight:** The `session.created` event arrives BEFORE our `session.update` message is processed. The adapter correctly waits for either `session.created` or `session.updated` to signal session readiness.

---

## 3. Event Queue Design Decisions

**Bounded queue was the right choice.** With `maxsize=1000`, we prevent unbounded memory growth if the consumer can't keep up with audio chunks.

**Stop sentinel pattern works well.** Using a sentinel object to signal the event generator to stop provides clean termination without relying on exception handling:
```python
_STOP_SENTINEL = object()

async def events(self):
    while True:
        event = await self._event_queue.get()
        if event is _STOP_SENTINEL:
            return
        yield event
```

---

## 4. OpenAI Realtime API Specifics

### Audio Format
- Default PCM16 at 24kHz mono
- Audio chunks arrive in variable sizes (4800, 7200, 12000, 28800 bytes observed)
- Total audio for "Hi!" response: ~88,800 bytes

### Event Types Observed
For a simple text-to-speech request:
```
session.created
session.updated (x2)
conversation.item (user message added)
response.started
conversation.item (assistant message)
transcript (streaming, e.g., "Hi", "!")
audio.chunk (multiple)
audio.done
transcript (final: "Hi!")
response.done
```

### Message Flow
- `session.update` - Configure voice, system prompt, modalities
- `conversation.item.create` - Add text message
- `response.create` - Trigger AI response

---

## 5. Reconnection Handling

**Important:** On reconnection, the session state is lost. The adapter must re-send `session.update` with the stored config to restore the session configuration.

```python
def _on_reconnect_success(self) -> None:
    if self._config:
        asyncio.create_task(self._resend_session_config())
```

---

## 6. Thread Safety Considerations

**asyncio.Lock is essential** for protecting shared state between:
- `connect()` / `disconnect()` - Modify `_ws`, `_config`, `_receive_task`
- `is_connected()` - Read `_ws` state
- Event handlers - Modify queue state

**Local reference pattern** prevents races in `is_connected()`:
```python
def is_connected(self) -> bool:
    ws = self._ws  # Local reference
    return ws is not None and ws.is_connected
```

---

## 7. Error Handling Gaps

### Base64 Decoding
Audio data arrives base64-encoded. Invalid data must be handled gracefully:
```python
def _safe_base64_decode(data: str) -> bytes | None:
    try:
        return base64.b64decode(data)
    except (ValueError, binascii.Error) as e:
        logger.warning("Invalid base64 data: %s", e)
        return None
```

### JSON Parsing in Tool Arguments
Tool call arguments come as JSON strings that may be malformed:
```python
def _safe_json_parse(s: str) -> Any:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s  # Return raw string if parsing fails
```

---

## 8. Testing Strategy

### Mock Adapter Value
The `MockRealtimeAdapter` proved invaluable for:
- Testing without API costs
- Simulating edge cases (disconnects, errors)
- Verifying event flow logic
- Fast test execution (28 tests in 0.09s)

### Integration Test Gating
Using `pytest.mark.skipif` for API tests prevents CI failures:
```python
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
```

---

## 9. Configuration Validation

**Validate early, fail fast.** Using `__post_init__` on dataclasses catches invalid configs before they cause runtime errors:
```python
@dataclass
class VoiceSessionConfig:
    temperature: float = 0.8

    def __post_init__(self):
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be 0.0-2.0, got {self.temperature}")
```

---

## 10. API Design Insights

### Separating Text Input from Response Trigger
The original design only had `send_text()`. Adding `add_text_item()` and `trigger_response` parameter provides flexibility:
```python
# Send multiple context items, then trigger once
await adapter.add_text_item("Context 1")
await adapter.add_text_item("Context 2")
await adapter.create_response()

# Or the simple case
await adapter.send_text("Hello")  # trigger_response=True by default
```

### VAD Mode Handling
Three modes with different server behaviors:
- `server` - Server detects speech, auto-triggers response
- `client` - App detects speech, must call `commit_audio()`
- `none` - Manual mode, must call `commit_audio()`

For `client` and `none`, we disable server VAD:
```python
if config.vad_mode == "server":
    session["turn_detection"] = {...}
else:
    session["turn_detection"] = None
```

---

## 11. Infrastructure Reuse Success

The WebSocket infrastructure provided significant value:
- **Automatic reconnection** with exponential backoff
- **Ping/pong heartbeat** for connection health
- **Send queue** with backpressure handling
- **Connection metrics** for debugging
- **Clean lifecycle management** via context manager

This allowed the adapter to focus purely on OpenAI-specific logic.

---

## 12. Performance Observations

From the live test:
- Connection setup: ~1.5 seconds
- Response latency: Near-instant after message sent
- Audio generation: Continuous streaming
- Total for "Hi!": 22 messages, 126KB received

The bounded queue (1000 events) is more than sufficient for normal operation.

---

## Summary

The implementation validated the hexagonal architecture approach. The port interface cleanly separates voice application logic from provider specifics. Key takeaways:

1. **Verify infrastructure APIs** before writing adapter code
2. **Bounded queues + sentinels** for clean async patterns
3. **Re-send state on reconnection** for stateful protocols
4. **Mock adapters** enable comprehensive testing
5. **Validate early** with dataclass `__post_init__`
6. **Flexible APIs** (separate add vs trigger) enable more use cases
