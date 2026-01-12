# Step-by-Step Implementation: In-Memory Conversation Item Tracking

## Analysis Summary

### Existing Architecture

```
chatforge/
├── ports/
│   └── realtime_voice.py          # Abstract port + ProviderCapabilities
└── adapters/
    └── realtime/
        └── openai/
            ├── adapter.py         # OpenAIRealtimeAdapter
            ├── translator.py      # Raw event → VoiceEvent
            └── messages.py        # Message factory functions
```

### Key Integration Points

1. **Item Creation Detection** (`translator.py:224-229`)
   - Already translates `conversation.item.created` → `VoiceEventType.CONVERSATION_ITEM`
   - Event data contains `raw.get("item")` with `id` field

2. **Event Processing Loop** (`adapter.py:414-446`)
   - `_receive_loop()` processes raw events before translation
   - Perfect place to track item IDs before emitting to application

3. **Message Factory** (`messages.py`)
   - Need to add `conversation_item_delete()` function

4. **Lifecycle Methods** (`adapter.py:129-228`)
   - `connect()` - clear tracking
   - `disconnect()` - clear tracking

5. **Thread Safety** (`adapter.py:107`)
   - Already has `self._lock = asyncio.Lock()`

---

## Implementation Phases

### Phase 1: Port Interface Update

**File:** `chatforge/ports/realtime_voice.py`

**Goal:** Add abstract method and capability flag.

#### Step 1.1: Add Capability Flag

```python
# In ProviderCapabilities dataclass (around line 251)
@dataclass
class ProviderCapabilities:
    """What the provider supports."""

    provider_name: str
    supports_server_vad: bool = True
    supports_function_calling: bool = True
    supports_interruption: bool = True
    supports_transcription: bool = True
    supports_input_transcription: bool = True
    supports_conversation_reset: bool = False  # NEW
    max_audio_length_seconds: float | None = None
    available_voices: list[str] = field(default_factory=list)
    available_models: list[str] = field(default_factory=list)
```

#### Step 1.2: Add Abstract Method

```python
# In RealtimeVoiceAPIPort class (after cancel_response, around line 434)

@abstractmethod
async def reset_conversation(self) -> None:
    """
    Clear conversation history.

    After reset:
    - Conversation history is empty
    - System prompt remains active
    - Tools remain configured
    - Session stays connected

    Use this for "stateless-like" behavior where you want
    to inject fresh context without prior conversation history.

    Raises:
        RealtimeSessionError: Not connected
        NotImplementedError: Provider doesn't support reset
    """
    ...
```

#### Step 1.3: Update __all__

No change needed - `ProviderCapabilities` already exported.

---

### Phase 2: Message Factory

**File:** `chatforge/adapters/realtime/openai/messages.py`

**Goal:** Add conversation item delete message.

#### Step 2.1: Add Delete Function

```python
# Add after response_cancel() (around line 135)

def conversation_item_delete(item_id: str) -> dict:
    """Create conversation.item.delete message."""
    return {
        "type": "conversation.item.delete",
        "item_id": item_id,
    }
```

---

### Phase 3: Adapter - Data Structure

**File:** `chatforge/adapters/realtime/openai/adapter.py`

**Goal:** Add item tracking storage.

#### Step 3.1: Add Instance Variable

```python
# In __init__ (around line 100, after self._lock)

def __init__(
    self,
    api_key: str,
    model: str = DEFAULT_MODEL,
    *,
    connect_timeout: float = 30.0,
    auto_reconnect: bool = True,
    max_reconnect_attempts: int = 5,
    enable_metrics: bool = True,
):
    # ... existing code ...

    # Lock for thread safety on shared state
    self._lock = asyncio.Lock()

    # NEW: Track conversation item IDs for reset_conversation()
    self._conversation_item_ids: list[str] = []
```

---

### Phase 4: Adapter - Item Tracking

**File:** `chatforge/adapters/realtime/openai/adapter.py`

**Goal:** Track items as they're created.

#### Step 4.1: Add Tracking Method

```python
# Add as new internal method (around line 400)

def _track_conversation_item(self, raw_event: dict) -> None:
    """
    Track conversation item ID if this is a creation event.

    Called during raw event processing, before translation.
    """
    if raw_event.get("type") != "conversation.item.created":
        return

    item = raw_event.get("item", {})
    item_id = item.get("id")

    if item_id and item_id not in self._conversation_item_ids:
        self._conversation_item_ids.append(item_id)
        logger.debug("Tracked conversation item: %s (total: %d)",
                    item_id, len(self._conversation_item_ids))
```

#### Step 4.2: Integrate Into Receive Loop

```python
# Modify _receive_loop() (around line 414)

async def _receive_loop(self) -> None:
    """Background task to receive and translate events."""
    try:
        async for msg in self._ws.messages():
            try:
                raw = json.loads(msg.as_text())

                # NEW: Track conversation items before translation
                self._track_conversation_item(raw)

                event = translate_event(raw)
                # ... rest of existing code ...
```

---

### Phase 5: Adapter - Reset Method

**File:** `chatforge/adapters/realtime/openai/adapter.py`

**Goal:** Implement reset_conversation().

#### Step 5.1: Add Reset Method

```python
# Add new public method (after update_session, around line 328)

async def reset_conversation(self) -> None:
    """
    Clear conversation history by deleting all tracked items.

    After reset:
    - Conversation history is empty
    - System prompt remains active
    - Tools remain configured
    - Session stays connected
    """
    async with self._lock:
        self._ensure_connected()

        if not self._conversation_item_ids:
            logger.debug("reset_conversation: no items to delete")
            return

        item_count = len(self._conversation_item_ids)
        logger.info("Resetting conversation: deleting %d items", item_count)

        # Delete all tracked items
        for item_id in self._conversation_item_ids:
            try:
                await self._ws.send_json(messages.conversation_item_delete(item_id))
            except Exception as e:
                # Log but continue - item might already be deleted
                logger.warning("Failed to delete item %s: %s", item_id, e)

        # Clear tracking regardless of delete success
        self._conversation_item_ids.clear()

        logger.debug("Conversation reset complete")
```

---

### Phase 6: Adapter - Lifecycle Integration

**File:** `chatforge/adapters/realtime/openai/adapter.py`

**Goal:** Clear tracking on connect/disconnect.

#### Step 6.1: Update connect()

```python
# In connect() method, after self._session_ready.clear() (around line 136)

async def connect(self, config: VoiceSessionConfig) -> None:
    """Connect to OpenAI Realtime API."""
    async with self._lock:
        if self._ws is not None and self._ws.is_connected:
            raise RealtimeSessionError("Already connected")

        self._config = config
        self._session_ready.clear()

        # NEW: Clear any stale item tracking from previous session
        self._conversation_item_ids.clear()

        # ... rest of existing code ...
```

#### Step 6.2: Update disconnect()

```python
# In disconnect() method, before signaling stop (around line 218)

async def disconnect(self) -> None:
    """Disconnect from OpenAI."""
    async with self._lock:
        # ... existing cleanup code ...

        self._config = None
        self._session_ready.clear()

        # NEW: Clear item tracking
        self._conversation_item_ids.clear()

        # Signal event generator to stop
        self._queue_event_nowait(_STOP_SENTINEL)
```

---

### Phase 7: Adapter - Update Capabilities

**File:** `chatforge/adapters/realtime/openai/adapter.py`

**Goal:** Report reset capability.

#### Step 7.1: Update get_capabilities()

```python
# In get_capabilities() method (around line 354)

def get_capabilities(self) -> ProviderCapabilities:
    """Get OpenAI capabilities."""
    return ProviderCapabilities(
        provider_name="openai",
        supports_server_vad=True,
        supports_function_calling=True,
        supports_interruption=True,
        supports_transcription=True,
        supports_input_transcription=True,
        supports_conversation_reset=True,  # NEW
        available_voices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        available_models=[
            # ... existing models ...
        ],
    )
```

---

### Phase 8: Mock Adapter Update

**File:** `chatforge/adapters/realtime/mock/adapter.py`

**Goal:** Implement reset_conversation() in mock for testing.

#### Step 8.1: Add to Mock

```python
# Add reset_conversation to MockRealtimeAdapter

def __init__(self, ...):
    # ... existing init ...
    self._conversation_item_ids: list[str] = []

async def reset_conversation(self) -> None:
    """Mock implementation - just clear tracking."""
    self._conversation_item_ids.clear()

def get_capabilities(self) -> ProviderCapabilities:
    return ProviderCapabilities(
        provider_name="mock",
        supports_conversation_reset=True,  # Support it in mock
        # ... other capabilities ...
    )
```

---

### Phase 9: Testing

**File:** `tests/adapters/realtime/openai/test_item_tracking.py`

#### Step 9.1: Unit Tests

```python
"""Tests for conversation item tracking."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from chatforge.adapters.realtime.openai.adapter import OpenAIRealtimeAdapter


class TestItemTracking:
    """Test conversation item tracking."""

    def test_init_empty_tracking(self):
        """Tracking list starts empty."""
        adapter = OpenAIRealtimeAdapter(api_key="test")
        assert adapter._conversation_item_ids == []

    def test_track_conversation_item(self):
        """Items are tracked on creation event."""
        adapter = OpenAIRealtimeAdapter(api_key="test")

        raw_event = {
            "type": "conversation.item.created",
            "item": {"id": "item_123", "type": "message"}
        }

        adapter._track_conversation_item(raw_event)

        assert "item_123" in adapter._conversation_item_ids

    def test_track_ignores_other_events(self):
        """Non-creation events are ignored."""
        adapter = OpenAIRealtimeAdapter(api_key="test")

        raw_event = {"type": "session.created", "session": {}}

        adapter._track_conversation_item(raw_event)

        assert adapter._conversation_item_ids == []

    def test_track_no_duplicates(self):
        """Same item ID is not tracked twice."""
        adapter = OpenAIRealtimeAdapter(api_key="test")

        raw_event = {
            "type": "conversation.item.created",
            "item": {"id": "item_123"}
        }

        adapter._track_conversation_item(raw_event)
        adapter._track_conversation_item(raw_event)

        assert adapter._conversation_item_ids == ["item_123"]

    def test_track_handles_missing_id(self):
        """Events without item ID are handled gracefully."""
        adapter = OpenAIRealtimeAdapter(api_key="test")

        raw_event = {
            "type": "conversation.item.created",
            "item": {}  # No id field
        }

        adapter._track_conversation_item(raw_event)

        assert adapter._conversation_item_ids == []


class TestResetConversation:
    """Test reset_conversation method."""

    @pytest.fixture
    def connected_adapter(self):
        """Create adapter with mocked connection."""
        adapter = OpenAIRealtimeAdapter(api_key="test")
        adapter._ws = MagicMock()
        adapter._ws.is_connected = True
        adapter._ws.send_json = AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_reset_clears_tracking(self, connected_adapter):
        """Reset clears the tracking list."""
        connected_adapter._conversation_item_ids = ["item_1", "item_2"]

        await connected_adapter.reset_conversation()

        assert connected_adapter._conversation_item_ids == []

    @pytest.mark.asyncio
    async def test_reset_sends_delete_messages(self, connected_adapter):
        """Reset sends delete for each item."""
        connected_adapter._conversation_item_ids = ["item_1", "item_2"]

        await connected_adapter.reset_conversation()

        assert connected_adapter._ws.send_json.call_count == 2
        calls = connected_adapter._ws.send_json.call_args_list
        assert calls[0][0][0] == {
            "type": "conversation.item.delete",
            "item_id": "item_1"
        }
        assert calls[1][0][0] == {
            "type": "conversation.item.delete",
            "item_id": "item_2"
        }

    @pytest.mark.asyncio
    async def test_reset_empty_is_noop(self, connected_adapter):
        """Reset with no items doesn't send anything."""
        connected_adapter._conversation_item_ids = []

        await connected_adapter.reset_conversation()

        connected_adapter._ws.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_requires_connection(self):
        """Reset raises if not connected."""
        adapter = OpenAIRealtimeAdapter(api_key="test")

        with pytest.raises(Exception):  # RealtimeSessionError
            await adapter.reset_conversation()
```

---

## Implementation Order

| Step | File | Change | Risk |
|------|------|--------|------|
| 1 | `ports/realtime_voice.py` | Add `supports_conversation_reset` | None |
| 2 | `ports/realtime_voice.py` | Add abstract `reset_conversation()` | Breaking* |
| 3 | `adapters/realtime/openai/messages.py` | Add `conversation_item_delete()` | None |
| 4 | `adapters/realtime/openai/adapter.py` | Add `_conversation_item_ids` | None |
| 5 | `adapters/realtime/openai/adapter.py` | Add `_track_conversation_item()` | None |
| 6 | `adapters/realtime/openai/adapter.py` | Update `_receive_loop()` | Low |
| 7 | `adapters/realtime/openai/adapter.py` | Add `reset_conversation()` | None |
| 8 | `adapters/realtime/openai/adapter.py` | Update `connect()` | Low |
| 9 | `adapters/realtime/openai/adapter.py` | Update `disconnect()` | Low |
| 10 | `adapters/realtime/openai/adapter.py` | Update `get_capabilities()` | None |
| 11 | `adapters/realtime/mock/adapter.py` | Add mock implementation | None |
| 12 | `tests/` | Add tests | None |

*Breaking: Adding abstract method requires all implementations to add it. Since we control all implementations (OpenAI, Mock), this is manageable.

---

## Edge Cases Handled

### 1. Duplicate Item IDs

```python
if item_id and item_id not in self._conversation_item_ids:
    self._conversation_item_ids.append(item_id)
```

### 2. Missing Item ID

```python
item_id = item.get("id")
if item_id:  # Only track if ID exists
```

### 3. Delete Failure

```python
try:
    await self._ws.send_json(messages.conversation_item_delete(item_id))
except Exception as e:
    logger.warning("Failed to delete item %s: %s", item_id, e)
# Continue with next item, clear tracking regardless
```

### 4. Reset During Active Response

Application responsibility. Document that `reset_conversation()` should be called when conversation is idle (after RESPONSE_DONE, before next user turn).

### 5. Reconnection

Item IDs are session-scoped. On reconnect, server assigns new IDs. Current tracking becomes stale but harmless (delete will fail silently, tracking cleared on next connect).

---

## Memory Impact

| Scenario | Items | Memory |
|----------|-------|--------|
| Typical session (10 min) | ~50 | ~1.8 KB |
| Long session (1 hour) | ~300 | ~10.8 KB |
| Edge case (1000 items) | 1000 | ~36 KB |

Negligible. No memory management needed.

---

## Validation Checklist

After implementation:

- [ ] `ProviderCapabilities.supports_conversation_reset` exists
- [ ] `RealtimeVoiceAPIPort.reset_conversation()` is abstract
- [ ] `OpenAIRealtimeAdapter` implements `reset_conversation()`
- [ ] `MockRealtimeAdapter` implements `reset_conversation()`
- [ ] Items tracked on `conversation.item.created`
- [ ] Tracking cleared on `connect()`
- [ ] Tracking cleared on `disconnect()`
- [ ] `get_capabilities()` returns `supports_conversation_reset=True`
- [ ] Unit tests pass
- [ ] No type errors (`mypy`)
- [ ] No lint errors

---

## Future Considerations

1. **Bulk Delete API**: If OpenAI adds `session.reset` or `conversation.delete.all`, update implementation to use it instead of per-item deletion.

2. **Item Deletion Events**: Could track `conversation.item.deleted` events to confirm deletion succeeded. Currently fire-and-forget.

3. **Selective Reset**: Could add `reset_conversation(keep_last_n: int)` to preserve recent context. Not needed now.

4. **ContextManager Integration**: The `ContextManager` service can call `port.reset_conversation()` for its Layer 3 (Override) operations.
