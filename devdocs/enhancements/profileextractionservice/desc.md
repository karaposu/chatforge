# ProfilingDataExtractionService

## Overview

A service that extracts profiling data from conversations using LLM-based semantic understanding. Implements CPF-7 (Conversational Profiling Framework - 7 Dimensions).

**Note:** This service extracts raw profiling data, not aggregated profiles. Profiling (aggregation) is a separate future step.

Uses existing `StoragePort` - no new ports needed.

## The 7 Dimensions

1. **Core Identity** - name, age, profession, stable attributes
2. **Opinions & Views** - persistent beliefs, worldviews (non-ephemeral)
3. **Preferences & Patterns** - recurring choices, behavioral tendencies
4. **Desires & Needs** - wants, wishes, hopes, motivations
5. **Life Narrative** - story arc, formative experiences, transitions
6. **Events** - significant events (filtered by importance)
7. **Entities & Relationships** - people, places, organizations they mention

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION                               │
│                                                              │
│  ┌─────────────────────────────────────┐                    │
│  │  SQLiteStorageAdapter               │                    │
│  │  (or PostgresStorageAdapter, etc.)  │                    │
│  └──────────────────┬──────────────────┘                    │
│                     │ implements                             │
└─────────────────────┼────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                       CHATFORGE                              │
│                                                              │
│  ┌─────────────────────────────────────┐                    │
│  │          StoragePort                │  ← ALREADY EXISTS  │
│  │  - get_conversation()               │                    │
│  │  - list_conversations()             │                    │
│  │  - get_messages()                   │                    │
│  │  + create_extraction_run()  ← EXTEND│                    │
│  │  + save_extracted_data()    ← EXTEND│                    │
│  └──────────────────┬──────────────────┘                    │
│                     │                                        │
│                     ▼                                        │
│  ┌─────────────────────────────────────┐                    │
│  │  ProfilingDataExtractionService     │                    │
│  │                                      │                    │
│  │  __init__(storage: StoragePort)     │                    │
│  │                                      │                    │
│  │  - Reads messages via storage       │                    │
│  │  - Extracts via LLM                 │                    │
│  │  - Writes extracted data via storage│                    │
│  └─────────────────────────────────────┘                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Usage

```python
from chatforge.services.profiling_data_extraction import ProfilingDataExtractionService

service = ProfilingDataExtractionService(
    storage=my_storage_adapter,  # App's existing StoragePort
    config=ExtractionConfig(
        dimensions=["core_identity", "preferences_patterns", "desires_needs", "entities_relationships"],
    ),
)

# Extract profiling data for a user from a specific chat
run = await service.extract(user_id=user_id, chat_id=chat_id)

# Or extract from all user's chats
run = await service.extract(user_id=user_id, chat_id=None)
```

## Key Principle

DB-agnostic. Applications bring their own `StoragePort` adapter. The extraction logic lives in Chatforge, data ownership stays with the application.
