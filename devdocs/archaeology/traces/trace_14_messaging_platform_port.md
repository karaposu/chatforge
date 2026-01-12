# Trace 14: MessagingPlatformIntegrationPort

Abstract interface for embedding chatforge into external messaging platforms (Slack, Teams, Discord).

---

## Entry Point

**File:** `chatforge/ports/messaging_platform_integration.py:100`
**Interface:** `MessagingPlatformIntegrationPort` (Abstract Base Class)

**Implementation:**
- `chatforge/adapters/null.py:NullMessagingAdapter` - No-op for testing
- (Real adapters like Slack would be external)

**Primary Methods:**
```python
async def get_conversation_history(context) -> list[Message]
async def send_message(context, message) -> None
async def send_typing_indicator(context) -> None
async def download_file(file, context) -> bytes
async def get_user_email(user_id) -> str | None
async def get_user_display_name(user_id) -> str
```

**Callers:**
- Platform-specific bot implementations
- Webhook handlers
- Event processors

---

## Execution Path: Message Processing Pipeline

```
Platform Event (e.g., Slack message)
    │
    ├─► Platform adapter receives event
    │   └── Slack: slack_events_api webhook
    │
    ├─► Build ConversationContext
    │   │
    │   └── ConversationContext(
    │           conversation_id="C123",  # Channel/thread ID
    │           user_id="U456",           # Platform user ID
    │           user_email="user@co.com", # If available
    │           platform="slack",
    │           metadata={                 # Platform extras
    │               "channel_name": "support",
    │               "thread_ts": "1234.5678",
    │           },
    │       )
    │
    ├─► Get conversation history
    │   │
    │   └── history = await port.get_conversation_history(context)
    │       │
    │       └── Returns list[Message] from platform
    │           └── Message(content="...", role="user"|"assistant")
    │
    ├─► Process attachments (if any)
    │   │
    │   └── for attachment in message.attachments:
    │       │
    │       └── file_bytes = await port.download_file(attachment, context)
    │           │
    │           └── Downloads from platform with proper auth
    │
    ├─► Send typing indicator
    │   │
    │   └── await port.send_typing_indicator(context)
    │       └── Shows "Agent is typing..." in platform
    │
    ├─► Process with agent
    │   │
    │   └── response = agent.process_message(user_message, history)
    │
    └─► Send response
        │
        └── await port.send_message(context, response)
            └── Delivers message back to platform
```

---

## Data Types

```python
@dataclass
class ConversationContext:
    conversation_id: str      # Platform thread/channel ID
    user_id: str              # Platform user ID
    user_email: str | None    # User email if available
    platform: str             # "slack", "teams", "discord", "api"
    metadata: dict[str, Any]  # Platform-specific extras

@dataclass
class FileAttachment:
    file_id: str          # Platform file ID
    filename: str         # Original filename
    mimetype: str         # MIME type
    download_url: str     # URL to download
    size_bytes: int       # File size

    @property
    def is_image(self) -> bool  # Check if image
    @property
    def is_text(self) -> bool   # Check if text file

@dataclass
class Message:
    content: str                        # Message text
    role: str                           # "user" | "assistant"
    attachments: list[FileAttachment]   # File attachments
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Platform API connection | Per-request | After response | Timeout |
| File download stream | Per-download | After read | Incomplete download |
| Typing indicator | send_typing_indicator | Auto-expires | No cleanup needed |

**Platform considerations:**
- Rate limits per platform
- Authentication tokens
- Webhook timeouts

---

## Error Path

```
Platform errors (abstract - implementations vary):
    │
    ├── get_conversation_history
    │   ├── Platform API error → propagates
    │   ├── Auth failure → propagates
    │   └── Rate limit → propagates
    │
    ├── send_message
    │   ├── Message too long → platform-specific
    │   ├── Channel not found → propagates
    │   └── Permissions error → propagates
    │
    ├── download_file
    │   ├── File not found → propagates
    │   ├── Access denied → propagates
    │   └── Timeout → propagates
    │
    └── send_typing_indicator
        └── Usually fire-and-forget (no error handling)
```

---

## Performance Characteristics

| Operation | Typical Latency | Notes |
|-----------|-----------------|-------|
| get_conversation_history | 100-500ms | API call |
| send_message | 50-200ms | API call |
| send_typing_indicator | 20-50ms | Async fire |
| download_file | 100ms-10s | File size dependent |
| get_user_email | 50-200ms | May need user lookup |

**Bottleneck:** External API calls. Consider caching user info.

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Message sent to platform | External platform | send_message |
| Typing indicator shown | External platform | send_typing_indicator |
| File download | External platform | download_file |
| API rate consumption | External platform | All methods |

---

## Why This Design

**Conversation context abstraction:**
- Platform-agnostic identity
- Metadata for platform specifics
- Consistent API

**Separate from StoragePort:**
- StoragePort = our persistence
- MessagingPort = platform's data
- May want both simultaneously

**Async all methods:**
- Platform APIs are network calls
- Non-blocking
- Consistent with rest of system

**FileAttachment with helpers:**
- `is_image`, `is_text` convenience
- Common checks
- Platform-agnostic

---

## What Feels Incomplete

1. **No reaction/emoji support:**
   - Can't add reactions
   - Can't read reactions
   - Common platform feature

2. **No thread management:**
   - Can't create threads
   - Can't reply in thread
   - Metadata workaround

3. **No rich formatting:**
   - Plain text only
   - No blocks, cards, embeds
   - Platform-specific markup needed

4. **No message editing:**
   - Can't update sent message
   - No edit/delete
   - Common need

5. **No presence/status:**
   - Can't check if user online
   - Can't set bot status
   - Useful for UX

---

## What Feels Vulnerable

1. **download_url in FileAttachment:**
   - URL may expire
   - Needs auth headers
   - Time-sensitive

2. **user_id is opaque:**
   - Platform-specific format
   - Can't validate
   - May contain PII

3. **metadata is untyped:**
   - dict[str, Any]
   - Easy to misuse
   - Platform-specific keys not documented

4. **No rate limit handling:**
   - Up to caller
   - Easy to hit limits
   - Should have built-in throttling

5. **get_conversation_history unbounded:**
   - No pagination in interface
   - Could return huge history
   - Memory issues

---

## What Feels Bad Design

1. **Port naming is verbose:**
   - `MessagingPlatformIntegrationPort`
   - Could be `MessagingPort`
   - Unwieldy

2. **ConversationContext vs context dict:**
   - Sometimes dataclass
   - Sometimes dict
   - Inconsistent

3. **get_user_email returns str | None:**
   - But get_user_display_name returns str
   - Falls back to user_id
   - Inconsistent null handling

4. **No batch operations:**
   - One message at a time
   - Inefficient for bulk
   - Should have batch methods

5. **Method naming inconsistent:**
   - `get_conversation_history` vs `send_message`
   - get_ prefix inconsistent
   - Should be consistent style
