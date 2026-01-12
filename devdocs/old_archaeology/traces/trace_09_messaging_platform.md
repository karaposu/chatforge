# Trace 09: Messaging Platform Integration

How Chatforge integrates with external messaging platforms like Slack, Teams, and Discord.

---

## Entry Point

**Location:** `ports/messaging_platform_integration.py:100` - `MessagingPlatformIntegrationPort` abstract class

**Trigger:** Agent needs to interact with external messaging platform:
- Fetch conversation history from Slack thread
- Send response to Teams channel
- Download file attachment from Discord
- Resolve user email from platform user ID

**Key Methods:**
```python
get_conversation_history(context) → list[Message]
send_message(context, message) → None
send_typing_indicator(context) → None
download_file(file, context) → bytes
get_user_email(user_id) → str | None
get_user_display_name(user_id) → str
```

**Supporting Types:**
```python
ConversationContext  # Platform-agnostic conversation identifier
FileAttachment      # File metadata with download URL
Message            # Text content with role and attachments
```

---

## Execution Path

### Path A: Agent with Messaging Port (in ReActAgent)

```
ReActAgent.__init__(..., messaging_port=slack_adapter)
├── Store messaging_port
├── Enable async methods:
│   ├── get_conversation_history_async()
│   ├── send_response_async()
│   ├── send_typing_indicator_async()
│   └── get_user_email_async()
```

### Path B: Get Conversation History

```
ReActAgent.get_conversation_history_async(context)
├── Check if messaging_port exists
│   └── if not: raise RuntimeError("No messaging port configured")
├── Call await self.messaging_port.get_conversation_history(context)
├── Convert Message objects to dicts:
│   └── [{"role": msg.role, "content": msg.content} for msg in messages]
├── Return list of dicts
```

**Example implementation (NullMessagingAdapter):**
```python
async def get_conversation_history(self, context: ConversationContext) -> list[Message]:
    return []  # No history
```

### Path C: Send Response

```
ReActAgent.send_response_async(context, message)
├── Check if messaging_port exists
├── Call await self.messaging_port.send_message(context, message)
├── Log debug with message preview
```

### Path D: Download File

```
messaging_port.download_file(file, context)
├── Use file.download_url to fetch content
├── May need context for authentication headers
├── Return raw bytes
```

**Platform-specific implementation would:**
- Slack: Use `files.sharedPublicURL` or `files.info` API
- Teams: Use Microsoft Graph API
- Discord: Use CDN URL with bot token

### Path E: Resolve User Email

```
messaging_port.get_user_email(user_id)
├── Call platform user lookup API
├── Return email or None
```

**Platform-specific:**
- Slack: `users.info` API → `user.profile.email`
- Teams: Microsoft Graph → `/users/{id}`
- Discord: Not typically available (privacy)

---

## Resource Management

### ConversationContext
```python
@dataclass
class ConversationContext:
    conversation_id: str        # Thread ID, channel ID, etc.
    user_id: str               # Platform user ID
    user_email: str | None     # If already known
    platform: str              # "slack", "teams", "discord", "api"
    metadata: dict[str, Any]   # Platform-specific extras
```

### FileAttachment
```python
@dataclass
class FileAttachment:
    file_id: str           # Platform file ID
    filename: str          # Original filename
    mimetype: str          # MIME type
    download_url: str      # URL to fetch content
    size_bytes: int = 0    # File size if known
```

**Properties:**
```python
file.is_image  # mimetype.startswith("image/")
file.is_text   # mimetype.startswith("text/") or JSON/XML
```

### Message
```python
@dataclass
class Message:
    content: str                        # Text content
    role: str                           # "user" or "assistant"
    attachments: list[FileAttachment]   # Files in message
```

---

## Error Path

### No Messaging Port Configured
```python
async def get_conversation_history_async(self, context):
    if not self.messaging_port:
        raise RuntimeError(
            "No messaging port configured. "
            "Initialize ReActAgent with messaging_port parameter."
        )
```

### Platform API Errors
```
# Handled by adapter implementation
# Should wrap in AdapterError with context
raise AdapterError(
    "Failed to fetch conversation history",
    original_error=slack_error,
    service_name="Slack"
)
```

### File Download Errors
```
# Network errors, authentication failures
# Returns empty bytes in NullAdapter
# Real adapters should raise or return error
```

---

## Performance Characteristics

### API Call Latencies (typical)
| Operation | Slack | Teams | Discord |
|-----------|-------|-------|---------|
| Get history | 100-500ms | 200-800ms | 100-400ms |
| Send message | 50-200ms | 100-400ms | 50-200ms |
| Download file | 100ms-10s | 100ms-10s | 100ms-5s |
| Get user info | 50-200ms | 100-400ms | 50-200ms |

### Rate Limits
- **Slack:** 1 request/second for most APIs
- **Teams:** 30-60 requests/minute
- **Discord:** Varies by endpoint, burst limits

### Caching Considerations
- User info: Cache for session duration
- History: Fetch fresh each time
- Files: Cache after download

---

## Observable Effects

### On get_conversation_history
- Platform API called
- Messages returned in chronological order
- Attachments included in messages

### On send_message
- Message appears in platform
- Typing indicator cleared
- Delivery confirmation (platform-specific)

### On download_file
- File content fetched
- May be cached by implementation
- Bytes returned

### Logging (in ReActAgent)
```python
logger.debug(f"Sent response via messaging port: {message[:100]}...")
```

---

## Why This Design

### Abstract Port Interface
**Choice:** Define abstract interface, not concrete implementations

**Rationale:**
- Platform-agnostic core logic
- Easy to add new platforms
- Testable with NullAdapter

**Trade-off:**
- Must implement adapter per platform
- Common patterns not shared

### Context Object
**Choice:** ConversationContext bundles all identifiers

**Rationale:**
- Single parameter to pass around
- Platform-specific metadata in one place
- Easy to extend

**Trade-off:**
- More verbose than raw IDs
- Must construct for each call

### Separate from StoragePort
**Choice:** MessagingPlatformIntegrationPort is distinct from StoragePort

**Rationale:**
- Different concerns: external platform vs internal storage
- Can use both or neither
- Clear responsibilities

**Trade-off:**
- History might need syncing between them
- Two sources of truth

### Optional in Agent
**Choice:** messaging_port is optional in ReActAgent

**Rationale:**
- Not all use cases need platform integration
- Direct API usage doesn't need messaging port
- Simpler for basic usage

**Trade-off:**
- Runtime errors if used without port
- Must check `has_messaging_port()`

---

## What Feels Incomplete

1. **No concrete implementations**
   - Only NullMessagingAdapter exists
   - No Slack, Teams, or Discord adapters in codebase
   - Must build from scratch

2. **No webhook handling**
   - Interface assumes polling/calling out
   - No incoming message handling
   - Webhook setup not addressed

3. **No message formatting**
   - send_message takes plain string
   - No rich formatting (bold, links, etc.)
   - Platform-specific formatting not supported

4. **No reaction handling**
   - Can't add emoji reactions
   - Can't read reactions
   - Common in chat platforms

5. **No thread management**
   - context.conversation_id is flat
   - No explicit thread creation
   - Relies on platform behavior

---

## What Feels Vulnerable

1. **No authentication abstraction**
   - Port doesn't define auth pattern
   - Each adapter handles differently
   - Token refresh not standardized

2. **download_url exposure**
   ```python
   file.download_url: str  # Could be time-limited token URL
   ```
   - URLs may expire
   - Should fetch immediately
   - Could leak if logged

3. **No rate limit handling**
   - Port doesn't define backoff
   - Adapters must implement
   - Easy to hit platform limits

4. **User email availability**
   ```python
   async def get_user_email(self, user_id: str) -> str | None:
   ```
   - May not be available (Discord)
   - Privacy settings may block
   - Code may assume it's present

5. **Platform field is string**
   ```python
   platform: str = "unknown"
   ```
   - No enum or validation
   - Typos possible
   - Should be enum

---

## What Feels Like Bad Design

1. **Role is string not enum**
   ```python
   role: str  # "user" | "assistant"
   ```
   - No validation
   - Could be "USER", "bot", anything
   - Should be enum

2. **FileAttachment size default 0**
   ```python
   size_bytes: int = 0  # Unknown size
   ```
   - 0 is ambiguous (unknown vs empty file)
   - Should be None for unknown
   - Or -1 sentinel

3. **get_user_display_name returns user_id**
   ```python
   # NullMessagingAdapter
   async def get_user_display_name(self, user_id: str) -> str:
       return user_id  # Fallback
   ```
   - Silent fallback
   - Caller doesn't know if real name
   - Could confuse users

4. **Context.get_metadata returns Any**
   ```python
   def get_metadata(self, key: str, default: Any = None) -> Any:
       return self.metadata.get(key, default)
   ```
   - No type safety
   - Caller must cast
   - Could use generics

5. **Attachment list is mutable default**
   ```python
   @dataclass
   class Message:
       attachments: list[FileAttachment] = field(default_factory=list)
   ```
   - Correct with field(default_factory=...)
   - But could accidentally share if not careful

6. **No correlation IDs**
   - Messages don't have unique IDs
   - Can't reference specific message later
   - Threading relies on platform behavior
