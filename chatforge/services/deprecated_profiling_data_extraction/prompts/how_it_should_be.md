# CPDE-7 Configurable Extraction System

## Overview

The profile data extraction system should be **configurable** with two extraction strategies:

1. **Per-Dimension Calls** - Separate LLM call for each dimension (parallel or sequential)
2. **Combined Single Call** - One LLM call for all selected dimensions (uses Proteas)

Both strategies allow users to select which dimensions to extract.
Both strategies return the **same type**: `BatchProfilingDataExtractionResult`.

---

## Return Type: BatchProfilingDataExtractionResult

Both strategies return `BatchProfilingDataExtractionResult` - a static Pydantic model with all 7 dimension fields as optional:

```python
class BatchProfilingDataExtractionResult(BaseModel):
    core_identity: BatchCoreIdentityResult | None = None
    opinions_views: BatchOpinionsResult | None = None
    preferences_patterns: BatchPreferencesResult | None = None
    desires_needs: BatchDesiresResult | None = None
    life_narrative: BatchNarrativeResult | None = None
    events: BatchEventsResult | None = None
    entities_relationships: BatchEntitiesResult | None = None
```

### Why This Approach?

| Benefit | Explanation |
|---------|-------------|
| **Full type safety** | IDE autocompletion, mypy/pyright work perfectly |
| **Predictable schema** | API consumers always know the structure |
| **No magic** | No dynamic model creation, no runtime surprises |
| **Easy consumer code** | `if pde_result.core_identity is not None:` |
| **Consistent interface** | Same return type regardless of strategy |
| **Serialization** | JSON schema is always consistent |
| **Future proof** | Adding dimension #8 = add one field |

### Result Semantics

| Scenario | Value |
|----------|-------|
| Not requested | `None` |
| Requested, nothing found | `has_content=False, items=[]` |
| Requested, data found | `has_content=True, items=[...]` |

```python
pde_result = await service.extract_dimensions(messages, ["core_identity", "events"])

pde_result.core_identity           # BatchCoreIdentityResult (requested)
pde_result.core_identity.has_content  # True or False
pde_result.core_identity.items     # [...] or []

pde_result.events                  # BatchEventsResult (requested)

pde_result.opinions_views          # None (not requested)
```

---

## Configuration Options

```python
# User configures:
dimensions = ["core_identity", "events", "entities_relationships"]
strategy = "combined"  # or "per_dimension"
parallel = True        # only applies to "per_dimension" strategy
```

---

## Strategy 1: Per-Dimension Calls

### How It Works
- Each dimension has its own static prompt (already exists in `batch_prompts.py`)
- Makes N LLM calls (one per selected dimension)
- Can run parallel or sequential
- **No Proteas needed**

### Interface

```python
# Sequential
pde_result = await service.extract_dimensions(
    messages=messages,
    dimensions=["core_identity", "events"],
    strategy="per_dimension",
    parallel=False
)

# Parallel
pde_result = await service.extract_dimensions(
    messages=messages,
    dimensions=["core_identity", "events"],
    strategy="per_dimension",
    parallel=True
)
```

### Implementation

```python
async def _extract_per_dimension(
    self,
    messages: str,
    dimensions: list[str],
    parallel: bool = False
) -> BatchProfilingDataExtractionResult:
    """Make separate LLM call per dimension."""
    pde_result = BatchProfilingDataExtractionResult()

    if parallel:
        tasks = [self.extract_dimension(messages, dim) for dim in dimensions]
        outputs = await asyncio.gather(*tasks)
        for dim, output in zip(dimensions, outputs):
            # Extract inner result from wrapper (e.g., output.core_identity)
            inner = getattr(output, dim)
            setattr(pde_result, dim, inner)
    else:
        for dim in dimensions:
            output = await self.extract_dimension(messages, dim)
            inner = getattr(output, dim)
            setattr(pde_result, dim, inner)

    # Non-requested dimensions stay None
    return pde_result
```

---

## Strategy 2: Combined Single Call

### How It Works
- **Proteas** combines selected dimension prompts into one
- Makes **1 LLM call**
- Response mapped back to `BatchProfilingDataExtractionResult`

### Note: All 7 Dimensions
A static prompt for all 7 dimensions already exists (`CPDE_ALL_7_BATCH` / `extract_all_7()`).
When user selects all 7 dimensions, use the existing static prompt instead of building with Proteas.

```python
if set(dimensions) == set(ALL_DIMENSIONS):
    # Use existing static prompt and BatchAll7Output
    return await self.extract_all_7(messages)
else:
    # Use Proteas to build combined prompt
    ...
```

### Interface

```python
pde_result = await service.extract_dimensions(
    messages=messages,
    dimensions=["core_identity", "events"],
    strategy="combined"
)
```

### Implementation

```python
from chatforge.services.profiling_data_extraction.prompts import build_prompt

async def _extract_combined(
    self,
    messages: str,
    dimensions: list[str]
) -> BatchProfilingDataExtractionResult:
    """Single LLM call with combined prompt."""

    # Proteas builds prompt with only requested dimensions
    prompt = build_prompt(dimensions=dimensions, messages=messages)

    # Dynamic model for LLM response (only requested fields)
    output_model = build_output_model(dimensions)

    # Single LLM call
    structured_llm = self._get_llm().with_structured_output(output_model)
    llm_response = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Map to BatchProfilingDataExtractionResult
    pde_result = BatchProfilingDataExtractionResult()
    for dim in dimensions:
        setattr(pde_result, dim, getattr(llm_response, dim))

    return pde_result
```

### Dynamic Model for LLM Call

The LLM needs a schema with only the requested dimensions. We create this dynamically:

```python
from pydantic import create_model

BATCH_RESULT_TYPES = {
    "core_identity": BatchCoreIdentityResult,
    "opinions_views": BatchOpinionsResult,
    "preferences_patterns": BatchPreferencesResult,
    "desires_needs": BatchDesiresResult,
    "life_narrative": BatchNarrativeResult,
    "events": BatchEventsResult,
    "entities_relationships": BatchEntitiesResult,
}

def build_output_model(dimensions: list[str]) -> type[BaseModel]:
    """Create Pydantic model with exactly the requested dimensions."""
    fields = {
        dim: (BATCH_RESULT_TYPES[dim], ...)
        for dim in dimensions
    }
    return create_model("DynamicExtractionOutput", **fields)
```

This dynamic model is **only used internally** for the LLM call. The user always receives `BatchProfilingDataExtractionResult`.

---

## Unified Interface

```python
async def extract_dimensions(
    self,
    messages: str,
    dimensions: list[str],
    strategy: Literal["per_dimension", "combined"] = "combined",
    parallel: bool = False  # only for "per_dimension"
) -> BatchProfilingDataExtractionResult:
    """
    Extract selected dimensions using specified strategy.

    Args:
        messages: Formatted message text
        dimensions: List of dimensions to extract
        strategy:
            - "per_dimension": Separate LLM call per dimension
            - "combined": Single LLM call with combined prompt (uses Proteas)
        parallel: Run per-dimension calls in parallel (only for "per_dimension")

    Returns:
        BatchProfilingDataExtractionResult with requested dimensions populated,
        non-requested dimensions are None.
    """
    if strategy == "per_dimension":
        return await self._extract_per_dimension(messages, dimensions, parallel)
    else:
        return await self._extract_combined(messages, dimensions)
```

---

## Comparison

| Aspect | Per-Dimension | Combined |
|--------|---------------|----------|
| LLM Calls | N (one per dimension) | 1 |
| Prompt Source | Static (`batch_prompts.py`) | Dynamic (Proteas) |
| Parallel support | Yes | N/A (single call) |
| Use case | Need per-dimension control | Efficiency, cost savings |
| Return type | `BatchProfilingDataExtractionResult` | `BatchProfilingDataExtractionResult` |

---

## Proteas Role

Proteas is **only used for the "combined" strategy**:

1. **Dimension Units** (`dimension_units.py`) - Each dimension as a `PromptTemplateUnit`
2. **Prompt Builder** (`builder.py`) - `build_prompt(dimensions, messages)` combines units
3. **Placeholder Syntax** - Uses `$variable` to avoid JSON escaping issues

```python
# Proteas assembles:
# 1. Header unit (always)
# 2. Selected dimension units only
# 3. Messages unit (with $messages placeholder)
# 4. Instructions unit (always)

prompt = build_prompt(
    dimensions=["core_identity", "events"],
    messages=messages_text
)
```

---

## File Structure

```
chatforge/services/profiling_data_extraction/
├── prompts/                      # Proteas-based (for combined strategy)
│   ├── __init__.py
│   ├── dimension_units.py        # 7 PromptTemplateUnits
│   ├── builder.py                # build_prompt(), build_output_model()
│   └── how_it_should_be.md
├── batch_prompts.py              # Static prompts (for per-dimension strategy)
├── models.py                     # Pydantic models
└── cpde7llmservice.py            # Service with extract_dimensions()
```

---

## Usage Examples

### Per-Dimension (Parallel)
```python
service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")

pde_result = await service.extract_dimensions(
    messages=messages,
    dimensions=["core_identity", "events", "entities_relationships"],
    strategy="per_dimension",
    parallel=True
)

# 3 parallel LLM calls
# Returns BatchProfilingDataExtractionResult:
pde_result.core_identity        # BatchCoreIdentityResult
pde_result.events               # BatchEventsResult
pde_result.entities_relationships  # BatchEntitiesResult
pde_result.opinions_views       # None (not requested)
```

### Combined (Single Call)
```python
pde_result = await service.extract_dimensions(
    messages=messages,
    dimensions=["core_identity", "events", "entities_relationships"],
    strategy="combined"
)

# 1 LLM call (Proteas-built prompt)
# Returns BatchProfilingDataExtractionResult:
pde_result.core_identity        # BatchCoreIdentityResult
pde_result.events               # BatchEventsResult
pde_result.entities_relationships  # BatchEntitiesResult
pde_result.opinions_views       # None (not requested)
```

### Consumer Code Pattern
```python
pde_result = await service.extract_dimensions(messages, dimensions, strategy="combined")

# Check and process each dimension
if pde_result.core_identity is not None:
    if pde_result.core_identity.has_content:
        for item in pde_result.core_identity.items:
            print(f"Found: {item.aspect} = {item.state_value}")
    else:
        print("Core identity requested but nothing found")
else:
    print("Core identity was not requested")
```
