# Batch CPDE-7 Improvement: Target-Only Extraction (Implemented)

## Overview

This document describes the **targeted extraction** feature added to CPDE-7, which extracts profiling data ONLY from TARGET messages while using CONTEXT messages for understanding references.

## The Problem (Solved)

When profiling conversational data between a user and an AI assistant, extracting from ALL messages caused issues:

```
Assistant: "You seem like someone who values efficiency over relationships..."
User: "Yeah, I guess that's true"
```

**Previous behavior:** AI assumptions became profile facts even with weak confirmations.

**New behavior:** Only extracts from TARGET (user) messages, and only with strong confirmations.

---

## Implementation: Option B (Inline Markers)

Messages are formatted with inline markers:

```
Message ID: msg_1
Role: assistant (CONTEXT)
Content: What do you do for work?

Message ID: msg_2
Role: user (TARGET)
Content: I'm an engineer at Google
```

The LLM is instructed to:
- Extract ONLY from messages marked `(TARGET)`
- Use `(CONTEXT)` messages for understanding references
- Require strong confirmations ("Yes, exactly") not weak ones ("Maybe")

---

## Files Added/Modified

### New File: `batch_prompts_targeted.py`

Contains all targeted prompts:

| Export | Description |
|--------|-------------|
| `TARGETING_RULES` | Shared rules for TARGET vs CONTEXT handling |
| `CPDE_CORE_IDENTITY_TARGETED` | Core identity extraction (targeted) |
| `CPDE_OPINIONS_VIEWS_TARGETED` | Opinions extraction (targeted) |
| `CPDE_PREFERENCES_PATTERNS_TARGETED` | Preferences extraction (targeted) |
| `CPDE_DESIRES_NEEDS_TARGETED` | Desires extraction (targeted) |
| `CPDE_LIFE_NARRATIVE_TARGETED` | Life narrative extraction (targeted) |
| `CPDE_EVENTS_TARGETED` | Events extraction (targeted) |
| `CPDE_ENTITIES_RELATIONSHIPS_TARGETED` | Entities extraction (targeted) |
| `CPDE_ALL_7_TARGETED` | All 7 dimensions in one prompt |
| `format_messages_with_markers()` | Helper to format messages |

### Modified: `cpde7llmservice.py`

Added targeted extraction methods:

```python
# Individual dimension methods
await service.extract_core_identity_targeted(messages)
await service.extract_opinions_views_targeted(messages)
await service.extract_preferences_patterns_targeted(messages)
await service.extract_desires_needs_targeted(messages)
await service.extract_life_narrative_targeted(messages)
await service.extract_events_targeted(messages)
await service.extract_entities_relationships_targeted(messages)

# Combined methods
await service.extract_all_7_targeted(messages)  # Single LLM call
await service.extract_targeted(messages, dimensions=[...])  # Main entry point
await service.extract_dimension_targeted(messages, "events")  # By name
```

### Modified: Exports

- `cpde7/__init__.py` - Exports `format_messages_with_markers`
- `profiling_data_extraction/__init__.py` - Re-exports from cpde7

---

## Usage

### Basic Usage: List of Messages

```python
from chatforge.services.profiling_data_extraction import (
    CPDE7LLMService,
    format_messages_with_markers,
)

service = CPDE7LLMService()

# Conversation with user and assistant
messages = [
    {"id": "msg_1", "role": "assistant", "content": "Tell me about yourself"},
    {"id": "msg_2", "role": "user", "content": "I'm a 34-year-old engineer"},
    {"id": "msg_3", "role": "assistant", "content": "You seem like an introvert"},
    {"id": "msg_4", "role": "user", "content": "Yes, I definitely am"},
]

# Extract all 7 dimensions from user messages only
result = await service.extract_all_7_targeted(
    messages=messages,
    target_roles=["user"],  # Only extract from user messages
)

# Or extract specific dimensions
result = await service.extract_targeted(
    messages=messages,
    target_roles=["user"],
    dimensions=["core_identity", "preferences_patterns"],
    parallel=True,  # Run extractions concurrently
)
```

### Pre-formatted Messages

```python
# Format messages manually
formatted = format_messages_with_markers(messages, target_roles=["user"])

# Pass pre-formatted string
result = await service.extract_core_identity_targeted(formatted)
```

### Single Dimension by Name

```python
result = await service.extract_dimension_targeted(
    messages=messages,
    dimension="events",
    target_roles=["user"],
)
```

---

## Confirmation Strength

The targeted prompts distinguish between strong and weak confirmations:

### Strong Confirmations (DO extract)
- "Yes, exactly"
- "That's right"
- "Absolutely"
- "Yes, I definitely am an introvert"

### Weak Confirmations (DO NOT extract)
- "Maybe"
- "I guess"
- "I don't know"
- "Perhaps"
- "Sort of"

**Examples:**

```
Assistant: "You seem like an introvert"
User: "Maybe, I guess"
-> Do NOT extract (weak confirmation)
```

Assistant: "You seem like an introvert"
User: "Yes, I definitely am"
-> DO extract (strong confirmation)
```

---

## Dimensional Boundaries

The prompts include negative examples to prevent cross-dimension extraction:

### Core Identity - What NOT to Extract

| Statement | Why NOT Core Identity | Correct Dimension |
|-----------|----------------------|-------------------|
| "I always code better at night" | How they work, not who they are | Preferences |
| "I really want to transition into AI/ML" | Personal aspiration | Desires |

### Opinions - Opinion vs Desire

**Opinions** express beliefs about THE WORLD:
- "Remote work IS the future" (belief about how things are)
- "AI IS dangerous" (judgment about something external)

**Desires** express PERSONAL wants:
- "I WANT to work remotely" (personal aspiration)
- "I HOPE to transition to AI" (personal goal)

Quick test:
- "X is/are/should be..." → Opinion (about the world)
- "I want/hope/wish/need..." → Desire (about themselves)

---

## Testing

See the test notebook: `extraction_tests/notebooks/cpde_test3.ipynb`

The notebook demonstrates:
1. Loading conversation data with user/assistant messages
2. Running targeted extraction on each dimension
3. Verifying that only TARGET (user) messages are extracted from
4. Checking dimensional boundaries are respected

---

## Comparison: Targeted vs Non-Targeted

| Aspect | Non-Targeted | Targeted |
|--------|-------------|----------|
| Extracts from | All messages | TARGET messages only |
| AI assumptions | May become facts | Ignored unless confirmed |
| Weak confirmations | Extracted | Ignored |
| Use case | Single-speaker text | Multi-party conversations |
| Methods | `extract_*()` | `extract_*_targeted()` |
