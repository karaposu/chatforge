# Deep Analysis: Prerequisites for ProfilingDataExtractionService

## Problem Analysis

### Core Challenge
Build a service that extracts profiling data (CPF-7) from conversations, using `StoragePort` for data access. The service must be DB-agnostic while the extraction logic is reusable.

**Important distinction:**
- **Profiling Data Extraction** (this service) = Extract raw data from messages
- **Profiling** (separate, future) = Aggregate extracted data into user profiles

This service focuses on extraction only. Raw extracted data can be injected into LLM context directly - LLMs are smart enough to use it effectively.

### Key Constraints
1. Must use existing `StoragePort` (no new ports for conversation access)
2. Must work with any adapter (SQLite, SQLAlchemy, Memory, etc.)
3. Must be async and batch-capable
4. LLM-based extraction (using existing `get_llm()`)

### Critical Success Factors
- Clean separation between extraction logic and storage
- Incremental extraction (don't reprocess old conversations)
- Full traceability from extracted data back to source messages

---

## Gap Analysis: What's Missing

### 1. Data Models (storage_types.py) - DONE

**Status:** Added `ProfilingDataExtractionRun` and `ExtractedProfilingData` to `chatforge/ports/storage_types.py`.

```python
@dataclass
class ProfilingDataExtractionRun:
    """Tracks a single profiling data extraction operation."""
    id: str | int | None = None
    user_id: str = ""

    # Scope (chat_id=None means all user's chats)
    chat_id: str | int | None = None

    # Status
    status: str = "pending"  # pending, running, completed, failed
    error: str | None = None

    # Config
    config: dict[str, Any] = field(default_factory=dict)
    model_used: str | None = None

    # Metrics
    message_count: int = 0
    message_id_range: dict[str, Any] | None = None
    duration_ms: int | None = None

    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExtractedProfilingData:
    """A single piece of extracted profile data with full traceability."""
    id: str | int | None = None
    extraction_run_id: str | int | None = None
    user_id: str = ""

    # Source traceability
    chat_id: str | int | None = None
    source_message_ids: list[str | int] = field(default_factory=list)
    source_quotes: list[str] = field(default_factory=list)

    # Extracted content (format-agnostic)
    data: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Note:** The `data` field is format-agnostic - stores CPF-7 dimensions, confidence, etc. as JSON. Schema doesn't need to change if extraction format evolves.

**Action:** Add to `chatforge/ports/storage_types.py`

---

### 2. StoragePort Extension (storage.py) - DONE

**Status:** Added 6 methods to `chatforge/ports/storage.py` extended interface. See `storageport_extension.md` for details.

```python
# Extraction run operations
async def create_extraction_run(
    self,
    run: ProfilingDataExtractionRun,
) -> ProfilingDataExtractionRun:
    """Create a new extraction run record."""
    raise NotImplementedError("Extended interface not implemented")

async def update_extraction_run(
    self,
    run_id: str | int,
    updates: dict[str, Any],
) -> ProfilingDataExtractionRun:
    """Update extraction run status/metrics."""
    raise NotImplementedError("Extended interface not implemented")

async def get_extraction_run(
    self,
    run_id: str | int,
) -> ProfilingDataExtractionRun | None:
    """Get extraction run by ID."""
    raise NotImplementedError("Extended interface not implemented")

# Extracted data operations
async def save_extracted_profiling_data(
    self,
    data: list[ExtractedProfilingData],
) -> list[ExtractedProfilingData]:
    """Save batch of extracted profiling data."""
    raise NotImplementedError("Extended interface not implemented")

async def get_extracted_profiling_data(
    self,
    user_id: str,
    chat_id: str | int | None = None,
    limit: int = 100,
) -> list[ExtractedProfilingData]:
    """Get extracted profiling data for user, optionally filtered by chat."""
    raise NotImplementedError("Extended interface not implemented")

# Message access for extraction
async def get_messages_for_extraction(
    self,
    user_id: str,
    chat_id: str | int | None = None,
    since_message_id: int | str | None = None,
    limit: int = 100,
) -> list[MessageRecord]:
    """Get user's messages for extraction processing."""
    raise NotImplementedError("Extended interface not implemented")
```

**Action:** Add to `chatforge/ports/storage.py` extended interface section

---

### 3. Extraction Configuration - DONE

**Status:** Created `chatforge/services/profiling_data_extraction/config.py` with `ExtractionConfig`.

```python
# chatforge/services/profiling_data_extraction/config.py

@dataclass
class ExtractionConfig:
    """Controls what and how to extract."""

    # Which CPF-7 dimensions to extract (all 7 by default)
    dimensions: list[str] = field(default_factory=lambda: [
        "core_identity",
        "opinions_views",
        "preferences_patterns",
        "desires_needs",
        "life_narrative",
        "events",
        "entities_relationships",
    ])

    # Extraction behavior
    batch_size: int = 50  # Messages per LLM call
    min_messages_for_extraction: int = 5  # Skip tiny convos
    confidence_threshold: float = 0.5  # Min confidence to save
```

**Note:** LLM config (provider, model) should come from application, not hardcoded here.

**Action:** Create new file in profiling data extraction service

---

### 4. CPF-7 Extraction Prompts

**Missing:** The actual prompts that instruct LLM what to extract.

```python
# chatforge/services/profiling_data_extraction/prompts.py

EXTRACTION_PROMPT = """
Extract profiling data from this conversation.

For each piece of information found, output JSON:
{
  "dimension": "core_identity|opinions_views|preferences_patterns|desires_needs|life_narrative|events|entities_relationships",
  "fact_type": "string (e.g., 'profession', 'preference', 'opinion')",
  "value": { ... extracted data ... },
  "confidence": 0.0-1.0,
  "source_quote": "exact quote from conversation"
}

Only extract what the user says about THEMSELVES.
...
"""
```

**Note:** Prompt design needs careful thought, especially for batch extraction.

**Action:** Create prompts file with structured extraction instructions

---

### 5. Adapter Updates

**Current State:** Adapters don't have extraction tables/methods.

**Action:**
1. Define tables first (see `table_design_discussion.md`)
2. Implement StoragePort extension methods in SQLAlchemy adapter
3. Create memory adapter for testing

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│              ProfilingDataExtractionService                      │
│                         (GOAL)                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ requires
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Extraction  │  │    CPF-7    │                               │
│  │   Config    │  │   Prompts   │                               │
│  └─────────────┘  └─────────────┘                               │
│         │                │                                       │
│         └────────┬───────┘                                       │
│                  │                                               │
│                  ▼                                               │
│       ┌─────────────────────┐                                   │
│       │ StoragePort         │                                   │
│       │ (Extended Methods)  │                                   │
│       │ + create_extraction_run                                 │
│       │ + save_extracted_profiling_data                         │
│       │ + get_messages_for_extraction                           │
│       └──────────┬──────────┘                                   │
│                  │                                               │
│                  ▼                                               │
│       ┌──────────────────────────────┐                          │
│       │ ProfilingDataExtractionRun   │                          │
│       │ ExtractedProfilingData       │                          │
│       │ (storage_types.py)           │                          │
│       └──────────────────────────────┘                          │
│                                                                  │
│  ALREADY EXISTS:                                                 │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  get_llm()  │  │ MessageRecord│                              │
│  │ LLM Factory │  │ ChatRecord   │                              │
│  └─────────────┘  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommended Build Order

| Priority | Component | Location | Status |
|----------|-----------|----------|--------|
| **1** | `ProfilingDataExtractionRun`, `ExtractedProfilingData` | `ports/storage_types.py` | DONE |
| **2** | Extraction methods in `StoragePort` | `ports/storage.py` | DONE |
| **3** | `ExtractionConfig` | `services/profiling_data_extraction/config.py` | DONE |
| **4** | CPF-7 Prompts | `services/profiling_data_extraction/prompts.py` | - |
| **5** | `ProfilingDataExtractionService` | `services/profiling_data_extraction/service.py` | - |
| **6** | Adapter support (SQLAlchemy) | `adapters/storage/sqlalchemy.py` | DONE |
| **7** | Tests | `tests/unit/profiling_data_extraction/` | - |

---

## Key Architectural Decisions

### 1. Extraction tracking
**Decision:** Separate `profiling_data_extraction_runs` table
- Tracks each extraction operation
- Links to `extracted_profiling_data` via FK
- See `table_design_discussion.md` for schema

### 2. Sync vs Async extraction
**Recommendation:** Batch (scheduled/on-demand)
- More efficient
- Controllable cost
- Can be triggered manually or on schedule

### 3. Data format
**Decision:** Format-agnostic `data` JSON field
- CPF-7 structure stored in JSON, not columns
- Schema doesn't change if extraction format evolves
- Application layer interprets the data

---

## Summary: Build These First

1. **Data models** in `storage_types.py` (dataclasses)
2. **Table schema** (see `table_design_discussion.md`)
3. **StoragePort extension** methods
4. **`ExtractionConfig`** dataclass
5. **CPF-7 prompts** for extraction

Then `ProfilingDataExtractionService` can be built on top.

---

## Out of Scope (Future)

- **Profile aggregation** - Combining extracted data into unified profile
- **Profile caching** - `user_profiles` table for fast access
- **Merge logic** - Handling contradictions, temporal changes
- **Knowledge graph** - Multi-user relationships, cross-user attribution
