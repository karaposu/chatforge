# Table Design Discussion: Profile Extraction

## Requirements

1. **Track each extraction operation** - when it ran, what config, what model
2. **Track per message/batch what was extracted** - link extraction to source
3. **Trace back extracted data to original messages** - full auditability

---

## Scope Boundaries

**In scope (now):**
- Extract what a user says about THEMSELVES
- Single user per extraction run
- Personal facts only

**Out of scope (future - knowledge graph):**
- Extract what others say about the user
- Relationship facts between users
- Multi-participant profiling from one chat

**Key simplification:** `user_id` = who we're profiling = whose messages we extract from.

---

## Entity Relationships

```
┌──────────┐       ┌──────────┐       ┌─────────────┐
│   User   │◀─────▶│Participant│◀─────▶│    Chat     │
└──────────┘  1:N  └──────────┘  N:1   └─────────────┘
                         │                    │
                         │ sends              │ contains
                         ▼                    ▼
                   ┌──────────┐         ┌──────────┐
                   │ Message  │◀────────│ Message  │
                   └──────────┘         └──────────┘
```

---

## Extraction Scenarios

| Scenario | Description | Use Case |
|----------|-------------|----------|
| **Single chat** | Extract user's profile from one chat | Game session, support ticket |
| **All user chats** | Extract user's profile from all their chats | Comprehensive profile (KANKA) |

---

## Proposed Schema

### Table 1: `profiling_data_extraction_runs`

Tracks each profiling data extraction operation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID/int | Primary key |
| `user_id` | str | **User being profiled** |
| `chat_id` | str/int | Which chat (NULL = all user's chats) |
| `status` | enum | `pending`, `running`, `completed`, `failed` |
| `config` | JSON | ExtractionConfig (which dimensions, thresholds) |
| `model_used` | str | LLM model (e.g., "gpt-4o-mini") |
| `message_count` | int | Total messages processed |
| `message_id_range` | JSON | `{min_id, max_id}` or explicit list |
| `started_at` | datetime | When extraction started |
| `completed_at` | datetime | When extraction finished |
| `duration_ms` | int | How long it took |
| `error` | text | Error message if failed |
| `created_at` | datetime | Record creation time |

**Note:** Extracted data count is not stored - query `extracted_profiling_data` table instead.

```sql
CREATE TABLE profiling_data_extraction_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    chat_id VARCHAR,              -- NULL = all user's chats
    status VARCHAR DEFAULT 'pending',
    config JSONB,
    model_used VARCHAR,
    message_count INT DEFAULT 0,
    message_id_range JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INT,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pde_runs_user ON profiling_data_extraction_runs(user_id);
CREATE INDEX idx_pde_runs_chat ON profiling_data_extraction_runs(chat_id);
CREATE INDEX idx_pde_runs_status ON profiling_data_extraction_runs(status);
```

---

### Table 2: `extracted_profiling_data`

Individual pieces of extracted data with full traceability. The `data` field stores extraction results as JSON, keeping the schema decoupled from the extraction format (e.g., CPF-7 dimensions can evolve without DB changes).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID/int | Primary key |
| `extraction_run_id` | FK | Which run produced this |
| `user_id` | str | **User this data is about** |
| `chat_id` | str/int | Which chat this came from |
| `source_message_ids` | JSON array | Which messages |
| `source_quotes` | JSON array | Exact quotes |
| `data` | JSON | The extracted profiling data (format-agnostic) |
| `created_at` | datetime | When extracted |

**Note:** The `data` field can contain any structure (CPF-7 dimensions, confidence scores, fact types, etc.). This flexibility means:
- Extraction format can change without migrations
- Different extraction configs can coexist
- Application layer interprets the data, not the DB

```sql
CREATE TABLE extracted_profiling_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_run_id UUID REFERENCES profiling_data_extraction_runs(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL,

    -- Where did it come from?
    chat_id VARCHAR,
    source_message_ids JSONB,
    source_quotes JSONB,

    -- What was extracted? (format-agnostic)
    data JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_profiling_user ON extracted_profiling_data(user_id);
CREATE INDEX idx_profiling_chat ON extracted_profiling_data(chat_id);
CREATE INDEX idx_profiling_run ON extracted_profiling_data(extraction_run_id);
```

---

### Table 3: `user_profiles` (Optional - Cached View)

Aggregated current profile per user. Can compute from facts on-demand instead.

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | str | Primary key |
| `core_identity` | JSON | Current facts for this dimension |
| `opinions_views` | JSON | Current facts for this dimension |
| `preferences_patterns` | JSON | Current facts for this dimension |
| `desires_needs` | JSON | Current facts for this dimension |
| `life_narrative` | JSON | Current facts for this dimension |
| `events` | JSON | Current facts for this dimension |
| `entities_relationships` | JSON | Current facts for this dimension |
| `fact_count` | int | Total current facts |
| `last_run_id` | FK | Most recent extraction run |
| `last_extracted_at` | datetime | When last extracted |
| `updated_at` | datetime | Last cache update |

**Note:** This table is optional. Can be:
- Materialized view (refreshed on schedule)
- Cache table (updated after each extraction)
- Skipped entirely (query `extracted_profiling_data` on-demand)

---

## CPF-7 Dimensions (Reference)

These dimensions are stored inside the `data` JSON field, not as DB columns. This keeps the schema flexible.

```python
class ExtractionDimension(str, Enum):
    """Used in application layer to structure the `data` field."""
    CORE_IDENTITY = "core_identity"
    OPINIONS_VIEWS = "opinions_views"
    PREFERENCES_PATTERNS = "preferences_patterns"
    DESIRES_NEEDS = "desires_needs"
    LIFE_NARRATIVE = "life_narrative"
    EVENTS = "events"
    ENTITIES_RELATIONSHIPS = "entities_relationships"
```

---

## Example Scenarios

### Scenario 1: Single Chat (Game)

Player talking to AI game character:

```python
run = ProfilingDataExtractionRun(
    user_id="player_123",
    chat_id="game_session_456",  # specific chat
    config={"dimensions": ["core_identity", "preferences", "desires"]},
)

# Extract from player's messages only
# Result:
ExtractedProfilingData(
    user_id="player_123",
    chat_id="game_session_456",
    data={
        "dimension": "core_identity",
        "fact_type": "profession",
        "value": {"profession": "engineer"},
        "confidence": 0.95,
    },
    source_message_ids=["msg_12"],
    source_quotes=["I work as an engineer"],
)
```

### Scenario 2: All Chats (KANKA)

Building comprehensive profile:

```python
run = ProfilingDataExtractionRun(
    user_id="user_789",
    chat_id=None,  # None = all user's chats
    config={"dimensions": ["all"]},
)

# Extracts from every chat user_789 participated in
# Data from different chats all linked to user_789
```

### Scenario 3: Tracing Back to Source

```python
profiling_data = get_profiling_data(data_id="data_xyz")

print(f"User: {profiling_data.user_id}")
print(f"Data: {profiling_data.data}")  # Contains dimension, fact_type, value, confidence, etc.
print(f"From chat: {profiling_data.chat_id}")
print(f"Message IDs: {profiling_data.source_message_ids}")
print(f"Quotes: {profiling_data.source_quotes}")
print(f"Extracted in run: {profiling_data.extraction_run_id}")
```

---

## Dataclass Representations

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Note: ExtractionDimension enum (CPF-7) is defined in application layer
# and stored inside the `data` JSON field - see "CPF-7 Dimensions (Reference)" above


@dataclass
class ProfilingDataExtractionRun:
    """Tracks a single profiling data extraction operation."""
    id: str | int | None = None
    user_id: str = ""

    # Scope (chat_id=None means all user's chats)
    chat_id: str | int | None = None

    # Status
    status: ExtractionStatus = ExtractionStatus.PENDING
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


@dataclass
class UserProfile:
    """Aggregated profile view (cached/materialized)."""
    user_id: str
    core_identity: list[dict] = field(default_factory=list)
    opinions_views: list[dict] = field(default_factory=list)
    preferences_patterns: list[dict] = field(default_factory=list)
    desires_needs: list[dict] = field(default_factory=list)
    life_narrative: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    entities_relationships: list[dict] = field(default_factory=list)
    fact_count: int = 0
    last_run_id: str | int | None = None
    last_extracted_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

---

## Query Patterns

### Get latest profile data for user

```sql
SELECT data, source_quotes, created_at
FROM extracted_profiling_data
WHERE user_id = 'user_123'
ORDER BY created_at DESC;
```

### Get all profiling data from a specific chat

```sql
SELECT * FROM extracted_profiling_data
WHERE chat_id = 'chat_456'
ORDER BY created_at;
```

### Get extraction history for user

```sql
SELECT * FROM profiling_data_extraction_runs
WHERE user_id = 'user_123'
ORDER BY created_at DESC;
```

### Trace profiling data to source messages

```sql
SELECT * FROM extracted_profiling_data WHERE id = 'data_xyz';

-- Then fetch messages using source_message_ids
```

---

## Open Questions

1. **Data deduplication:** Same data extracted from different messages - merge or keep both?

2. **Confidence aggregation:** Same data multiple times - increase confidence?

3. **Temporal data:** "I was an engineer" (past) vs "I am an engineer" (present)?

4. **Contradiction handling:** "I love coffee" then "I hate coffee" - supersede or keep history?

5. **Extraction frequency:** Real-time? Batch nightly? On-demand?

---

## Future Extensions (Knowledge Graph)

When needed, can extend to:
- `subject_user_id` + `source_user_id` distinction
- `related_user_id` for relationship facts
- Multi-participant extraction
- Cross-user fact attribution

For now, keep it simple: **user_id = who we're profiling = whose messages we extract from.**
