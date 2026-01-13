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

### Option B: Single Combined Prompt (Recommended for Cost)

One prompt extracts all dimensions at once. **Most cost-efficient approach.**

#### Why This Makes Sense

```
Single message often contains multiple dimensions:

"I'm a software engineer (IDENTITY) at Google (ENTITY) who hates meetings (OPINION).
 I always work better at night (PREFERENCE). Just got promoted (EVENT) last week.
 Really hoping to lead a team soon (DESIRE)."

With Option A: LLM reads this message 7 times (once per dimension)
With Option B: LLM reads once, extracts everything
```

#### Cost Comparison

| Approach | 100 msgs | 1,000 msgs | 10,000 msgs |
|----------|----------|------------|-------------|
| Per-message (7 dims) | 700 calls | 7,000 calls | 70,000 calls |
| Batch per-dim (size=20) | 35 calls | 350 calls | 3,500 calls |
| **Batch combined** | **5 calls** | **50 calls** | **500 calls** |

**Option B is 7x cheaper than Option A, 140x cheaper than per-message.**

#### Full Prompt Design

```python
BATCH_COMBINED_PROMPT = """
=== CPDE-7 FULL EXTRACTION ===

Extract profiling data from the messages below across ALL 7 dimensions.
For each extracted fact, cite the source message ID.

=== MESSAGES ===
{numbered_messages}

=== EXTRACTION DIMENSIONS ===

**1. CORE IDENTITY** - Who they ARE (stable characteristics)
- Roles, professions, demographics, affiliations
- Physical attributes, conditions, personality traits
- NOT: opinions, desires, events, preferences
- Fields: aspect, state_value, temporal?, relational_dimension?

**2. OPINIONS & VIEWS** - What they BELIEVE (non-ephemeral)
- Lasting beliefs, worldviews, stances
- NOT: momentary reactions ("this coffee is cold")
- Fields: about, view, qualifier?

**3. PREFERENCES & PATTERNS** - How they consistently BEHAVE
- Recurring choices, habits, tendencies
- "always", "never", "prefer", "tend to"
- Fields: activity_category, activity, preference, context?

**4. DESIRES & NEEDS** - What they WANT
- Needs (essential), wants (active), wishes (hypothetical), hopes (aspirational)
- Fields: type (need/want/wish/hope), target, is_active, intensity?, temporal?

**5. LIFE NARRATIVE** - Their STORY (biographical past)
- Past experiences, life chapters, formative events
- NOT: current/future events (those go in EVENTS)
- Fields: what_happened, period?, significance?

**6. EVENTS** - What's HAPPENING (temporary occurrences)
- Current, recent, or planned discrete events
- Temporary states ("I'm sick", "I'm moving")
- Fields: event, involvement, temporal?, people_involved?, outcome?

**7. ENTITIES & RELATIONSHIPS** - Their WORLD
- People, organizations, places, products they mention
- Focus on entities with relationship to speaker
- Fields: name, type, mentioned_properties?, relationship_indicators, interaction_metadata?

=== EXTRACTION RULES ===

1. Only extract from USER messages (skip assistant/bot messages)
2. Only extract what user says about THEMSELVES
3. Each fact needs source_message_id (e.g., "MSG-001")
4. If nothing to extract for a dimension, return empty array
5. Split compound statements into separate facts
6. Include source_quote for traceability

=== OUTPUT FORMAT ===

Return JSON with all 7 dimensions:
{{
  "core_identity": [
    {{"aspect": "...", "state_value": "...", "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "opinions_views": [
    {{"about": "...", "view": "...", "qualifier": null, "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "preferences_patterns": [
    {{"activity_category": "...", "activity": "...", "preference": "...", "context": null, "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "desires_needs": [
    {{"type": "...", "target": "...", "is_active": "yes", "intensity": null, "temporal": null, "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "life_narrative": [
    {{"what_happened": "...", "period": null, "significance": null, "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "events": [
    {{"event": "...", "involvement": "...", "temporal": null, "people_involved": null, "outcome": null, "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ],
  "entities_relationships": [
    {{"name": "...", "type": "...", "relationship_indicators": [...], "source_message_id": "MSG-XXX", "source_quote": "..."}}
  ]
}}
"""
```

#### Pydantic Models for Combined Output

```python
# models.py additions

class SourcedExtraction(BaseModel):
    """Base for all batch-extracted items."""
    source_message_id: str = Field(
        description="Message ID this was extracted from (e.g., MSG-001)"
    )
    source_quote: str = Field(
        description="Exact quote from the message"
    )


class BatchIdentityItem(SourcedExtraction):
    aspect: str
    state_value: str
    temporal: str | None = None
    relational_dimension: str | None = None


class BatchOpinionItem(SourcedExtraction):
    about: str
    view: str
    qualifier: str | None = None


class BatchPreferenceItem(SourcedExtraction):
    activity_category: str
    activity: str
    preference: str
    context: str | None = None


class BatchDesireItem(SourcedExtraction):
    type: str  # need/want/wish/hope
    target: str
    is_active: str = "unknown"
    intensity: str | None = None
    temporal: str | None = None


class BatchNarrativeItem(SourcedExtraction):
    what_happened: str
    period: str | None = None
    significance: str | None = None


class BatchEventItem(SourcedExtraction):
    event: str
    involvement: str
    temporal: str | None = None
    people_involved: list[str] | None = None
    outcome: str | None = None


class BatchEntityItem(SourcedExtraction):
    name: str
    type: str
    mentioned_properties: dict | None = None
    relationship_indicators: list[str] = Field(default_factory=list)
    interaction_metadata: dict | None = None


class CombinedExtractionResult(BaseModel):
    """Complete extraction result from batch combined prompt."""

    core_identity: list[BatchIdentityItem] = Field(default_factory=list)
    opinions_views: list[BatchOpinionItem] = Field(default_factory=list)
    preferences_patterns: list[BatchPreferenceItem] = Field(default_factory=list)
    desires_needs: list[BatchDesireItem] = Field(default_factory=list)
    life_narrative: list[BatchNarrativeItem] = Field(default_factory=list)
    events: list[BatchEventItem] = Field(default_factory=list)
    entities_relationships: list[BatchEntityItem] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if no extractions were made."""
        return all(
            len(getattr(self, dim)) == 0
            for dim in [
                "core_identity", "opinions_views", "preferences_patterns",
                "desires_needs", "life_narrative", "events", "entities_relationships"
            ]
        )

    def total_items(self) -> int:
        """Count total extracted items across all dimensions."""
        return sum(
            len(getattr(self, dim))
            for dim in [
                "core_identity", "opinions_views", "preferences_patterns",
                "desires_needs", "life_narrative", "events", "entities_relationships"
            ]
        )
```

#### CPDE7LLMService Implementation

```python
class CPDE7LLMService:

    def extract_combined(
        self,
        messages: list[MessageRecord],
        model: str = None,
    ) -> CombinedExtractionResult:
        """
        Extract all 7 dimensions from messages in a single LLM call.

        Most cost-efficient approach. Use for bulk processing.

        Args:
            messages: Messages to extract from
            model: Optional model override

        Returns:
            CombinedExtractionResult with all dimensions
        """
        # Format messages with IDs
        numbered_messages, id_map = format_messages_for_batch(messages)

        # Build prompt
        prompt = BATCH_COMBINED_PROMPT.format(
            numbered_messages=numbered_messages
        )

        # Get structured LLM
        structured_llm = self._get_llm(model).with_structured_output(
            CombinedExtractionResult
        )

        # Single call extracts everything
        result = structured_llm.invoke([HumanMessage(content=prompt)])

        # Map MSG-XXX back to actual message IDs
        self._remap_message_ids(result, id_map)

        return result

    def _remap_message_ids(
        self,
        result: CombinedExtractionResult,
        id_map: dict[str, int]
    ) -> None:
        """Replace MSG-XXX with actual database message IDs."""
        for dim in ["core_identity", "opinions_views", "preferences_patterns",
                    "desires_needs", "life_narrative", "events", "entities_relationships"]:
            for item in getattr(result, dim):
                if item.source_message_id in id_map:
                    item.source_message_id = str(id_map[item.source_message_id])
```

#### When to Use Option B

| Scenario | Use Option B? |
|----------|---------------|
| Bulk historical processing | ✅ Yes - cost matters |
| Real-time per-message | ❌ No - use per-message |
| Budget-constrained | ✅ Yes - 140x cheaper |
| Maximum precision needed | ⚠️ Maybe - test first |
| Debugging extraction issues | ❌ No - use per-dimension |
| Production at scale | ✅ Yes - default choice |

#### Potential Concerns & Mitigations

| Concern | Mitigation |
|---------|------------|
| Complex prompt | Modern LLMs (GPT-4, Claude) handle well |
| Missing extractions | Add verification pass for important data |
| Debugging difficulty | Log raw LLM responses, add per-dimension fallback |
| Token limits | Adjust batch size; 15-20 messages usually safe |
| Output parsing | Pydantic structured output handles this |

**Pros:**
- Single LLM call per batch (7x more efficient than Option A)
- LLM sees full context once - no redundant re-reading
- Natural fit - messages often contain multiple dimensions
- Simpler orchestration - one call, one result

**Cons:**
- Larger prompt (more tokens per call, but fewer calls)
- All-or-nothing - if call fails, lose all dimensions
- Slightly harder to debug specific dimension issues

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

### Primary: Option B (Batch Combined) for Production

For most use cases, **Option B is the recommended approach**:

1. **140x cheaper** than per-message extraction
2. **7x cheaper** than per-dimension batch (Option A)
3. **Natural fit** - messages contain multiple dimensions
4. **Simpler code** - one call, one result object

### Fallback: Per-Message for Precision

Keep per-message prompts (`prompts.py`) for:
- Debugging extraction issues
- High-value single messages
- Real-time extraction needs
- Verification of batch results

### Implementation Order

1. Add `Batch*` models to `models.py` (with `SourcedExtraction` base)
2. Create `batch_prompts.py` with `BATCH_COMBINED_PROMPT`
3. Add `extract_combined()` method to `CPDE7LLMService`
4. Add config options: `batch_mode`, `batch_size`
5. Update `ProfilingDataExtractionService` to use combined extraction
6. Keep per-message as fallback option

---

## Summary

| Decision | Choice |
|----------|--------|
| **Primary approach** | **Option B: Batch Combined** (single prompt, all dimensions) |
| Fallback | Per-message for precision/debugging |
| Attribution | Explicit `source_message_id` + `source_quote` in output |
| Message format | Numbered with `[MSG-XXX]` prefix |
| Batch size | Configurable, default 15-20 |
| Models | `SourcedExtraction` base → `Batch*Item` → `CombinedExtractionResult` |
| Mode selection | Config: `batch_mode: bool`, `batch_size: int` |
| Cost savings | 140x vs per-message, 7x vs per-dimension batch |
