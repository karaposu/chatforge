# StoragePort Extension Methods for Profiling Data Extraction

## Overview

These 6 methods extend the existing `StoragePort` interface to support profiling data extraction. They follow the same pattern as existing extended interface methods (optional, raise `NotImplementedError` by default).

---

## Method 1: `create_extraction_run`

```python
async def create_extraction_run(
    self,
    run: ProfilingDataExtractionRun,
) -> ProfilingDataExtractionRun:
```

**Purpose:** Start tracking a new extraction operation.

**When called:** At the beginning of an extraction, before processing any messages.

**Parameters:**

| Param | Why |
|-------|-----|
| `run` | Full dataclass with all initial values (user_id, scope, config, etc.) |

**Why full dataclass instead of individual params?**
- Cleaner API - one object vs many params
- Caller sets what they know, defaults handle the rest
- Easy to extend without changing signature

**Returns:** Same record with `id` populated by the database.

**Example flow:**
```python
run = ProfilingDataExtractionRun(
    user_id=user_id,
    chat_id=chat_id,  # or None for all user's chats
    config={"dimensions": ["core_identity", "preferences"]},
    status="running",
)
run = await storage.create_extraction_run(run)
# run.id is now set
```

---

## Method 2: `update_extraction_run`

```python
async def update_extraction_run(
    self,
    run_id: str | int,
    updates: dict[str, Any],
) -> ProfilingDataExtractionRun:
```

**Purpose:** Update run as it progresses (status, metrics, errors).

**When called:**
- When extraction starts processing → `status = "running"`
- When extraction completes → `status = "completed"`, `completed_at`, `duration_ms`
- When extraction fails → `status = "failed"`, `error`
- Periodically to update `message_count`

**Parameters:**

| Param | Why |
|-------|-----|
| `run_id` | Identify which run to update |
| `updates` | Dict of fields to update (partial update) |

**Why dict instead of full dataclass?**
- Partial updates - only change what's needed
- Avoids read-modify-write pattern
- Clearer intent - "update these specific fields"

**Returns:** Updated record with all current values.

**Example flow:**
```python
# Mark as running
await storage.update_extraction_run(run.id, {
    "status": "running",
    "started_at": datetime.utcnow(),
})

# Mark as completed
await storage.update_extraction_run(run.id, {
    "status": "completed",
    "completed_at": datetime.utcnow(),
    "message_count": 47,
    "duration_ms": 3200,
})
```

---

## Method 3: `get_extraction_run`

```python
async def get_extraction_run(
    self,
    run_id: str | int,
) -> ProfilingDataExtractionRun | None:
```

**Purpose:** Retrieve a run by ID.

**When called:**
- Check status of an extraction
- Resume after failure
- Display run details to user

**Parameters:**

| Param | Why |
|-------|-----|
| `run_id` | The ID to look up |

**Returns:** The run record, or `None` if not found.

**Example flow:**
```python
run = await storage.get_extraction_run(run_id)
if run is None:
    raise NotFoundError(f"Run {run_id} not found")
if run.status == "failed":
    print(f"Error: {run.error}")
```

---

## Method 4: `save_extracted_profiling_data`

```python
async def save_extracted_profiling_data(
    self,
    data: list[ExtractedProfilingData],
) -> list[ExtractedProfilingData]:
```

**Purpose:** Persist extracted profiling data from an extraction run.

**When called:** After LLM returns extracted data, save the results.

**Parameters:**

| Param | Why |
|-------|-----|
| `data` | List of extracted data records |

**Why list instead of single record?**
- Batch efficiency - one DB round trip for multiple inserts
- LLM often returns multiple facts per call
- Matches how extraction works (process batch → save batch)

**Returns:** Same records with `id` populated.

**Example flow:**
```python
extracted = [
    ExtractedProfilingData(
        extraction_run_id=run.id,
        user_id=user_id,
        chat_id=chat_id,
        source_message_ids=[42, 43],
        source_quotes=["I'm a software engineer"],
        data={
            "dimension": "core_identity",
            "fact_type": "profession",
            "value": {"profession": "software engineer"},
            "confidence": 0.95,
        },
    ),
    # ... more records
]
saved = await storage.save_extracted_profiling_data(extracted)
```

---

## Method 5: `get_extracted_profiling_data`

```python
async def get_extracted_profiling_data(
    self,
    user_id: str,
    chat_id: str | int | None = None,
    limit: int = 100,
) -> list[ExtractedProfilingData]:
```

**Purpose:** Retrieve previously extracted profiling data.

**When called:**
- Inject profile context into LLM prompts
- Display user's profile to them
- Analytics/reporting

**Parameters:**

| Param | Why |
|-------|-----|
| `user_id` | Required - always filter by user (privacy, multi-tenancy) |
| `chat_id` | Optional - filter to specific chat, or `None` for all chats |
| `limit` | Pagination - don't load everything at once |

**Why `user_id` is required:**
- Security - can't accidentally fetch other users' data
- Multi-tenancy - always scoped to user
- Matches extraction model (user_id = who we're profiling)

**Why `chat_id` is optional:**
- Sometimes want all user's data (comprehensive profile)
- Sometimes want chat-specific data (game session context)

**Returns:** List of records, ordered by `created_at DESC` (newest first).

**Example flow:**
```python
# Get all profiling data for user
all_data = await storage.get_extracted_profiling_data(user_id=user_id)

# Get profiling data from specific chat only
chat_data = await storage.get_extracted_profiling_data(
    user_id=user_id,
    chat_id=chat_id,
)
```

---

## Method 6: `get_messages_for_extraction`

```python
async def get_messages_for_extraction(
    self,
    user_id: str,
    chat_id: str | int | None = None,
    since_message_id: int | str | None = None,
    limit: int = 100,
) -> list[MessageRecord]:
```

**Purpose:** Get user's messages that need to be processed for extraction.

**When called:** At the start of extraction, to fetch source messages.

**Parameters:**

| Param | Why |
|-------|-----|
| `user_id` | Required - whose messages to extract from |
| `chat_id` | Optional - specific chat or all user's chats |
| `since_message_id` | For incremental extraction - skip already processed |
| `limit` | Batch size - process in chunks |

**Why `user_id` is required:**
- Only extract from user's own messages
- Not assistant responses, system messages, etc.
- Privacy - user controls their data

**Why `since_message_id`:**
- Incremental extraction - don't reprocess old messages
- Track progress across runs
- Efficiency - only process new conversations

**Why `limit`:**
- Memory efficiency - don't load 10k messages at once
- LLM context limits - batch appropriately
- Resumability - can checkpoint after each batch

**Returns:** Messages ordered by ID/timestamp, filtered to user's messages only.

**Example flow:**
```python
# First extraction - get all messages
messages = await storage.get_messages_for_extraction(
    user_id=user_id,
    chat_id=chat_id,
    limit=50,
)

# Subsequent extraction - only new messages
messages = await storage.get_messages_for_extraction(
    user_id=user_id,
    chat_id=chat_id,
    since_message_id=last_processed_id,
    limit=50,
)
```

---

## Summary

| Method | Purpose | Key Design Decision |
|--------|---------|---------------------|
| `create_extraction_run` | Start run | Full dataclass for clean API |
| `update_extraction_run` | Update progress | Dict for partial updates |
| `get_extraction_run` | Check status | Simple ID lookup |
| `save_extracted_profiling_data` | Save results | Batch for efficiency |
| `get_extracted_profiling_data` | Retrieve data | user_id required for security |
| `get_messages_for_extraction` | Get source | since_message_id for incremental |

---

## Implementation Notes

These methods go in the **extended interface** section of `StoragePort`:

```python
# In chatforge/ports/storage.py

class StoragePort(ABC):
    # ... existing methods ...

    # =================================================================
    # Extended Interface: Profiling Data Extraction
    # =================================================================
    
    async def create_extraction_run(
        self,
        run: ProfilingDataExtractionRun,
    ) -> ProfilingDataExtractionRun:
        """Create a new extraction run record."""
        raise NotImplementedError("Extended interface not implemented")

    # ... etc ...
```

Adapters that don't need extraction can ignore these (they raise `NotImplementedError`).
Adapters that support extraction implement them with actual DB logic.
