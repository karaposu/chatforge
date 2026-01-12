# In-Memory Conversation Item Tracker

## Overview

The OpenAI Realtime API maintains conversation history as a list of "items". To support `reset_conversation()`, the adapter must track item IDs as they're created during a session.

**Scope:** In-memory only. No persistence. Cleared on disconnect.

**Why no persistence?** Applications manage their own context via ContextManager. The adapter only needs to track items for the current WebSocket session to enable mid-session reset.

---

## What Creates Items

Every conversation item has a unique `item_id` assigned by OpenAI:

| User Action | API Event | Item Type |
|-------------|-----------|-----------|
| User speaks → VAD commits | `conversation.item.created` | `message` (input_audio) |
| `add_text_item(text)` | `conversation.item.created` | `message` (input_text) |
| `send_text(text)` | `conversation.item.created` | `message` (input_text) |
| AI generates response | `conversation.item.created` | `message` (output) |
| AI calls a tool | `conversation.item.created` | `function_call` |
| `send_tool_result()` | `conversation.item.created` | `function_call_output` |

**Key insight:** We don't create items directly. We listen for `conversation.item.created` events from the server.

---

## Event Structure

When an item is created, OpenAI sends:

```json
{
  "type": "conversation.item.created",
  "previous_item_id": "item_abc123",
  "item": {
    "id": "item_def456",
    "object": "realtime.item",
    "type": "message",
    "status": "completed",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "Hello"
      }
    ]
  }
}
```

**We only need:** `event["item"]["id"]`

---

## Implementation

### Data Structure

Simple list is sufficient. Items are always deleted in bulk (reset), not individually.

```python
class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, api_key: str, ...):
        # ... existing init
        self._conversation_item_ids: list[str] = []
```

**Why list, not set?**
- Order might matter for debugging
- No duplicates expected (IDs are unique)
- Iteration order is deterministic

---

### Tracking Items

Track during raw event processing, before normalization:

```python
async def _event_loop(self):
    """Internal loop that reads from WebSocket and processes events."""
    async for raw_message in self._ws:
        raw_event = json.loads(raw_message)

        # Track conversation items
        self._track_item_if_created(raw_event)

        # Normalize to VoiceEvent
        event = self._normalize_event(raw_event)
        if event:
            await self._event_queue.put(event)

def _track_item_if_created(self, raw_event: dict) -> None:
    """Track item ID if this is a conversation.item.created event."""
    if raw_event.get("type") != "conversation.item.created":
        return

    item = raw_event.get("item", {})
    item_id = item.get("id")

    if item_id:
        self._conversation_item_ids.append(item_id)
        logger.debug(f"Tracked conversation item: {item_id}")
```

---

### Resetting Conversation

Delete all tracked items:

```python
async def reset_conversation(self) -> None:
    """
    Delete all conversation items to reset history.

    After reset, the session has empty history but maintains:
    - System prompt
    - Tool definitions
    - Session configuration
    """
    if not self._conversation_item_ids:
        logger.debug("No items to delete")
        return

    logger.info(f"Resetting conversation: deleting {len(self._conversation_item_ids)} items")

    for item_id in self._conversation_item_ids:
        await self._send({
            "type": "conversation.item.delete",
            "item_id": item_id
        })

    self._conversation_item_ids.clear()
```

**Note:** We don't wait for `conversation.item.deleted` confirmations. Fire-and-forget is sufficient since:
- Items are deleted server-side immediately
- If delete fails, we'll get an error event
- Tracking list is cleared regardless (worst case: orphaned items on server)

---

### Lifecycle

```python
async def connect(self, config: VoiceSessionConfig) -> None:
    # Clear any stale items from previous connection attempt
    self._conversation_item_ids.clear()

    # ... establish WebSocket connection

async def disconnect(self) -> None:
    # ... close WebSocket

    # Clear items (session is gone anyway)
    self._conversation_item_ids.clear()
```

---

## Memory Considerations

**Typical session:** 50-200 items (conservative estimate)
**Memory per item:** ~36 bytes (UUID string)
**Total:** ~7KB worst case

Negligible. No memory management needed.

**Long sessions:** If a session runs for hours with thousands of turns:
- 1000 items ≈ 36KB
- Still negligible
- Session would likely hit OpenAI's limits first

---

## What We Don't Track

| Event | Why Not Tracked |
|-------|-----------------|
| `conversation.item.deleted` | We initiated it, no need to track |
| `conversation.item.truncated` | Item still exists, just truncated |
| `conversation.item.input_audio_transcription.*` | Metadata, not an item |
| `response.*` | Responses create items via `conversation.item.created` |

---

## Edge Cases

### Item Created During Reset

```
Timeline:
  reset_conversation() starts
    → delete item_001
    → delete item_002
    → user speaks, item_003 created  ← Race condition?
    → delete item_003  ← Not in our list!
  reset_conversation() ends
```

**Mitigation:** Don't reset during active conversation. The ContextManager should:
1. Check `is_safe_for_injection()` before reset
2. Or accept that items created during reset survive

### Failed Delete

If `conversation.item.delete` fails:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "Item not found: item_xyz"
  }
}
```

**Handling:** Log and continue. Item might have been auto-deleted by server.

```python
async def _handle_error_event(self, error: dict):
    if "Item not found" in error.get("message", ""):
        logger.warning(f"Item already deleted: {error}")
        return  # Not a real error
    # ... handle other errors
```

---

## Integration with Port Interface

Add to `RealtimeVoiceAPIPort`:

```python
class RealtimeVoiceAPIPort(ABC):
    # ... existing methods

    @abstractmethod
    async def reset_conversation(self) -> None:
        """
        Clear conversation history.

        After reset:
        - Conversation history is empty
        - System prompt remains
        - Tools remain configured
        - Session stays connected

        Raises:
            RealtimeSessionError: Not connected
            NotImplementedError: Provider doesn't support reset
        """
        ...
```

Add to `ProviderCapabilities`:

```python
@dataclass
class ProviderCapabilities:
    # ... existing fields
    supports_conversation_reset: bool = False
```

OpenAI adapter reports:

```python
def get_capabilities(self) -> ProviderCapabilities:
    return ProviderCapabilities(
        provider_name="openai",
        supports_conversation_reset=True,  # We support it!
        # ... other capabilities
    )
```

---

## Summary

```
┌─────────────────────────────────────────────────────────┐
│                  OpenAIRealtimeAdapter                   │
│                                                          │
│  _conversation_item_ids: list[str] = []                 │
│                                                          │
│  Events In:                                              │
│    conversation.item.created → append(item_id)          │
│                                                          │
│  Actions Out:                                            │
│    reset_conversation() → delete all → clear list       │
│                                                          │
│  Lifecycle:                                              │
│    connect()    → clear list                            │
│    disconnect() → clear list                            │
└─────────────────────────────────────────────────────────┘
```

Simple, in-memory, session-scoped. No persistence needed.
