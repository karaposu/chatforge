# S2S Stateless Mode: Is It Possible?

## The Question

> Can we disable S2S statefulness to have full context control per turn?

## The Answer

**Yes.** Use `conversation.item.delete` to clear history before injecting fresh context.

---

## How S2S Statefulness Works

```
Session Start
    ├── System prompt set
    ├── Conversation history: []
    │
Turn 1:
    ├── User: "My name is Alice"
    ├── AI: "Nice to meet you, Alice!"
    ├── History: [user: "My name...", ai: "Nice to..."]
    │
Turn 2:
    ├── User: "What's my name?"
    ├── AI: "Your name is Alice."  ← AI remembers from history
    │
Turn N:
    └── History keeps growing...
```

**AI context = system_prompt + entire conversation history**

---

## The Solution: Conversation Item Deletion

Every piece of conversation is an "item" with a unique ID. Delete all items = empty history.

### How Items Are Created

| Action | Creates Item |
|--------|--------------|
| User speaks → VAD commits | `message` (input_audio) |
| `add_text_item()` | `message` (input_text) |
| AI responds | `message` (output) |
| AI calls tool | `function_call` |
| Tool result sent | `function_call_output` |

### Tracking Items

Every `conversation.item.created` event contains the item ID:

```json
{
  "type": "conversation.item.created",
  "item": {
    "id": "item_ABC123",
    "type": "message",
    "role": "user"
  }
}
```

### Deleting Items

```json
{
  "type": "conversation.item.delete",
  "item_id": "item_ABC123"
}
```

Server responds with `conversation.item.deleted`.

---

## Implementation

Item tracking belongs in the **adapter layer** (OpenAIRealtimeAdapter), not ContextManager.

### Port Interface

```python
class RealtimeVoiceAPIPort(ABC):
    @abstractmethod
    async def reset_conversation(self) -> None:
        """Clear conversation history."""
        ...

@dataclass
class ProviderCapabilities:
    supports_conversation_reset: bool = False
```

### Adapter Implementation

```python
class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, ...):
        self._conversation_item_ids: list[str] = []

    def _track_conversation_item(self, raw_event: dict) -> None:
        """Track item ID from conversation.item.created events."""
        if raw_event.get("type") != "conversation.item.created":
            return
        item_id = raw_event.get("item", {}).get("id")
        if item_id:
            self._conversation_item_ids.append(item_id)

    async def reset_conversation(self) -> None:
        """Delete all tracked items to reset history."""
        for item_id in self._conversation_item_ids:
            await self._ws.send_json({
                "type": "conversation.item.delete",
                "item_id": item_id
            })
        self._conversation_item_ids.clear()

    async def connect(self, config):
        self._conversation_item_ids.clear()  # Clear stale tracking
        # ... connect logic

    async def disconnect(self):
        self._conversation_item_ids.clear()  # Cleanup
        # ... disconnect logic
```

### Usage

```python
# Reset before injecting fresh context
await port.reset_conversation()
await port.add_text_item("[Fresh context here]")
await port.create_response()
```

---

## Verification

Community confirmed working (OpenAI forum, Nov 2024):

> "All I needed is to record every conv item created and delete all at the end of each turn."

Key findings:
- Works for BOTH text and audio items
- `conversation.item.created` event returns item_id when audio is committed
- Prompt caching still applies (cost mitigation)

---

## Characteristics

| Aspect | Detail |
|--------|--------|
| **Reliability** | High - true deletion, not advisory |
| **Latency** | Low - no reconnection needed |
| **UX Impact** | None - session stays connected |
| **Complexity** | Medium - must track all item IDs |
| **Memory** | Negligible (~36 bytes per item) |

---

## When to Use

1. **Testing** - Inject exact context, verify exact response
2. **Scene transitions** - Game room changes, new scenario
3. **Security** - Prevent context leakage
4. **Debugging** - Reproduce specific situations

---

## Limitations

1. **No bulk delete** - Must delete items one by one
2. **Race conditions** - Don't reset during active response
3. **No `session.reset`** - Community requested, not yet available

---

## Future

OpenAI may add:

```python
# Ideal API (not yet available)
await realtime.reset_conversation()  # Native bulk reset

# Or
await realtime.connect(VoiceSessionConfig(
    context_mode="per_turn"  # vs "cumulative"
))
```

Until then, item deletion is the solution.

---

## Summary

**Q: Can we disable S2S statefulness?**

**A: Yes.** Track conversation item IDs, delete them all when you want fresh context. Implementation belongs in the adapter layer with `reset_conversation()` method exposed via port interface.

See: `devdocs/enhancements/openairealtimeadapter/step_by_step_implementation_for_in_memory_item_tracking.md`
