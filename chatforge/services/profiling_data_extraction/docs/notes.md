# Implementation Notes

## Prompts vs Pydantic Structured Output

### Current State

`prompts.py` currently includes JSON schema instructions in each prompt:

```python
CORE_IDENTITY_PROMPT = """
...
Return JSON:
{{
  "has_identity_content": true/false,
  "items": [
    {{
      "aspect": "string - category of identity marker",
      "state_value": "string - the value",
      "temporal": "string or null",
      "relational_dimension": "string or null"
    }}
  ]
}}
"""
```

### The Issue

This approach expects the LLM to generate **raw JSON text** which we then parse. Problems:
- LLM might wrap JSON in markdown (```json ... ```)
- LLM might add explanation text before/after
- LLM might generate invalid JSON
- We need parsing/validation code

### The Solution: Pydantic Structured Output

LangChain's `with_structured_output()` handles this:

```python
from pydantic import BaseModel, Field

class CoreIdentityItem(BaseModel):
    aspect: str = Field(description="Category of identity marker")
    state_value: str = Field(description="The value")
    temporal: str | None = Field(default=None, description="Time-bound info")
    relational_dimension: str | None = Field(default=None)

class CoreIdentityResult(BaseModel):
    has_identity_content: bool
    items: list[CoreIdentityItem] = Field(default_factory=list)

# LLM returns Pydantic object directly - no parsing needed
structured_llm = llm.with_structured_output(CoreIdentityResult)
result: CoreIdentityResult = structured_llm.invoke(messages)
```

### Where Pydantic Models Live

**Pydantic models are defined in `CPDE7LLMService`** (or a separate `models.py`):

```
prompts.py          → Extraction instructions (WHAT to extract)
models.py           → Pydantic schemas (output structure)
cpde7llmservice.py  → Connects prompts + models + LLM
```

### How Prompts Change

**Before (raw JSON):**
```python
CORE_IDENTITY_PROMPT = """
Extract identity facts...

Return JSON:
{{"has_identity_content": true/false, "items": [...]}}
"""
```

**After (Pydantic):**
```python
CORE_IDENTITY_PROMPT = """
Extract identity facts from the TARGET MESSAGE.

WHAT COUNTS AS CORE IDENTITY:
- What someone IS (roles, attributes, states)
- Stable characteristics that define them
...

=== CONTEXT MESSAGES ===
{context_messages}

=== TARGET MESSAGE ===
{target_message}
"""
# No JSON schema in prompt - Pydantic handles output structure
```

The prompt focuses on **extraction logic**, not output formatting.

### CPDE7LLMService Implementation

```python
class CPDE7LLMService:
    def extract_core_identity(
        self,
        target_message: str,
        context_messages: str = "",
    ) -> CoreIdentityResult:
        # Build prompt (no JSON schema needed)
        prompt = CORE_IDENTITY_PROMPT.format(
            target_message=target_message,
            context_messages=context_messages,
        )

        # Get structured LLM
        structured_llm = self._get_llm().with_structured_output(
            CoreIdentityResult
        )

        # Returns Pydantic object directly
        return structured_llm.invoke([HumanMessage(content=prompt)])
```

### Benefits

| Raw JSON Approach | Pydantic Structured Output |
|-------------------|---------------------------|
| LLM generates text | LLM generates structured object |
| Need JSON parsing | No parsing needed |
| Validation after parse | Validation built-in |
| Prompt includes schema | Prompt focuses on logic |
| Error-prone | Reliable |

### Migration Path

1. **Create `models.py`** with Pydantic models for each dimension
2. **Simplify `prompts.py`** - remove JSON schema instructions
3. **Implement `cpde7llmservice.py`** - use `with_structured_output()`
4. **Keep prompt logic** - the extraction rules, examples, what counts/doesn't count

### Example: Full Flow

```python
# models.py
class CoreIdentityItem(BaseModel):
    aspect: str
    state_value: str
    temporal: str | None = None
    relational_dimension: str | None = None

class CoreIdentityResult(BaseModel):
    has_identity_content: bool
    items: list[CoreIdentityItem] = Field(default_factory=list)

# prompts.py (simplified - no JSON schema)
CORE_IDENTITY_PROMPT = """
Extract facts about WHO THE PERSON IS from the TARGET MESSAGE.
...
=== TARGET MESSAGE ===
{target_message}
"""

# cpde7llmservice.py
class CPDE7LLMService:
    def extract_core_identity(self, target_message, context_messages=""):
        prompt = CORE_IDENTITY_PROMPT.format(...)
        structured_llm = self._get_llm().with_structured_output(CoreIdentityResult)
        return structured_llm.invoke([HumanMessage(content=prompt)])

# Usage
service = CPDE7LLMService()
result = service.extract_core_identity("I'm a 34-year-old engineer")
# result.has_identity_content = True
# result.items[0].aspect = "age"
# result.items[0].state_value = "34"
```

---

## Summary

| Component | Contains |
|-----------|----------|
| `prompts.py` | Extraction logic, examples, rules (no JSON schema) |
| `models.py` | Pydantic models defining output structure |
| `cpde7llmservice.py` | Connects prompts + models + LLM via `with_structured_output()` |

The JSON schema instructions in current `prompts.py` will be replaced by Pydantic models. The extraction logic (what counts, what doesn't, examples) stays in the prompts.

---

## Open Questions / Tensions to Resolve

### 1. Per-Message vs Batch Processing

| Source | Model |
|--------|-------|
| `prompts.py` | Per-message with context window (TARGET + CONTEXT pattern) |
| `elaboration.md` | Per-message with `context_window` config |
| `step_by_step_...md` | Batch processing (multiple messages per LLM call) |

**The prompts are designed for per-message extraction:**
```
=== CONTEXT MESSAGES (for reference only) ===
{context_messages}

=== TARGET MESSAGE (extract from this) ===
{target_message}
```

**Decision needed:** Which model do we implement?

| Per-Message + Context | Batch |
|-----------------------|-------|
| More LLM calls | Fewer LLM calls |
| Precise extraction per message | May miss message-level attribution |
| Matches current prompts | Requires prompt redesign |
| Better traceability | More efficient |

**Recommendation:** Per-message with context window matches the prompts. Use this model.

---

### 2. Config Complexity

| Source | Config Fields |
|--------|---------------|
| `config.py` (current) | `dimensions`, `batch_size`, `min_messages_for_extraction`, `confidence_threshold` |
| `elaboration.md` | Adds `context_window`, `deduplication`, `output_format` |

**Are these needed?**

| Field | Needed? | Reason |
|-------|---------|--------|
| `context_window` | YES | Per-message extraction needs context size |
| `deduplication` | MAYBE | Depends on data source quality |
| `output_format` | NO | Always return dataclasses/Pydantic |

**Recommendation:** Add `context_window: int = 5` to `ExtractionConfig`.

---

### 3. Aggregated Profile

| Source | Says |
|--------|------|
| `elaboration.md` | Shows `aggregated_profile` in output |
| `details.md` | "Profiling (aggregation) is a separate future step" |

**Clarification:**

```
ProfilingDataExtractionService    →    Future: ProfileAggregationService
(extracts raw data)                    (combines into unified profile)
         ↓                                         ↓
ExtractedProfilingData              →         UserProfile
(per-message facts)                    (aggregated, deduplicated)
```

**Current scope:** Extraction only. No aggregation.

**What we return:**
- `list[ExtractedProfilingData]` - raw extracted facts
- `ProfilingDataExtractionRun` - metadata about the extraction

**What we DON'T return (yet):**
- `AggregatedProfile` - future enhancement

**Recommendation:** Confirm aggregation is out of scope. Update `elaboration.md` to reflect this or mark it as future.

---

## Summary of Decisions Needed

| Question | Current State | Recommendation |
|----------|---------------|----------------|
| Per-message vs Batch? | Prompts expect per-message | **Per-message with context window** |
| Add `context_window` to config? | Not in config.py | **Yes, add it** |
| Add `deduplication` to config? | Not in config.py | Optional, can add later |
| Include aggregation? | Out of scope per details.md | **Confirm out of scope** |
