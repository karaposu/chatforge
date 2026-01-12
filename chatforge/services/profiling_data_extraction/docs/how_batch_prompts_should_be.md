# How Batch Prompts Should Be Designed

Deep analysis of batch extraction approach as alternative to per-message extraction.

---

## The Two Models

| Aspect | Per-Message (`prompts.py`) | Batch (`batch_prompts.py`) |
|--------|---------------------------|---------------------------|
| Input | 1 target + N context messages | N messages together |
| LLM calls | 7 dimensions × M messages | 7 dimensions × (M / batch_size) |
| Attribution | Perfect (single source) | Needs explicit tracking |
| Use case | Precision, traceability | Cost, speed |

---

## Core Challenge: Source Attribution

Per-message extraction has perfect attribution - every fact comes from one known message.

Batch extraction must solve: **Which message did each fact come from?**

### Solution: Message IDs in Output

```
=== MESSAGES TO EXTRACT FROM ===
[MSG-001] (Alice, 2024-01-15 10:30): I'm a software engineer at Google
[MSG-002] (Bot, 2024-01-15 10:31): That's interesting!
[MSG-003] (Alice, 2024-01-15 10:32): The Seattle commute is killing me
[MSG-004] (Alice, 2024-01-15 10:33): I really want to work remotely

Extract facts and cite source message ID for each.
```

Output includes source:
```json
{
  "items": [
    {
      "aspect": "profession",
      "state_value": "software engineer",
      "source_message_id": "MSG-001"
    },
    {
      "aspect": "employer",
      "state_value": "Google",
      "source_message_id": "MSG-001"
    }
  ]
}
```

---

## Batch Prompt Structure

### Option A: Per-Dimension Batch Prompts (Recommended)

Still 7 separate prompts, but each processes multiple messages.

```python
BATCH_CORE_IDENTITY_PROMPT = """
=== CORE IDENTITY EXTRACTION (BATCH) ===

Extract identity facts from the messages below.
For each fact, cite the source message ID.

WHAT COUNTS AS CORE IDENTITY:
- What someone IS (roles, attributes, states)
- Stable characteristics that define them
[... same rules as per-message ...]

=== MESSAGES ===
{numbered_messages}

INSTRUCTIONS:
- Extract from ALL messages, not just one
- Include source_message_id for each extracted fact
- If a fact spans multiple messages, cite the primary source
- Skip messages with no identity content

Return JSON:
{{
  "items": [
    {{
      "aspect": "string",
      "state_value": "string",
      "temporal": "string or null",
      "relational_dimension": "string or null",
      "source_message_id": "string (e.g., MSG-001)"
    }}
  ]
}}
"""
```

**Pros:**
- Leverages existing dimension expertise in prompts
- Clear separation of concerns
- Easier to maintain/debug

**Cons:**
- Still 7 LLM calls per batch
- Some redundancy in reading same messages 7 times

---

### Option B: Single Combined Prompt

One prompt extracts all dimensions at once.

```python
BATCH_ALL_DIMENSIONS_PROMPT = """
=== FULL PROFILE EXTRACTION (BATCH) ===

Extract profiling data across all dimensions from the messages below.

=== MESSAGES ===
{numbered_messages}

=== DIMENSIONS TO EXTRACT ===

1. CORE IDENTITY: Who they are (roles, attributes, demographics)
2. OPINIONS/VIEWS: Non-ephemeral beliefs and stances
3. PREFERENCES: Stable patterns and behavioral tendencies
4. DESIRES/NEEDS: Wants, wishes, hopes, needs
5. LIFE NARRATIVE: Biographical elements, life story
6. EVENTS: Significant occurrences they're involved in
7. ENTITIES: People, places, organizations they mention

For each extracted fact, include:
- dimension: which of the 7
- source_message_id: which message (MSG-001, etc.)
- the dimension-specific fields

Return JSON with all dimensions...
"""
```

**Pros:**
- Single LLM call per batch (7x more efficient)
- LLM sees full context once

**Cons:**
- Very complex prompt
- May reduce extraction quality
- Harder to debug which dimension failed
- Token limits may be hit faster

---

### Option C: Hybrid - Batch with Verification

1. Use batch for initial extraction (fast, cheap)
2. Use per-message for high-confidence verification (precise)

```python
# Step 1: Batch extract
batch_results = batch_extract(messages, dimensions)

# Step 2: Verify high-value extractions
for item in batch_results:
    if item.needs_verification:
        verified = per_message_extract(
            target=messages[item.source_message_id],
            context=surrounding_messages
        )
```

---

## Pydantic Models for Batch

### Extended Item Models

Each item needs `source_message_id`:

```python
class BatchCoreIdentityItem(BaseModel):
    """Identity fact with source attribution."""

    aspect: str
    state_value: str
    temporal: str | None = None
    relational_dimension: str | None = None
    source_message_id: str = Field(
        description="Message ID this fact was extracted from (e.g., MSG-001)"
    )


class BatchCoreIdentityResult(BaseModel):
    """Batch extraction result for core identity."""

    items: list[BatchCoreIdentityItem] = Field(default_factory=list)
    # No has_content flag - just check if items is empty
```

### Alternative: Inherit from Base

```python
class SourcedItem(BaseModel):
    """Mixin for batch extraction items."""
    source_message_id: str


class BatchCoreIdentityItem(CoreIdentityItem, SourcedItem):
    """Core identity item with source tracking."""
    pass
```

---

## Message Formatting

### Format Function

```python
def format_messages_for_batch(
    messages: list[MessageRecord],
    id_prefix: str = "MSG"
) -> tuple[str, dict[str, int]]:
    """
    Format messages for batch extraction.

    Returns:
        formatted: String with numbered messages
        id_map: Maps MSG-001 -> actual message.id
    """
    lines = []
    id_map = {}

    for i, msg in enumerate(messages, 1):
        msg_id = f"{id_prefix}-{i:03d}"
        id_map[msg_id] = msg.id

        sender = msg.sender_name or msg.role or "Unknown"
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M") if msg.created_at else ""

        lines.append(f"[{msg_id}] ({sender}, {timestamp}): {msg.content}")

    return "\n".join(lines), id_map
```

### Example Output

```
[MSG-001] (Alice, 2024-01-15 10:30): I'm a software engineer at Google
[MSG-002] (Bot, 2024-01-15 10:31): That's interesting! Tell me more.
[MSG-003] (Alice, 2024-01-15 10:32): Well, I've been there 3 years now
[MSG-004] (Alice, 2024-01-15 10:33): The Seattle commute is rough though
[MSG-005] (Alice, 2024-01-15 10:34): I really want to try remote work
```

---

## Optimal Batch Size

### Factors

| Factor | Smaller Batch | Larger Batch |
|--------|---------------|--------------|
| Token usage per call | Lower | Higher |
| Attribution accuracy | Higher | May degrade |
| Context coherence | Messages more related | May span topics |
| LLM focus | Better | May miss things |

### Recommendations

| Model | Recommended Batch Size |
|-------|----------------------|
| gpt-4o-mini | 10-20 messages |
| gpt-4o | 20-30 messages |
| claude-3-haiku | 10-15 messages |
| claude-3-opus | 25-40 messages |

### Config

```python
@dataclass
class ExtractionConfig:
    # ... existing fields ...

    # Per-message settings
    context_window: int = 5

    # Batch settings
    batch_size: int = 15  # Messages per batch extraction
    batch_mode: bool = False  # Use batch vs per-message
```

---

## Trade-off Analysis

### When to Use Per-Message

- **High-value conversations**: Important customer, critical context
- **Legal/compliance**: Need exact source attribution
- **Debugging**: Understanding extraction behavior
- **Small message sets**: < 20 messages, batch overhead not worth it

### When to Use Batch

- **Historical analysis**: Processing large archives
- **Cost-sensitive**: Need to minimize LLM calls
- **Speed-sensitive**: Need results faster
- **Lower precision OK**: Attribution doesn't need to be perfect

### Cost Comparison

```
Scenario: 100 messages, 7 dimensions

Per-Message:
  - 100 messages × 7 dimensions = 700 LLM calls
  - Each call: ~500 tokens input, ~200 output
  - Total: ~350K input tokens, ~140K output tokens

Batch (size=20):
  - 5 batches × 7 dimensions = 35 LLM calls
  - Each call: ~2000 tokens input, ~500 output
  - Total: ~70K input tokens, ~17.5K output tokens

Batch is ~5x cheaper in tokens, 20x fewer API calls
```

---

## Implementation Plan

### Files to Create

```
profiling_data_extraction/
├── prompts.py           # Per-message prompts (exists)
├── batch_prompts.py     # Batch prompts (NEW)
├── models.py            # Add Batch* variants
├── cpde7llmservice.py   # Add batch methods
└── service.py           # Support batch_mode in config
```

### CPDE7LLMService Interface

```python
class CPDE7LLMService:
    # Per-message (existing)
    def extract_core_identity(self, target, context) -> CoreIdentityResult

    # Batch (new)
    def batch_extract_core_identity(
        self,
        messages: list[MessageRecord]
    ) -> BatchCoreIdentityResult

    # Or unified with mode parameter
    def extract_core_identity(
        self,
        messages: list[MessageRecord],
        mode: Literal["per_message", "batch"] = "per_message",
        target_index: int | None = None,  # For per-message mode
    ) -> CoreIdentityResult | BatchCoreIdentityResult
```

---

## Open Questions

1. **Should batch models inherit from per-message models?**
   - Pro: DRY, shared validation
   - Con: Different semantics (source_message_id required vs not)

2. **How to handle cross-message facts?**
   - "I moved to Seattle [MSG-1] for my job at Amazon [MSG-3]"
   - Cite primary source? Cite both?

3. **Should batch support context window too?**
   - Batch of 20 messages, but also include 5 prior for context?
   - Or is batch large enough to be self-contextualizing?

4. **Confidence in batch mode?**
   - Is LLM less confident when processing many messages?
   - Should we adjust confidence_threshold for batch?

---

## Recommendation

### Start with Option A: Per-Dimension Batch Prompts

1. **Clearer**: Each dimension prompt stays focused
2. **Debuggable**: Can test/fix one dimension at a time
3. **Incremental**: Easy migration from per-message
4. **Flexible**: Can add combined prompt later if needed

### Implementation Order

1. Create `batch_prompts.py` with 7 batch prompts
2. Add `Batch*` models to `models.py`
3. Add `batch_extract_*` methods to `CPDE7LLMService`
4. Add `batch_mode` to `ExtractionConfig`
5. Update `ProfilingDataExtractionService` to use batch when configured

---

## Summary

| Decision | Choice |
|----------|--------|
| Prompt structure | Per-dimension batch (Option A) |
| Attribution | Explicit `source_message_id` in output |
| Message format | Numbered with `[MSG-XXX]` prefix |
| Batch size | Configurable, default 15 |
| Models | Extend base models with `source_message_id` |
| Mode selection | Config flag: `batch_mode: bool` |
