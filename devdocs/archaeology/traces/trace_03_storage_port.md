# Trace 03: StoragePort Interactions

The persistence layer for conversation history. Implements the hexagonal "port" pattern with multiple adapters.

---

## Entry Point

**File:** `chatforge/ports/storage.py:47`
**Interface:** `StoragePort` (Abstract Base Class)

**Primary Methods:**
```python
async def save_message(conversation_id, message, user_id=None) -> None
async def get_conversation(conversation_id, limit=50) -> list[MessageRecord]
async def delete_conversation(conversation_id) -> bool
async def cleanup_expired(ttl_minutes=30) -> int
async def list_conversations(user_id=None, limit=100) -> list[ConversationRecord]
```

**Implementations:**
- `InMemoryStorageAdapter` - RAM-based, ephemeral
- `SQLiteStorageAdapter` - File-based persistence

**Callers:**
- Application code (directly)
- FastAPI routes (via adapter injection)
- Background cleanup tasks

---

## Execution Path: save_message

### InMemoryStorageAdapter

```
save_message(conversation_id, message, user_id)
    │
    ├─1─► Acquire asyncio.Lock (thread safety)
    │
    ├─2─► Check if conversation exists
    │     │
    │     ├── [New conversation]
    │     │   ├── Create ConversationRecord
    │     │   │   └── conversation_id, user_id, platform="api",
    │     │   │       created_at=now, updated_at=now
    │     │   └── Initialize empty message list
    │     │
    │     └── [Existing conversation]
    │         ├── Update updated_at timestamp
    │         └── Update user_id if provided
    │
    ├─3─► Append message to _messages[conversation_id]
    │
    ├─4─► Release lock (automatic via async with)
    │
    └─5─► Log: "Saved message to conversation X (total: N)"
```

### SQLiteStorageAdapter

```
save_message(conversation_id, message, user_id)
    │
    ├─1─► _ensure_tables() - Create tables if first call
    │     │
    │     ├── Check _initialized flag
    │     ├── Import aiosqlite (lazy)
    │     │   └── ImportError → raise with install instructions
    │     ├── CREATE TABLE IF NOT EXISTS conversations
    │     ├── CREATE TABLE IF NOT EXISTS messages
    │     └── CREATE INDEX IF NOT EXISTS ...
    │
    ├─2─► Connect to database: aiosqlite.connect(self._db_path)
    │
    ├─3─► UPSERT conversation
    │     INSERT INTO conversations ... ON CONFLICT DO UPDATE SET updated_at
    │
    ├─4─► INSERT message
    │     INSERT INTO messages (conversation_id, role, content, created_at, metadata)
    │
    ├─5─► Commit transaction
    │
    ├─6─► Close connection
    │
    └─7─► Log: "Saved message to conversation X"
```

---

## Execution Path: get_conversation

### InMemoryStorageAdapter

```
get_conversation(conversation_id, limit=50)
    │
    ├─1─► Check if conversation_id in _messages
    │     └── [Not found] → Return []
    │
    ├─2─► Get message list (no lock - read-only dict access)
    │
    ├─3─► Slice to last `limit` messages
    │
    └─4─► Return copy of list (not reference)
```

### SQLiteStorageAdapter

```
get_conversation(conversation_id, limit=50)
    │
    ├─1─► _ensure_tables()
    │
    ├─2─► Connect to database
    │
    ├─3─► SELECT role, content, created_at, metadata
    │     FROM messages
    │     WHERE conversation_id = ?
    │     ORDER BY id DESC  ← Note: descending for LIMIT
    │     LIMIT ?
    │
    ├─4─► Convert rows to MessageRecord objects
    │
    ├─5─► Reverse list (to chronological order)
    │
    └─6─► Return list[MessageRecord]
```

---

## Execution Path: cleanup_expired

```
cleanup_expired(ttl_minutes=30)
    │
    ├─1─► Calculate cutoff: now - ttl_minutes
    │
    ├─2─► [InMemory] Acquire lock
    │     [SQLite] Connect to database
    │
    ├─3─► Find expired: WHERE updated_at < cutoff
    │
    ├─4─► Delete messages for expired conversations
    │
    ├─5─► Delete conversation records
    │
    ├─6─► Log: "Cleaned up N expired conversations"
    │
    └─7─► Return count of deleted conversations
```

---

## Resource Management

### InMemoryStorageAdapter

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| asyncio.Lock | Per-mutating operation | Automatic (async with) | Deadlock if exception in critical section |
| Memory | Grows with usage | Never (until close()) | OOM if too many conversations |

### SQLiteStorageAdapter

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| DB connection | Per-operation | After each operation | Connection leak if not closed |
| File handle | Via aiosqlite | Automatic | File locked if crash |
| Disk space | Per message | Never automatic | Disk full |

**Note:** SQLite adapter opens/closes connection per operation. No connection pooling.

---

## Error Path

```
InMemoryStorageAdapter:
    │
    └── Minimal - pure Python dict operations
        └── Only KeyError if dict corrupted (shouldn't happen)

SQLiteStorageAdapter:
    │
    ├── ImportError (aiosqlite missing)
    │   └── Raise with install instructions
    │
    ├── sqlite3.OperationalError (DB locked, disk full)
    │   └── Bubbles up - no handling
    │
    └── aiosqlite.Error (any DB error)
        └── Bubbles up - no handling
```

**No retry logic.** Errors bubble up to caller.

---

## Performance Characteristics

### InMemoryStorageAdapter

| Operation | Complexity | Notes |
|-----------|------------|-------|
| save_message | O(1) | Dict append |
| get_conversation | O(limit) | List slice + copy |
| cleanup_expired | O(n) | Scan all conversations |
| list_conversations | O(n log n) | Sort by updated_at |

### SQLiteStorageAdapter

| Operation | Complexity | Notes |
|-----------|------------|-------|
| save_message | O(log n) | Index lookup + insert |
| get_conversation | O(log n + limit) | Index scan |
| cleanup_expired | O(n) | Full scan on updated_at |
| list_conversations | O(n log n) | Sort + limit |

**SQLite bottleneck:** Connection per operation. No pooling means connection setup overhead per call.

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "Saved message to conversation X" | adapter | save_message |
| Log: "Deleted conversation X" | adapter | delete_conversation |
| Log: "Cleaned up N expired conversations" | adapter | cleanup_expired |
| File creation | disk | SQLite first write |
| File modification | disk | SQLite every write |

---

## Why This Design

**Async interface:**
- All methods are async
- Ready for async DB drivers
- Consistent with rest of codebase

**Per-operation connection (SQLite):**
- Simple - no pool management
- SQLite is local, connection overhead is low
- Avoids connection lifetime issues

**Lock in InMemory:**
- asyncio.Lock for thread safety
- Protects dict mutations
- Reads don't need lock (dict is thread-safe for reads)

**TTL-based cleanup:**
- Simple age-based expiration
- No complex retention policies
- Caller must schedule cleanup calls

---

## What Feels Incomplete

1. **No pagination for list_conversations:**
   - Only `limit` parameter
   - No offset or cursor
   - Can't page through results

2. **No transaction support:**
   - Each operation is atomic
   - Can't do multi-step transactions
   - save_message + update_conversation not atomic

3. **No connection pooling (SQLite):**
   - Connection per operation
   - Overhead for high-throughput
   - Should use pool for production

4. **Extended interface mostly NotImplementedError:**
   - `create_chat`, `log_tool_call`, `start_agent_run` defined but not implemented
   - Only legacy interface works in adapters
   - Dead code in port definition

5. **No search/query capability:**
   - Only get by conversation_id
   - No full-text search
   - No filtering by content

---

## What Feels Vulnerable

1. **InMemory has no size limit:**
   - Grows unbounded
   - No eviction policy
   - Will OOM eventually

2. **SQLite file permissions:**
   - Created with default umask
   - May be world-readable
   - Contains conversation content

3. **No encryption at rest:**
   - SQLite stores plaintext
   - InMemory is plaintext in RAM
   - PII in conversations exposed

4. **cleanup_expired is caller's responsibility:**
   - If caller forgets, data grows forever
   - No automatic background cleanup
   - Should have scheduled task option

5. **Metadata stored as JSON string:**
   - Can't query metadata fields
   - No schema validation
   - Corrupt JSON breaks retrieval

---

## What Feels Bad Design

1. **setup() must be called manually:**
   - Easy to forget
   - Should be automatic on first use
   - SQLite does this right, InMemory doesn't need it

2. **Two interface layers (legacy + extended):**
   - Confusing which to use
   - Extended methods raise NotImplementedError
   - Should be single coherent interface

3. **ConversationRecord vs ChatRecord:**
   - Legacy alias creates confusion
   - Two names for same thing
   - Should pick one

4. **get_conversation returns list, not conversation:**
   - Name suggests getting conversation object
   - Actually returns messages
   - Should be `get_messages()`

5. **No type safety for metadata:**
   - `dict[str, Any]` is too loose
   - No schema for expected keys
   - Easy to store invalid data
