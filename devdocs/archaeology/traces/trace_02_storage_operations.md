# Trace 02: Storage Operations

How conversation data is persisted and retrieved through the StoragePort interface.

---

## Entry Point

**Location:** `ports/storage.py:47` - `StoragePort` abstract class

**Trigger:** Any component needing conversation persistence:
- FastAPI routes saving messages
- Cleanup service deleting old data
- Application code querying history

**Interface Methods:**
```python
# Core operations (required)
save_message(conversation_id, message, user_id) → None
get_conversation(conversation_id, limit) → list[MessageRecord]
get_conversation_metadata(conversation_id) → ConversationRecord | None
delete_conversation(conversation_id) → bool
cleanup_expired(ttl_minutes) → int
list_conversations(user_id, limit) → list[ConversationRecord]

# Lifecycle (optional, can be no-op)
setup() → None
close() → None
health_check() → bool

# Extended interface (optional, for observability)
create_chat(...) → ChatRecord
log_tool_call(...) → ToolCallRecord
start_agent_run(...) → AgentRunRecord
# ... and more
```

---

## Execution Path

### Path A: Save Message (InMemoryStorageAdapter)

```
save_message(conversation_id, message, user_id)
├── Acquire asyncio.Lock (thread safety)
├── Check if conversation exists
│   ├── EXISTS: Update updated_at, optionally update user_id
│   └── NOT EXISTS: Create ConversationRecord, init empty message list
├── Append message to messages[conversation_id]
├── Release lock
└── Log debug message with count
```

**Data flow:**
```python
# Input
conversation_id: "conv-abc123"
message: MessageRecord(content="Hello", role="user", created_at=datetime, metadata={})
user_id: "user@example.com"

# Internal storage
self._conversations = {
    "conv-abc123": ConversationRecord(
        conversation_id="conv-abc123",
        user_id="user@example.com",
        platform="api",
        created_at=datetime(...),
        updated_at=datetime(...),  # Updated on each message
    )
}
self._messages = {
    "conv-abc123": [MessageRecord(...), MessageRecord(...), ...]
}
```

### Path B: Save Message (SQLiteStorageAdapter)

```
save_message(conversation_id, message, user_id)
├── _ensure_tables() - Lazy table creation
│   ├── Check self._initialized flag
│   ├── If not initialized:
│   │   ├── Import aiosqlite (lazy)
│   │   ├── Connect to database
│   │   ├── CREATE TABLE IF NOT EXISTS conversations
│   │   ├── CREATE TABLE IF NOT EXISTS messages
│   │   ├── CREATE INDEX IF NOT EXISTS (2 indexes)
│   │   ├── COMMIT
│   │   └── Set self._initialized = True
│   └── If initialized: return immediately
├── Connect to database
├── INSERT OR UPDATE conversation (upsert)
├── INSERT message
├── COMMIT
├── Close connection
└── Log debug message
```

**SQL executed:**
```sql
-- Conversation upsert
INSERT INTO conversations (conversation_id, user_id, platform, created_at, updated_at, metadata)
VALUES (?, ?, 'api', ?, ?, '{}')
ON CONFLICT(conversation_id) DO UPDATE SET
    updated_at = excluded.updated_at,
    user_id = COALESCE(excluded.user_id, conversations.user_id)

-- Message insert
INSERT INTO messages (conversation_id, role, content, created_at, metadata)
VALUES (?, ?, ?, ?, ?)
```

### Path C: Get Conversation

```
get_conversation(conversation_id, limit=50)
├── InMemory:
│   ├── Check if conversation_id in self._messages
│   ├── Return empty list if not found
│   ├── Get messages[-limit:] (most recent)
│   └── Return copy of list
├── SQLite:
│   ├── _ensure_tables()
│   ├── SELECT ... ORDER BY id DESC LIMIT ?
│   ├── Build MessageRecord objects from rows
│   ├── Reverse list (to get chronological order)
│   └── Return list
```

**Important detail:** Messages are fetched in reverse order (newest first) then reversed to maintain oldest-first order for the agent.

### Path D: Cleanup Expired

```
cleanup_expired(ttl_minutes=30)
├── Calculate cutoff = now - ttl_minutes
├── InMemory:
│   ├── Acquire lock
│   ├── Find all conversations where updated_at < cutoff
│   ├── Delete from both dicts
│   ├── Release lock
│   └── Return count
├── SQLite:
│   ├── SELECT conversation_ids WHERE updated_at < cutoff
│   ├── DELETE FROM messages WHERE conversation_id IN (...)
│   ├── DELETE FROM conversations WHERE conversation_id IN (...)
│   ├── COMMIT
│   └── Return count
```

---

## Resource Management

### InMemoryStorageAdapter
- **Memory:** Unbounded growth until cleanup runs
- **Lock:** Single `asyncio.Lock` for all operations
- **Cleanup:** No automatic cleanup; depends on external caller

### SQLiteStorageAdapter
- **Connections:** Opened and closed per operation
- **No connection pooling:** Each call is independent
- **File locks:** SQLite handles concurrent access via file locking
- **Indexes:** Created on first use for query performance

### Connection Lifecycle
```python
# SQLite - per-operation pattern
async with aiosqlite.connect(self._db_path) as db:
    # Use connection
    await db.commit()
# Connection automatically closed
```

---

## Error Path

### InMemoryStorageAdapter
```
# Most operations cannot fail (dict operations)
# Lock acquisition could theoretically deadlock
# No explicit error handling - exceptions propagate
```

### SQLiteStorageAdapter
```
Import Error:
└── aiosqlite not installed
    → ImportError with helpful message
    → "Install with: pip install chatforge[sqlite]"

Connection Error:
└── Database file inaccessible
    → aiosqlite raises exception
    → Exception propagates to caller

Table Creation Error:
└── Disk full, permissions, etc.
    → SQL error propagates
    → _initialized stays False
    → Next operation retries table creation

Query Error:
└── Malformed data, type errors
    → Exception propagates
    → Transaction rolled back (implicit)
```

### Health Check
```python
async def health_check(self) -> bool:
    try:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"SQLite health check failed: {e}")
        return False
```

---

## Performance Characteristics

### InMemoryStorageAdapter
| Operation | Complexity | Notes |
|-----------|------------|-------|
| save_message | O(1) | Dict append |
| get_conversation | O(n) | Copy + slice |
| cleanup_expired | O(n) | Iterate all conversations |
| list_conversations | O(n log n) | Sort by updated_at |

### SQLiteStorageAdapter
| Operation | Complexity | Notes |
|-----------|------------|-------|
| save_message | O(log n) | Index update |
| get_conversation | O(log n) | Index scan |
| cleanup_expired | O(k) | k = expired count |
| list_conversations | O(log n) | Index scan |

### Bottlenecks
- **InMemory:** Lock contention under high concurrency
- **SQLite:** File I/O, single-writer limitation
- **Both:** Message serialization/deserialization

---

## Observable Effects

### On save_message
- Conversation record created or updated
- Message appended to history
- updated_at timestamp refreshed
- `DEBUG` log: "Saved message to conversation {id}"

### On cleanup_expired
- Expired conversations removed
- Associated messages removed
- `INFO` log: "Cleaned up {n} expired conversations"

### On delete_conversation
- Conversation and all messages removed
- `INFO` log: "Deleted conversation {id}"

---

## Why This Design

### Lazy Table Creation
**Choice:** Tables created on first operation, not constructor

**Rationale:**
- Avoids blocking import/initialization
- Allows adapter creation before async context available
- Handles missing aiosqlite gracefully

**Trade-off:**
- First operation is slower
- _ensure_tables called on every operation (though cached)

### Per-Operation Connections
**Choice:** Open/close connection for each database operation

**Rationale:**
- Simple implementation
- No connection lifecycle management
- SQLite handles this efficiently

**Trade-off:**
- Connection overhead per operation
- No connection pooling benefits
- Cannot use transactions across operations

### Lock on InMemory
**Choice:** Single asyncio.Lock for all operations

**Rationale:**
- Prevents race conditions on dict operations
- Simple to reason about
- Correct behavior guaranteed

**Trade-off:**
- Serializes all writes
- Single point of contention
- Could use per-conversation locks for better concurrency

### Messages Stored Separately
**Choice:** `_conversations` and `_messages` are separate dicts

**Rationale:**
- Metadata retrieval doesn't load messages
- Can limit message count without scanning
- Clear separation of concerns

**Trade-off:**
- Must keep both in sync
- Delete requires two operations

---

## What Feels Incomplete

1. **No pagination support**
   - `list_conversations` returns all up to limit
   - No cursor/offset for paginating large result sets
   - Memory issues with many conversations

2. **No message update/delete**
   - Can delete entire conversation
   - Cannot edit or remove individual messages
   - No soft delete for messages

3. **Extended interface mostly unimplemented**
   - `create_chat`, `log_tool_call`, `start_agent_run` raise NotImplementedError
   - Designed for observability but not wired up
   - SQLAlchemy adapter may implement these

4. **No migration support**
   - Schema changes require manual migration
   - No versioning of table structure
   - Adding columns would break existing data

---

## What Feels Vulnerable

1. **No input validation**
   - conversation_id could be any string (including SQL injection vectors in metadata)
   - Message content not sanitized
   - Trusts caller completely

2. **Unbounded memory growth (InMemory)**
   - No limit on conversation count
   - No limit on messages per conversation
   - Only cleanup prevents OOM

3. **Race condition window (SQLite)**
   - Check-then-act pattern in some operations
   - Two concurrent saves could both think they're creating conversation
   - SQLite UPSERT helps but not bulletproof

4. **Data loss on crash (InMemory)**
   - All data lost on process restart
   - No persistence mechanism
   - Only suitable for testing/development

---

## What Feels Like Bad Design

1. **Inconsistent return types**
   ```python
   get_conversation() → list[MessageRecord]  # List of messages
   get_conversation_metadata() → ConversationRecord | None  # Metadata only
   ```
   - Naming suggests metadata is separate concern
   - But `get_conversation` name doesn't indicate it returns messages
   - Could be `get_messages` for clarity

2. **Magic number for limit**
   ```python
   async def get_conversation(self, conversation_id: str, limit: int = 50)
   ```
   - Default limit of 50 hardcoded
   - Not configurable via settings
   - May not be appropriate for all use cases

3. **TTL in minutes**
   ```python
   async def cleanup_expired(self, ttl_minutes: int = 30)
   ```
   - Minutes as unit is arbitrary
   - 30 minute default seems too aggressive for production
   - Inconsistent with other time units in Python (usually seconds)

4. **No bulk operations**
   - save_message handles one message at a time
   - Saving user message + response = 2 operations
   - Could have save_messages for batch operations

5. **Metadata as JSON string in SQLite**
   ```python
   metadata=json.dumps(message.metadata or {})
   ```
   - Cannot query by metadata fields
   - Must deserialize on every read
   - No schema enforcement
